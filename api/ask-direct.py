# /api/ask-direct.py (TAM DÜZELTİLMİŞ - 3 SAYFA TAM OKUMA)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import tempfile
import re
from io import BytesIO
import ssl

# SSL doğrulamasını devre dışı bırak (Vercel için)
ssl._create_default_https_context = ssl._create_unverified_context

def find_latest_excel():
    """Sitedeki EN GÜNCEL Excel dosyasını AKILLICA bul"""
    try:
        base_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/"
        
        # ÖNCE: Bilinen dosya isimlerini kontrol et
        today = datetime.now()
        excel_files_to_try = []
        
        # Son 7 günü kontrol et
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%d%m%Y")
            filename = f"BORSAANALIZ_V11_TAM_{date_str}.xlsm"
            excel_files_to_try.append(filename)
        
        # 630+ hisse olduğu için dosya büyük, en günceli bul
        print(f"🔍 En güncel Excel aranıyor ({len(excel_files_to_try)} dosya kontrol edilecek)...")
        
        for filename in excel_files_to_try:
            file_url = f"{base_url}{filename}"
            try:
                # HEAD isteği ile dosya var mı kontrol et
                req = urllib.request.Request(file_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ EN GÜNCEL EXCEL BULUNDU: {filename}")
                        
                        # Dosyadan tarihi çıkar
                        date_match = re.search(r'(\d{2})(\d{2})(\d{4})\.xlsm$', filename)
                        if date_match:
                            day, month, year = date_match.groups()
                            file_date = datetime(int(year), int(month), int(day))
                            return file_url, file_date.strftime("%d.%m.%Y")
                        else:
                            return file_url, "güncel"
            except:
                continue  # Bu dosya yok, diğerini dene
        
        # Hiçbiri yoksa, fallback olarak bilinen son dosya
        print("⚠️ Güncel dosya bulunamadı, fallback kullanılıyor...")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"
        
    except Exception as e:
        print(f"❌ Excel bulma hatası: {e}")
        # Son çare
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"

def clean_header(header):
    """Başlığı temizle: 'Hisse (06-02-2026)' -> 'Hisse'"""
    if not header:
        return ""
    # Tarih parantezlerini kaldır
    header = str(header).split('(')[0].strip()
    # Fazla boşlukları temizle
    header = re.sub(r'\s+', ' ', header)
    return header

def read_all_excel_data(excel_path):
    """Excel'den TÜM verileri oku (3 sayfa TAM)"""
    try:
        from openpyxl import load_workbook
        
        print(f"📖 Excel açılıyor: {excel_path}")
        
        # URL'den indir
        req = urllib.request.Request(excel_path, 
                                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        with urllib.request.urlopen(req, timeout=60) as response:
            excel_content = response.read()
        
        print(f"✅ Excel indirildi ({len(excel_content):,} bytes)")
        
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
            tmp.write(excel_content)
            tmp_path = tmp.name
        
        # Excel'i aç - SADECE OKUMA MODUNDA
        wb = load_workbook(tmp_path, data_only=True, read_only=True)
        
        # Geçici dosyayı temizle
        os.unlink(tmp_path)
        
        print(f"✅ Excel açıldı. Sayfalar: {wb.sheetnames}")
        
        data = {
            "excel_file": os.path.basename(excel_path),
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "sheets": {}
        }
        
        # 1. SİNYALLER SAYFASI (TÜM HİSSELER - 630+)
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            print(f"📊 Sinyaller sayfası TAMAMEN okunuyor: ~{ws.max_row} satır...")
            
            # BAŞLIKLARI TEMİZLE
            headers_clean = []
            headers_raw = []
            
            for col in range(1, 150):  # 150 sütuna kadar kontrol
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    raw_header = str(cell_val)
                    headers_raw.append(raw_header)
                    clean_header_text = clean_header(raw_header)
                    headers_clean.append(clean_header_text)
                else:
                    break
            
            print(f"📋 Sinyaller başlıklar ({len(headers_clean)}): {headers_clean[:8]}...")
            
            # TÜM hisseleri oku
            sinyaller_data = {}
            total_hisseler = 0
            
            # Performans için: İlk 1000 satır oku (630+ hisse)
            max_rows = min(1001, ws.max_row)
            
            for row_num, row in enumerate(ws.iter_rows(min_row=2, max_row=max_rows, values_only=True), start=2):
                if row and row[0]:
                    hisse_adi = str(row[0]).strip()
                    if hisse_adi:
                        hisse_dict = {}
                        
                        # Tüm sütunları işle
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                
                                # Format dönüşümü
                                if isinstance(cell_val, datetime):
                                    hisse_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, (int, float)):
                                    hisse_dict[header_name] = cell_val
                                else:
                                    hisse_dict[header_name] = str(cell_val).strip()
                        
                        sinyaller_data[hisse_adi] = hisse_dict
                        total_hisseler += 1
            
            data["sheets"]["Sinyaller"] = {
                "headers": headers_clean,
                "hisseler": sinyaller_data,
                "toplam_hisse": total_hisseler,
                "ornek_hisseler": list(sinyaller_data.keys())[:5]
            }
            
            print(f"✅ Sinyaller okundu: {total_hisseler} hisse")
        
        # 2. ENDEKSLER SAYFASI (TÜM SATIRLAR)
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            print(f"📈 ENDEKSLER sayfası TAMAMEN okunuyor: ~{ws.max_row} satır...")
            
            # BAŞLIKLARI TEMİZLE
            headers_clean = []
            
            for col in range(1, 150):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    clean_header_text = clean_header(str(cell_val))
                    headers_clean.append(clean_header_text)
                else:
                    break
            
            print(f"📋 ENDEKSLER başlıklar ({len(headers_clean)}): {headers_clean[:8]}...")
            
            # TÜM SATIRLARI OKU (200 satır)
            endeks_data = []
            endeks_dict = {}
            max_rows = min(201, ws.max_row)
            
            for row_num, row in enumerate(ws.iter_rows(min_row=2, max_row=max_rows, values_only=True), start=2):
                if row and row[0]:
                    sembol_adi = str(row[0]).strip()
                    if sembol_adi:
                        sembol_dict = {}
                        
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                
                                if isinstance(cell_val, datetime):
                                    sembol_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, (int, float)):
                                    sembol_dict[header_name] = cell_val
                                else:
                                    sembol_dict[header_name] = str(cell_val).strip()
                        
                        endeks_dict[sembol_adi] = sembol_dict
                        endeks_data.append(row)
            
            data["sheets"]["ENDEKSLER"] = {
                "headers": headers_clean,
                "semboller": endeks_dict,
                "data": endeks_data,
                "toplam_sembol": len(endeks_dict),
                "okunan_satir": max_rows - 1
            }
            
            print(f"✅ ENDEKSLER okundu: {len(endeks_dict)} sembol")
        
        # 3. FON_EMTIA_COIN_DOVIZ SAYFASI (TÜM SATIRLAR)
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            print(f"💰 FON_EMTIA_COIN_DOVIZ sayfası TAMAMEN okunuyor: ~{ws.max_row} satır...")
            
            # BAŞLIKLARI TEMİZLE
            headers_clean = []
            
            for col in range(1, 150):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    clean_header_text = clean_header(str(cell_val))
                    headers_clean.append(clean_header_text)
                else:
                    break
            
            print(f"📋 FON_EMTIA başlıklar ({len(headers_clean)}): {headers_clean[:8]}...")
            
            # TÜM SATIRLARI OKU (150 satır)
            fon_data = []
            fon_dict = {}
            max_rows = min(151, ws.max_row)
            
            for row_num, row in enumerate(ws.iter_rows(min_row=2, max_row=max_rows, values_only=True), start=2):
                if row and row[0]:
                    sembol_adi = str(row[0]).strip()
                    if sembol_adi:
                        sembol_dict = {}
                        
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                
                                if isinstance(cell_val, datetime):
                                    sembol_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, float):
                                    sembol_dict[header_name] = round(cell_val, 4)
                                elif isinstance(cell_val, (int, float)):
                                    sembol_dict[header_name] = cell_val
                                else:
                                    sembol_dict[header_name] = str(cell_val).strip()
                        
                        fon_dict[sembol_adi] = sembol_dict
                        fon_data.append(row)
            
            data["sheets"]["FON_EMTIA_COIN_DOVIZ"] = {
                "headers": headers_clean,
                "semboller": fon_dict,
                "data": fon_data,
                "toplam_sembol": len(fon_dict)
            }
            
            print(f"✅ FON_EMTIA_COIN_DOVIZ okundu: {len(fon_dict)} sembol")
        
        wb.close()
        
        # TOPLAM İSTATİSTİKLER
        toplam_sembol = 0
        for sheet_name, sheet_data in data["sheets"].items():
            if "hisseler" in sheet_data:
                toplam_sembol += sheet_data.get("toplam_hisse", 0)
            elif "semboller" in sheet_data:
                toplam_sembol += sheet_data.get("toplam_sembol", 0)
        
        print(f"🎉 TÜM EXCEL OKUNDU! Toplam: {toplam_sembol} sembol")
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Excel okuma hatası: {str(e)}"}

