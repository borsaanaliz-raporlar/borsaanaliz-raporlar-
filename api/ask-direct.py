# /api/ask-direct.py (DÜZELTİLMİŞ - 3 SAYFADA ARA)
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

def read_all_excel_data(excel_path):
    """Excel'den TÜM verileri oku (3 sayfa + TÜM hisseler)"""
    try:
        from openpyxl import load_workbook
        
        print(f"📖 Excel açılıyor: {excel_path}")
        
        # URL'den indir
        req = urllib.request.Request(excel_path, 
                                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        with urllib.request.urlopen(req, timeout=60) as response:  # 60 saniye timeout
            excel_content = response.read()
        
        print(f"✅ Excel indirildi ({len(excel_content):,} bytes)")
        
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
            tmp.write(excel_content)
            tmp_path = tmp.name
        
        # Excel'i aç - SADECE OKUMA MODUNDA (hızlı)
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
            print(f"📊 Sinyaller sayfası okunuyor: ~{ws.max_row} satır...")
            
            # Başlıkları al (ilk satır)
            headers = []
            max_columns = 0
            
            # Kaç sütun olduğunu bul
            for col in range(1, 100):  # Maksimum 100 sütun kontrol et
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers.append(str(cell_val).strip())
                    max_columns = col
                else:
                    break
            
            print(f"📋 {len(headers)} sütun başlığı bulundu: {headers[:5]}...")
            
            # TÜM hisseleri oku (tüm satırlar)
            sinyaller_data = {}
            total_hisseler = 0
            
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
                if row and row[0]:  # İlk sütunda hisse adı varsa
                    hisse_adi = str(row[0]).strip()
                    if hisse_adi:  # Boş değilse
                        hisse_dict = {}
                        
                        # Tüm sütunları işle
                        for col_idx in range(min(len(headers), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers[col_idx] if col_idx < len(headers) else f"Col{col_idx+1}"
                                
                                # Format dönüşümü
                                if isinstance(cell_val, datetime):
                                    hisse_dict[header_name] = cell_val.strftime("%d.%m.%Y %H:%M")
                                elif isinstance(cell_val, (int, float)):
                                    # Sayısal değerleri olduğu gibi sakla
                                    hisse_dict[header_name] = cell_val
                                else:
                                    hisse_dict[header_name] = str(cell_val).strip()
                        
                        sinyaller_data[hisse_adi] = hisse_dict
                        total_hisseler += 1
            
            data["sheets"]["Sinyaller"] = {
                "headers": headers,
                "hisseler": sinyaller_data,
                "toplam_hisse": total_hisseler,
                "ornek_hisseler": list(sinyaller_data.keys())[:5]  # İlk 5 hisseyi göster
            }
            
            print(f"✅ Sinyaller okundu: {total_hisseler} hisse")
        
        # 2. ENDEKSLER SAYFASI
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            print(f"📈 ENDEKSLER sayfası okunuyor...")
            
            endeks_data = []
            # İlk 50 satırı oku (performans için)
            for row in ws.iter_rows(min_row=1, max_row=min(51, ws.max_row), values_only=True):
                row_data = []
                for cell_val in row:
                    if cell_val is not None:
                        if isinstance(cell_val, datetime):
                            row_data.append(cell_val.strftime("%d.%m.%Y"))
                        elif isinstance(cell_val, (int, float)):
                            row_data.append(cell_val)
                        else:
                            row_data.append(str(cell_val))
                    else:
                        row_data.append("")
                endeks_data.append(row_data)
            
            data["sheets"]["ENDEKSLER"] = {
                "data": endeks_data,
                "toplam_satir": len(endeks_data)
            }
            print(f"✅ ENDEKSLER okundu: {len(endeks_data)} satır")
        
        # 3. FON_EMTIA_COIN_DOVIZ SAYFASI
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            print(f"💰 FON_EMTIA_COIN_DOVIZ sayfası okunuyor...")
            
            fon_data = []
            # İlk 100 satırı oku
            for row in ws.iter_rows(min_row=1, max_row=min(101, ws.max_row), values_only=True):
                row_data = []
                for cell_val in row:
                    if cell_val is not None:
                        if isinstance(cell_val, datetime):
                            row_data.append(cell_val.strftime("%d.%m.%Y"))
                        elif isinstance(cell_val, float):
                            row_data.append(round(cell_val, 4))
                        elif isinstance(cell_val, (int, float)):
                            row_data.append(cell_val)
                        else:
                            row_data.append(str(cell_val))
                    else:
                        row_data.append("")
                fon_data.append(row_data)
            
            data["sheets"]["FON_EMTIA_COIN_DOVIZ"] = {
                "data": fon_data,
                "toplam_satir": len(fon_data)
            }
            print(f"✅ FON_EMTIA_COIN_DOVIZ okundu: {len(fon_data)} satır")
        
        wb.close()
        print(f"🎉 TÜM EXCEL OKUNDU! Toplam: {data['sheets'].get('Sinyaller', {}).get('toplam_hisse', 0)} hisse")
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Excel okuma hatası: {str(e)}"}

def find_in_excel_data(question, excel_data):
    """Excel verilerinde soruya göre arama yap - 3 SAYFADA DA ARA!"""
    try:
        question_upper = question.upper()
        
        # Arama terimlerini al (en az 2 harfli kelimeler)
        search_terms = []
        for word in question_upper.split():
            clean_word = re.sub(r'[^A-Z0-9]', '', word)  # Sadece harf ve rakam
            if len(clean_word) >= 2:
                search_terms.append(clean_word)
        
        print(f"🔍 Aranan terimler: {search_terms}")
        
        # 1. ÖNCE: HİSSE ARA (Sinyaller sayfasında - 630+ hisse)
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            # Tüm hisselerde ara
            for hisse_adi, veriler in hisseler.items():
                hisse_clean = re.sub(r'[^A-Z0-9]', '', hisse_adi.upper())
                for term in search_terms:
                    if term in hisse_clean or hisse_clean in term:
                        print(f"✅ {hisse_adi} Sinyaller sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "hisse",
                            "data": veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        # 2. SONRA: FON/EMTİA/COİN/DÖVİZ ARA (GMSTR BURADA!)
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            fon_rows = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["data"]
            
            # İlk 50 satırda ara
            for i, row in enumerate(fon_rows[:50], 1):
                for j, cell in enumerate(row):
                    if cell:
                        cell_str = str(cell).upper()
                        cell_clean = re.sub(r'[^A-Z0-9]', '', cell_str)
                        for term in search_terms:
                            if term in cell_clean and len(term) >= 3:
                                print(f"✅ '{term}' FON_EMTIA_COIN_DOVIZ sayfasında bulundu (satır {i})")
                                return {
                                    "found": True,
                                    "type": "fon_emtia",
                                    "data": row,
                                    "sayfa": "FON_EMTIA_COIN_DOVIZ",
                                    "name": term,
                                    "satir": i,
                                    "tum_satir": row
                                }
        
        # 3. SON OLARAK: ENDEKS ARA
        if "ENDEKSLER" in excel_data["sheets"]:
            endeks_rows = excel_data["sheets"]["ENDEKSLER"]["data"]
            
            # İlk 20 satırda ara
            for i, row in enumerate(endeks_rows[:20], 1):
                for j, cell in enumerate(row):
                    if cell:
                        cell_str = str(cell).upper()
                        cell_clean = re.sub(r'[^A-Z0-9]', '', cell_str)
                        for term in search_terms:
                            if term in cell_clean and len(term) >= 3:
                                print(f"✅ '{term}' ENDEKSLER sayfasında bulundu (satır {i})")
                                return {
                                    "found": True,
                                    "type": "endeks",
                                    "data": row,
                                    "sayfa": "ENDEKSLER",
                                    "name": term,
                                    "satir": i
                                }
        
        # Hiçbir şey bulunamadı
        print(f"⚠️ Hiçbir sayfada bulunamadı: {search_terms}")
        return {
            "found": False,
            "type": None,
            "data": None,
            "sayfa": None,
            "name": None,
            "excel_file": excel_data["excel_file"]
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
                "sayfalar": ["Sinyaller (630+ hisse)", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"],
                "not": "En güncel Excel otomatik bulunur, 3 SAYFADA DA ARA"
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
            print("📥 Excel indiriliyor ve TÜM veriler okunuyor...")
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
            
            # 4. SORUYU EXCEL VERİLERİNDE ARA (3 SAYFADA DA!)
            print("🔍 Soru Excel verilerinde analiz ediliyor (3 sayfada da aranıyor)...")
            analysis = find_in_excel_data(question, excel_result["data"])
            
            # 5. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 6. PROMPT HAZIRLA (TÜM EXCEL VERİLERİYLE)
            prompt = f"""🎯 **BORSAANALIZ AI - GERÇEK EXCEL VERİ ANALİZİ**

**📊 GÜNCEL EXCEL RAPORU:** {excel_result['data']['excel_file']} ({excel_date})
**⏰ ANALİZ ZAMANI:** {excel_result['data']['timestamp']}
**📈 TOPLAM HİSSE:** {excel_result['data']['sheets'].get('Sinyaller', {}).get('toplam_hisse', 0)}+

**❓ KULLANICI SORUSU:** {question}

"""
            
            # BULUNAN VERİLERİ EKLE
            if analysis.get("found"):
                if analysis["type"] == "hisse":
                    hisse_data = analysis["data"]
                    prompt += f"""📈 **HİSSE ANALİZİ: {analysis['name']}**

**TEKNİK GÖSTERGELER (Excel'den alındı):**
"""
                    # Önemli alanları göster
                    important_fields = ['Close', 'Open', 'High', 'Low', 'Hacim', 'VMA',
                                      'EMA_8', 'EMA_21', 'EMA_55', 'Pivot', 'Trend',
                                      'S1', 'R1', 'BB_UPPER', 'BB_LOWER', 'Pearson55']
                    
                    fields_found = 0
                    for field in important_fields:
                        if field in hisse_data:
                            value = hisse_data[field]
                            prompt += f"- **{field}:** {value}\n"
                            fields_found += 1
                    
                    if fields_found > 0:
                        prompt += f"\n✅ **{analysis['name']}** hissesi Excel'de bulundu ({analysis['sayfa']} sayfası). Yukarıdaki değerler GERÇEKTİR.\n\n"
                    else:
                        prompt += f"\n⚠️ **{analysis['name']}** Excel'de bulundu ama teknik veriler eksik.\n\n"
                
                elif analysis["type"] == "fon_emtia":
                    fon_data = analysis["data"]
                    prompt += f"""💰 **FON/EMTİA/DÖVİZ ANALİZİ: {analysis['name']}**

**EXCEL VERİLERİ ({analysis['sayfa']} sayfası):**
"""
                    for i, value in enumerate(fon_data, 1):
                        if value not in ["", None]:
                            prompt += f"- Değer {i}: {value}\n"
                    
                    prompt += f"\n✅ **{analysis['name']}** Excel'de bulundu ({analysis['sayfa']} sayfası, satır {analysis.get('satir', 'N/A')}).\n\n"
                
                elif analysis["type"] == "endeks":
                    endeks_data = analysis["data"]
                    prompt += f"""📊 **ENDEKS ANALİZİ: {analysis['name']}**

**EXCEL VERİLERİ ({analysis['sayfa']} sayfası):**
"""
                    for i, value in enumerate(endeks_data, 1):
                        if value not in ["", None]:
                            prompt += f"- Değer {i}: {value}\n"
                    
                    prompt += f"\n✅ **{analysis['name']}** Excel'de bulundu ({analysis['sayfa']} sayfası).\n\n"
            
            else:
                prompt += """⚠️ **NOT:** Sorunuzdaki sembol Excel'de bulunamadı.

Excel raporunda şunlar mevcut:
• **Sinyaller:** 630+ hisse senedi
• **ENDEKSLER:** BIST endeksleri
• **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto para

**Lütfen hisse, endeks veya sembol adını doğru yazın.**

"""
            
            # DETAYLI ANALİZ TALİMATLARI (KÜÇÜLTMEDİM!)
            prompt += """🎯 **DETAYLI ANALİZ TALİMATLARI:**

1. **SADECE** yukarıdaki Excel verilerini kullanarak teknik analiz yap
2. **VMA (Volume Moving Algorithm)** değerini MUTLAKA analiz et ve yorumla
3. Close fiyatını, EMA değerlerini (EMA_8, EMA_21, EMA_55) karşılaştır
4. Pivot noktasını ve destek/direnç seviyelerini (S1, R1) belirt
5. Trend durumunu (YÜKSELİŞ/YANAL/DÜŞÜŞ) açıkla
6. Hacim verisini yorumla - yüksek/düşük/orta hacim mi?
7. Bollinger Bantları (BB_UPPER, BB_LOWER) ve Pearson korelasyonunu değerlendir
8. **RSI ve MACD'den BAHSETME** - bunlar Excel raporunda yok
9. Sayısal değerleri net şekilde belirt (Örnek: "Close: 322.50 TL")
10. **KESİNLİKLE yatırım tavsiyesi VERME** - sadece teknik analiz yap
11. Kapsamlı ama öz olsun (300-400 kelime ideal)

📊 **PROFESYONEL ANALİZ FORMATI:**

**1. VERİ ÖZETİ**
• Mevcut fiyat ve temel göstergeler
• VMA ve hacim analizi
• EMA'lar ve trend yapısı

**2. TEKNİK YORUM (VMA BAZLI)**
• VMA değerinin anlamı ve yorumu
• Fiyat-VMA ilişkisi
• Trendin gücü ve sürdürülebilirliği

**3. KRİTİK SEVİYELER**
• Ana destek ve direnç noktaları
• Pivot ve Bollinger Bantları
• Riskli ve fırsat alanları

**4. GÖZLEMLER VE ÖNERİLER (BİLGİ AMAÇLI)**
• Genel teknik görünüm
• İzlenmesi gereken seviyeler
• Dikkat edilmesi gereken riskler

**ÖNEMLİ:** Tüm analiz Excel'deki GERÇEK verilere dayanmalıdır. Hisse açılımları yazma, sadece sembol kullan.
**ÖNEMLİ:** TÜM bölümleri tamamla. Analiz yarım kalmasın.
**CEVAP:**
"""
            
            print(f"📝 Prompt hazır ({len(prompt):,} karakter)")
            
            # 7. DEEPSEEK API'Yİ ÇAĞIR
            ai_start = datetime.now()
            url = "https://api.deepseek.com/chat/completions"
            
            # MAX TOKEN'ı 500 yap (daha kısa değil, optimal)
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 700,  # 600'den 500'e düşürdüm (çok uzun olmasın)
                "temperature": 0.1
            }
            
            json_data = json.dumps(request_data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz-AI/3.0'
                }
            )
            
            print("🔄 DeepSeek API çağrılıyor...")
            response = urllib.request.urlopen(req, timeout=45)
            response_data = json.loads(response.read().decode('utf-8'))
            ai_time = (datetime.now() - ai_start).total_seconds()
            
            print(f"✅ DeepSeek yanıt aldı ({ai_time:.2f} sn)")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # 8. YANIT VER (TOKEN SAYISI GİZLİ)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                total_time = excel_time + ai_time
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    # "tokens": response_data.get('usage', {}).get('total_tokens', 0),  # GİZLİ
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
                        "toplam_hisse": excel_result["data"]["sheets"].get("Sinyaller", {}).get("toplam_hisse", 0)
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