def find_in_excel_data(question, excel_data):
    """Excel verilerinde soruya göre arama yap - 3 SAYFADA TAM ARA"""
    try:
        question_upper = question.upper()
        
        # Arama terimlerini al
        search_terms = []
        for word in re.findall(r'[A-Z0-9]+', question_upper):
            if len(word) >= 2:  # En az 2 karakter
                search_terms.append(word)
        
        print(f"🔍 Aranan terimler: {search_terms}")
        
        # 1. ÖNCE: HİSSE ARA (Sinyaller sayfasında)
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            for term in search_terms:
                for hisse_adi, hisse_veriler in hisseler.items():
                    hisse_clean = re.sub(r'[^A-Z0-9]', '', hisse_adi.upper())
                    if term in hisse_clean or hisse_clean in term:
                        print(f"✅ {hisse_adi} Sinyaller sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "hisse",
                            "data": hisse_veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        # 2. SONRA: ENDEKS ARA (ENDEKSLER sayfasında - XU100, XTEKS, XULAS vb.)
        if "ENDEKSLER" in excel_data["sheets"]:
            endeksler = excel_data["sheets"]["ENDEKSLER"]["semboller"]
            
            for term in search_terms:
                for sembol_adi, sembol_veriler in endeksler.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} ENDEKSLER sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "endeks",
                            "data": sembol_veriler,
                            "sayfa": "ENDEKSLER",
                            "name": sembol_adi
                        }
            
            # ÖZEL: XU100 araması
            if "XU100" in question_upper:
                # Benzer endeksleri bul
                benzer_endeksler = []
                for sembol in endeksler.keys():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol.upper())
                    if "XU" in sembol_clean or "BIST" in sembol_clean:
                        benzer_endeksler.append(sembol)
                
                if benzer_endeksler:
                    ilk_endeks = benzer_endeksler[0]
                    print(f"⚠️ XU100 bulunamadı, en yakın endeks: {ilk_endeks}")
                    return {
                        "found": True,
                        "type": "endeks",
                        "data": endeksler[ilk_endeks],
                        "sayfa": "ENDEKSLER",
                        "name": ilk_endeks,
                        "not": f"XU100 bulunamadı, en yakın endeks: {ilk_endeks}"
                    }
        
        # 3. SON OLARAK: FON/EMTİA/DÖVİZ ARA (GMSTR BURADA!)
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            fonlar = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
            
            for term in search_terms:
                for sembol_adi, sembol_veriler in fonlar.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} FON_EMTIA_COIN_DOVIZ sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "fon_emtia",
                            "data": sembol_veriler,
                            "sayfa": "FON_EMTIA_COIN_DOVIZ",
                            "name": sembol_adi
                        }
        
        # Hiçbir şey bulunamadı
        print(f"⚠️ Hiçbir sayfada bulunamadı: {search_terms}")
        
        # Hangi semboller mevcut? (debug için)
        available_symbols = []
        if "Sinyaller" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["Sinyaller"]["hisseler"].keys())[:5])
        if "ENDEKSLER" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["ENDEKSLER"]["semboller"].keys())[:5])
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"].keys())[:5])
        
        print(f"📋 Mevcut semboller (örnek): {available_symbols}")
        
        return {
            "found": False,
            "type": None,
            "data": None,
            "sayfa": None,
            "name": None,
            "available_symbols": available_symbols[:10]
        }
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {
            "found": False,
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # En güncel Excel'i bul
        excel_url, excel_date = find_latest_excel()
        
        response = json.dumps({
            "status": "online",
            "ai": "BORSAANALIZ AI - TAM EXCEL ANALİZ",
            "excel": {
                "guncel_dosya": os.path.basename(excel_url),
                "tarih": excel_date,
                "sayfalar": ["Sinyaller (630+ hisse)", "ENDEKSLER (200 satır)", "FON_EMTIA_COIN_DOVIZ (150 satır)"],
                "not": "3 sayfa TAMAMEN okunur, başlıklar temizlenir"
            }
        }, ensure_ascii=False)
        
        self.wfile.write(response.encode('utf-8'))
    
    def do_POST(self):
        try:
            # 1. Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"\n" + "="*70)
            print(f"🤖 TAM EXCEL ANALİZ BAŞLIYOR: {question}")
            print("="*70)
            
            # 2. EN GÜNCEL EXCEL'İ BUL
            print("🔍 EN GÜNCEL EXCEL DOSYASI ARANIYOR...")
            excel_start = datetime.now()
            excel_url, excel_date = find_latest_excel()
            print(f"✅ BULUNDU: {os.path.basename(excel_url)} ({excel_date})")
            
            # 3. EXCEL'İ İNDİR VE TÜM VERİLERİ OKU
            print("📥 Excel indiriliyor ve 3 sayfa TAMAMEN okunuyor...")
            excel_result = read_all_excel_data(excel_url)
            
            # EXCEL OKUNAMADIYSA HATA DÖN
            if not excel_result.get("success"):
                print("❌ Excel okunamadı, hata mesajı dönülüyor...")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
            
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Excel dosyası okunamadı. Lütfen:\n1. Excel'in sitede olduğundan emin olun\n2. Hisse adını doğru yazın\n3. Daha sonra tekrar deneyin",
                    "excel_data_used": False,
                    "help": "Excel: /raporlar/BORSAANALIZ_V11_TAM_*.xlsm"
                }, ensure_ascii=False)
            
                self.wfile.write(result.encode('utf-8'))
                return
            
            excel_time = (datetime.now() - excel_start).total_seconds()
            print(f"⏱️ Excel işlem süresi: {excel_time:.2f} sn")
            
            # 4. SORUYU EXCEL VERİLERİNDE ARA (3 SAYFADA TAM ARA)
            print("🔍 Soru Excel verilerinde analiz ediliyor (3 sayfada TAM arama)...")
            analysis = find_in_excel_data(question, excel_result["data"])
            
            # 5. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 6. PROMPT HAZIRLA
            prompt = f"""🎯 **BORSAANALIZ AI - GERÇEK EXCEL VERİ ANALİZİ**

**📊 GÜNCEL EXCEL RAPORU:** {excel_result['data']['excel_file']} ({excel_date})
**⏰ ANALİZ ZAMANI:** {excel_result['data']['timestamp']}

**❓ KULLANICI SORUSU:** {question}

"""
            
            # BULUNAN VERİLERİ EKLE
            if analysis.get("found"):
                sembol_data = analysis["data"]
                sembol_name = analysis["name"]
                sayfa_name = analysis["sayfa"]
                
                prompt += f"""📊 **{sembol_name.upper()} ANALİZİ**

**KAYNAK:** {sayfa_name} sayfası (Excel'de bulundu)
**VERİLER (Excel'den alındı):**

"""
                
                # ÖNEMLİ ALANLARI GÖSTER
                important_fields = [
                    'Close', 'Open', 'High', 'Low', 'Hacim',
                    'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55',
                    'Pivot', 'S1', 'R1', 'BB_UPPER', 'BB_LOWER',
                    'Pearson55', 'DURUM', 'AI_YORUM'
                ]
                
                fields_found = 0
                for field in important_fields:
                    if field in sembol_data:
                        value = sembol_data[field]
                        prompt += f"• **{field}:** {value}\n"
                        fields_found += 1
                
                if fields_found > 0:
                    prompt += f"\n✅ **{sembol_name}** Excel'de bulundu. Yukarıdaki değerler GERÇEKTİR.\n\n"
                else:
                    prompt += f"\n⚠️ **{sembol_name}** Excel'de bulundu ama teknik veriler eksik.\n\n"
                
                # Özel not
                if analysis.get("not"):
                    prompt += f"**Not:** {analysis['not']}\n\n"
            
            else:
                prompt += """⚠️ **UYARI:** Sorunuzdaki sembol Excel'de bulunamadı.

**EXCEL'DE MEVCUT OLANLAR:**
• **Sinyaller:** 630+ hisse senedi (A1CAP, FROTO, THYAO, TUPRS vb.)
• **ENDEKSLER:** BIST endeksleri (XTEKS, XULAS, XU serisi vb.)
• **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto para (GMSTR, ALTIN, USD, EUR vb.)

**Lütfen:**
1. Sembol adını doğru yazın
2. Büyük/küçük harf fark etmez
3. Örnek: "FROTO analiz et", "GMSTR teknik durumu", "XU100 endeksi"

"""
                if analysis.get("available_symbols"):
                    prompt += f"**Örnek semboller:** {', '.join(analysis['available_symbols'][:8])}\n\n"
            
            # ANALİZ TALİMATLARI
            prompt += """🎯 **ANALİZ TALİMATLARI:**

1. **SADECE** yukarıdaki Excel verilerini kullan
2. **VMA trend algo** değerini MUTLAKA analiz et (Örnek: "POZİTİF (50)")
3. Close, EMA_8, EMA_21, EMA_55 değerlerini karşılaştır
4. Pivot, S1, R1 seviyelerini belirt
5. **DURUM** alanını yorumla (GÜÇLÜ POZİTİF/ZAYIF vb.)
6. **AI_YORUM** alanındaki özeti dikkate al
7. **RSI/MACD YOK** - onlardan bahsetme
8. Sayısal değerleri net belirt (Örnek: "Close: 712,5 TL")
9. **YATIRIM TAVSİYESİ VERME** - sadece teknik analiz
10. Kapsamlı ama öz olsun (400-500 kelime ideal)

📊 **TAM ANALİZ FORMATI:**

**1. VERİ ÖZETİ**
• Mevcut fiyat ve temel göstergeler
• VMA trend algo analizi
• EMA'lar ve trend yapısı

**2. TEKNİK YORUM**
• VMA değerinin anlamı ve yorumu
• Fiyat-VMA ilişkisi
• Trendin gücü ve sürdürülebilirliği

**3. KRİTİK SEVİYELER**
• Ana destek (S1) ve direnç (R1) noktaları
• Pivot seviyesi ve Bollinger Bantları
• Riskli ve fırsat alanları

**4. TREND ANALİZİ**
• Kısa, orta, uzun vade trendleri
• EMA'ların sıralaması ve anlamı
• Pearson korelasyon değeri

**5. SONUÇ VE ÖNERİLER (BİLGİ AMAÇLI)**
• Genel teknik görünüm
• İzlenmesi gereken seviyeler
• Dikkat edilmesi gereken riskler

**ÖNEMLİ:** TÜM bölümleri tamamla. Analiz yarım kalmasın.

**CEVAP:**
"""
            
            print(f"📝 Prompt hazır ({len(prompt):,} karakter)")
            
            # 7. DEEPSEEK API'Yİ ÇAĞIR
            ai_start = datetime.now()
            url = "https://api.deepseek.com/chat/completions"
            
            # MAX TOKEN: 800 (daha uzun yanıtlar için)
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 800,  # Uzun analizler için
                "temperature": 0.1
            }
            
            json_data = json.dumps(request_data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz-AI/4.0'
                }
            )
            
            print("🔄 DeepSeek API çağrılıyor (800 token)...")
            response = urllib.request.urlopen(req, timeout=50)
            response_data = json.loads(response.read().decode('utf-8'))
            ai_time = (datetime.now() - ai_start).total_seconds()
            
            print(f"✅ DeepSeek yanıt aldı ({ai_time:.2f} sn)")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # 8. YANIT VER
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                total_time = excel_time + ai_time
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "excel_data_used": analysis.get("found", False),
                    "symbol": analysis.get("name"),
                    "sheet": analysis.get("sayfa"),
                    "performance": {
                        "excel_okuma_sn": round(excel_time, 2),
                        "ai_analiz_sn": round(ai_time, 2),
                        "toplam_sn": round(total_time, 2)
                    },
                    "excel_info": {
                        "dosya": excel_result["data"]["excel_file"],
                        "tarih": excel_date,
                        "sayfalar": list(excel_result["data"]["sheets"].keys())
                    }
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 YANIT GÖNDERİLDİ! Toplam süre: {total_time:.2f} sn")
                print("="*70 + "\n")
                
            else:
                raise Exception("API geçersiz yanıt")
                
        except Exception as e:
            print(f"❌ HATA: {str(e)}")
            print("="*70 + "\n")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası: {str(e)}\nLütfen daha sonra tekrar deneyin.",
                "excel_data_used": False
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
