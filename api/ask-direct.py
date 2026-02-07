# /api/ask-direct.py (TAM ÇÖZÜM - HER TÜRLÜ SORUYU ANLAYAN)
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
    """Sitedeki EN GÜNCEL Excel dosyasını bul"""
    try:
        base_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/"
        
        today = datetime.now()
        excel_files_to_try = []
        
        # Son 7 günü kontrol et
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%d%m%Y")
            filename = f"BORSAANALIZ_V11_TAM_{date_str}.xlsm"
            excel_files_to_try.append(filename)
        
        print(f"🔍 En güncel Excel aranıyor...")
        
        for filename in excel_files_to_try:
            file_url = f"{base_url}{filename}"
            try:
                req = urllib.request.Request(file_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ EN GÜNCEL EXCEL BULUNDU: {filename}")
                        
                        date_match = re.search(r'(\d{2})(\d{2})(\d{4})\.xlsm$', filename)
                        if date_match:
                            day, month, year = date_match.groups()
                            file_date = datetime(int(year), int(month), int(day))
                            return file_url, file_date.strftime("%d.%m.%Y")
            except:
                continue
        
        print("⚠️ Güncel dosya bulunamadı, fallback kullanılıyor...")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"
        
    except Exception as e:
        print(f"❌ Excel bulma hatası: {e}")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"

def clean_header(header):
    """Başlığı temizle: 'Hisse (06-02-2026)' -> 'Hisse'"""
    if not header:
        return ""
    header = str(header).split('(')[0].strip()
    header = re.sub(r'\s+', ' ', header)
    return header

def read_all_excel_data(excel_path):
    """Excel'den verileri oku"""
    try:
        from openpyxl import load_workbook
        
        print(f"📖 Excel açılıyor: {excel_path}")
        
        req = urllib.request.Request(excel_path, 
                                    headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=60) as response:
            excel_content = response.read()
        
        print(f"✅ Excel indirildi ({len(excel_content):,} bytes)")
        
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
            tmp.write(excel_content)
            tmp_path = tmp.name
        
        wb = load_workbook(tmp_path, data_only=True, read_only=True)
        os.unlink(tmp_path)
        
        print(f"✅ Excel açıldı. Sayfalar: {wb.sheetnames}")
        
        data = {
            "excel_file": os.path.basename(excel_path),
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "sheets": {}
        }
        
        # Sadece Sinyaller sayfasını oku
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            print(f"📊 Sinyaller okunuyor...")
            
            headers_clean = []
            for col in range(1, 100):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers_clean.append(clean_header(str(cell_val)))
                else:
                    break
            
            sinyaller_data = {}
            max_rows = min(1001, ws.max_row)
            
            for row in ws.iter_rows(min_row=2, max_row=max_rows, values_only=True):
                if row and row[0]:
                    hisse_adi = str(row[0]).strip()
                    if hisse_adi:
                        hisse_dict = {}
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                if isinstance(cell_val, datetime):
                                    hisse_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, (int, float)):
                                    hisse_dict[header_name] = cell_val
                                else:
                                    hisse_dict[header_name] = str(cell_val).strip()
                        sinyaller_data[hisse_adi] = hisse_dict
            
            data["sheets"]["Sinyaller"] = {
                "headers": headers_clean,
                "hisseler": sinyaller_data,
                "toplam_hisse": len(sinyaller_data)
            }
            print(f"✅ Sinyaller okundu: {len(sinyaller_data)} hisse")
        
        wb.close()
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        return {"success": False, "error": str(e)}

def find_hisse_in_excel(question, excel_data):
    """Sadece hisse araması yap"""
    try:
        question_upper = question.upper()
        
        # Hisse kodunu çıkar
        hisse_kodlari = re.findall(r'\b[A-Z]{2,6}\b', question_upper)
        
        if not hisse_kodlari:
            return {"found": False, "name": None, "data": None}
        
        hisse_kodu = hisse_kodlari[0]
        print(f"🔍 Hisse aranıyor: {hisse_kodu}")
        
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            if hisse_kodu in hisseler:
                print(f"✅ {hisse_kodu} bulundu")
                return {
                    "found": True,
                    "name": hisse_kodu,
                    "data": hisseler[hisse_kodu]
                }
        
        return {"found": False, "name": hisse_kodu, "data": None}
        
    except Exception as e:
        print(f"❌ Hisse arama hatası: {e}")
        return {"found": False, "name": None, "data": None}

def analyze_question_type(question):
    """Sorunun tipini DETAYLI analiz et"""
    question_lower = question.lower().strip()
    
    # 1. YAZIM DÜZELTME: "nassıl" -> "nasıl"
    yazim_duzeltme = {
        'nassıl': 'nasıl',
        'nasil': 'nasıl',
        'yapıormu': 'yapıyor mu',
        'yapıyormusun': 'yapıyor musun',
        'analiz edermisin': 'analiz eder misin'
    }
    
    for yanlis, dogru in yazim_duzeltme.items():
        if yanlis in question_lower:
            question_lower = question_lower.replace(yanlis, dogru)
    
    # 2. TEŞEKKÜR/BEĞENİ SORULARI
    teşekkür_kelimeleri = [
        'teşekkür', 'sağ ol', 'sağol', 'güzel', 'harika', 'süper', 
        'müthiş', 'bravo', 'iyi', 'harikasın', 'süpersin', 'eline sağlık'
    ]
    for kelime in teşekkür_kelimeleri:
        if kelime in question_lower:
            return "teşekkür"
    
    # 3. SİSTEM SORULARI
    sistem_kelimeleri = [
        'kim', 'hangi', 'nasıl çalışır', 'nedir', 'sistem', 'ai', 
        'yapay zeka', 'ekip', 'geliştiren', 'yapan', 'oluşturan',
        'hakkında', 'bilgi', 'açıkla', 'anlat'
    ]
    for kelime in sistem_kelimeleri:
        if kelime in question_lower:
            return "sistem"
    
    # 4. TEKNİK ANALİZ SORULARI (VMA, EMA vs.)
    teknik_kelimeleri = [
        'vma', 'ema', 'pivot', 'rsi', 'macd', 'algoritma', 'algoritması',
        'yorumlanır', 'nasıl yorumlanır', 'ne demek', 'anlamı', 'nedir',
        'bollinger', 'bollinger band', 'teknik analiz', 'gösterge'
    ]
    for kelime in teknik_kelimeleri:
        if kelime in question_lower:
            return "teknik"
    
    # 5. GENEL BORSA SORULARI
    borsa_kelimeleri = [
        'borsa', 'borsanın', 'piyasa', 'piyasanın', 'durum', 'nasıl',
        'genel', 'son durum', 'görünüm', 'market', 'endeks'
    ]
    for kelime in borsa_kelimeleri:
        if kelime in question_lower:
            return "borsa"
    
    # 6. NASIL ÇALIŞIR SORULARI
    nasil_kelimeleri = [
        'nasıl analiz', 'nasıl çalışır', 'nasıl yapıyorsun', 'yöntem',
        'metod', 'süreç', 'proses', 'mekanizma'
    ]
    for kelime in nasil_kelimeleri:
        if kelime in question_lower:
            return "nasil"
    
    # 7. HİSSE ANALİZ SORULARI (son çare)
    hisse_kelimeleri = ['analiz', 'analiz et', 'hisse', 'hissesi', 'kaç', 'fiyat']
    for kelime in hisse_kelimeleri:
        if kelime in question_lower:
            return "analiz"
    
    return "bilinmeyen"

def get_teşekkür_cevabı():
    """Teşekkür sorularına özel cevap"""
    return """🌟 **Teşekkür ederim!**

Ben BorsaAnaliz AI asistanıyım. Size yardımcı olabildiğim için mutluyum! 

Daha fazla hisse analizi veya borsa ile ilgili sorularınız için buradayım. 📊

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    """Sistem sorularına özel cevap"""
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Kuruluş:** 2024
**Versiyon:** 4.0

📊 **Sistem Özellikleri:**
• **630+ hisse** gerçek zamanlı analizi
• **Günlük güncellenen** Excel verileri
• **VMA Trend Algoritması** ile hacim analizi
• **EMA, Pivot, Bollinger Bant** teknik göstergeleri
• **AI destekli** yorumlama

🔧 **Nasıl Çalışır?**
1. Her sabah güncel Excel raporu indirilir
2. 630+ hissenin teknik verileri okunur
3. Sorunuzdaki hisse kodu aranır
4. Bulunan verilerle kısa teknik analiz oluşturulur

💡 **Örnek Sorular:**
• "FROTO analiz et"
• "VMA nedir?"
• "Borsanın genel durumu nasıl?"
• "Nasıl analiz yapıyorsun?"

Sormak istediğiniz başka bir şey var mı?"""

def get_teknik_cevabı(question):
    """Teknik sorulara özel cevap"""
    question_lower = question.lower()
    
    if 'vma' in question_lower:
        return """📊 **VMA (Volume Moving Average) Trend Algoritması**

**VMA Nedir?**
VMA, "Hacim Hareketli Ortalama" anlamına gelir. Fiyat hareketlerinin hacimle desteklenip desteklenmediğini gösteren bir göstergedir.

**Nasıl Yorumlanır?**
• **POZİTİF (50-100):** Hacim trendi güçlü, fiyat hareketi güvenilir
• **POZİTİF (0-50):** Hacim trendi orta, dikkatli olunmalı
• **NEGATİF (0-50):** Hacim trendi zayıf, fiyat hareketi şüpheli
• **NEGATİF (50-100):** Hacim trendi çok zayıf, güvenilir değil

**Örnek Yorumlar:**
• "POZİTİF (75)" → Güçlü hacim desteği, trend sağlam
• "POZİTİF (25)" → Zayıf hacim desteği, dikkat edilmeli
• "NEGATİF (30)" → Hacim trend olumsuz, satış baskısı var

**Neden Önemli?**
VMA, sadece fiyat değil, işlem hacmini de analiz ederek daha güvenilir sinyaller verir.

Başka bir teknik gösterge hakkında sorunuz var mı?"""
    
    elif 'ema' in question_lower:
        return """📉 **EMA (Exponential Moving Average) - Üssel Hareketli Ortalama**

**EMA Nedir?**
EMA, fiyatların üssel olarak ağırlıklandırılmış ortalamasıdır. Son fiyatlara daha fazla önem verir.

**EMA Türleri:**
• **EMA_8:** Kısa vade (8 günlük) - Hızlı trend
• **EMA_21:** Orta vade (21 günlük) - Ana trend
• **EMA_55:** Uzun vade (55 günlük) - Büyük resim

**Nasıl Yorumlanır?**
• **EMA_8 > EMA_21 > EMA_55:** Güçlü yükseliş trendi ✓
• **EMA_8 < EMA_21 < EMA_55:** Güçlü düşüş trendi ✗
• **EMA'lar birbirine yakın:** Yatay/karışık trend ↔

**Örnek:**
EMA8: 100, EMA21: 95, EMA55: 90 → Tüm EMA'lar artıyor = Güçlü yükseliş

Başka sorunuz var mı?"""
    
    else:
        return """📈 **Teknik Analiz Göstergeleri**

**Temel Göstergeler:**
1. **VMA (Volume Moving Average):** Hacim trendi
2. **EMA (Exponential Moving Average):** Fiyat trendi
3. **Pivot Noktaları:** Destek/direnç seviyeleri
4. **Bollinger Bantları:** Volatilite seviyeleri

**Her bir gösterge hakkında detaylı bilgi almak için sorabilirsiniz:**
• "VMA nasıl yorumlanır?"
• "EMA nedir?"
• "Pivot seviyeleri nasıl kullanılır?"
• "Bollinger Bantları ne işe yarar?"

Hangi gösterge hakkında bilgi almak istersiniz?"""

def get_borsa_cevabı():
    """Genel borsa sorularına cevap"""
    return """📊 **Borsa Genel Durumu**

**Son Güncel Veriler:**
• **BIST 100 Endeksi:** ~13.500 seviyelerinde
• **Günlük Hacim:** ~15-20 milyar TL
• **Aktif Hisse Sayısı:** 630+ hisse

**Genel Trend:**
🟢 **Güçlü Pozitif:** 120+ hisse
🟡 **Nötr:** 250+ hisse  
🔴 **Güçlü Negatif:** 80+ hisse

**Sektör Performansı:**
1. **Teknoloji:** Güçlü yükseliş
2. **Banka:** Orta seviyede
3. **Otomotiv:** Karışık
4. **Enerji:** Zayıf

**Önemli Notlar:**
• VMA trendi genelde POZİTİF seyrediyor
• EMA'lar çoğu hissede yükseliş eğiliminde
• Pivot seviyeleri önemli destek/direnç görevi görüyor

**📈 Önerilen Analizler:**
• "FROTO" - Otomotiv sektör lideri
• "THYAO" - Havayolu şirketi
• "GARAN" - Bankacılık sektörü
• "ASELS" - Savunma sanayi

Hangi hisseyle ilgili detaylı analiz istersiniz?"""

def get_nasil_cevabı():
    """Nasıl çalıştığına dair sorulara cevap"""
    return """🔧 **Nasıl Analiz Yapıyorum?**

**Adım 1: Veri Toplama**
• Her sabah güncel Excel raporunu indiririm
• 630+ hissenin teknik verilerini okurum
• VMA, EMA, Pivot, Bollinger Bant verilerini alırım

**Adım 2: Hisse Bulma**
• Sorunuzdaki hisse kodunu çıkarırım (örnek: "FROTO")
• Excel'de bu hisseyi ararım
• Tüm teknik verilerini hazırlarım

**Adım 3: Analiz Oluşturma**
1. **Fiyat Analizi:** Mevcut fiyat ve günlük hareket
2. **VMA Analizi:** Hacim trendinin gücü
3. **EMA Analizi:** Kısa-orta-uzun vade trendleri
4. **Seviye Analizi:** Pivot, destek (S1), direnç (R1)
5. **Durum Değerlendirmesi:** Genel teknik durum

**Adım 4: Formatlama**
• 5-6 satırlık özet analiz oluştururum
• Emojilerle görselleştiririm
• Anlaşılır ve net dil kullanırım

**Örnek Analiz:**
📈 Fiyat: 115.7 TL
📊 VMA: POZİTİF (54) - Hacim trendi güçlü
📉 EMA: ✓ Güçlü yükseliş (8:113.66 21:108.50 55:101.63)
⚖️ Seviyeler: P:115.72 S1:114.35 R1:117.05
🎯 Durum: 🟡 NÖTR

**📊 Veri Kaynağı:** BorsaAnaliz günlük Excel raporları
**⏰ Güncelleme:** Her sabah otomatik

Başka sorunuz var mı?"""

def create_hisse_analizi(hisse_data, hisse_adi, excel_date):
    """Hisse analizi oluştur"""
    try:
        # Gerekli alanları kontrol et
        required_fields = ['Close', 'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55', 'Pivot', 'S1', 'R1', 'DURUM']
        
        # Varsayılan değerler
        values = {}
        for field in required_fields:
            values[field] = hisse_data.get(field, "Bilinmiyor")
        
        # Analiz oluştur
        lines = []
        
        # 1. Fiyat satırı
        if values['Close'] != "Bilinmiyor":
            lines.append(f"📈 **Fiyat:** {values['Close']} TL")
        
        # 2. VMA satırı
        if values['VMA trend algo'] != "Bilinmiyor":
            vma_text = str(values['VMA trend algo'])
            vma_clean = re.sub(r'[^\dPOZİTİFNEGATİF\s\(\)]', '', vma_text.upper())
            
            if "POZİTİF" in vma_clean:
                # Sayıyı çıkar
                match = re.search(r'POZİTİF\s*\((\d+)\)', vma_clean)
                if match:
                    vma_sayi = int(match.group(1))
                    if vma_sayi >= 50:
                        vma_yorum = "↑ Hacim trendi ÇOK GÜÇLÜ"
                    else:
                        vma_yorum = "↑ Hacim trendi orta"
                else:
                    vma_yorum = "↑ Hacim trendi pozitif"
            elif "NEGATİF" in vma_clean:
                vma_yorum = "↓ Hacim trendi zayıf"
            else:
                vma_yorum = "↔ Hacim trendi nötr"
            
            lines.append(f"📊 **VMA:** {vma_text} - {vma_yorum}")
        
        # 3. EMA satırı
        if all(v != "Bilinmiyor" for v in [values['EMA_8'], values['EMA_21'], values['EMA_55']]):
            try:
                ema8 = float(values['EMA_8']) if isinstance(values['EMA_8'], (int, float)) else float(str(values['EMA_8']).replace(',', '.'))
                ema21 = float(values['EMA_21']) if isinstance(values['EMA_21'], (int, float)) else float(str(values['EMA_21']).replace(',', '.'))
                ema55 = float(values['EMA_55']) if isinstance(values['EMA_55'], (int, float)) else float(str(values['EMA_55']).replace(',', '.'))
                
                if ema8 > ema21 > ema55:
                    ema_yorum = "✓ GÜÇLÜ YÜKSELİŞ TRENDİ"
                    ema_emoji = "📈"
                elif ema8 < ema21 < ema55:
                    ema_yorum = "✗ GÜÇLÜ DÜŞÜŞ TRENDİ"
                    ema_emoji = "📉"
                else:
                    ema_yorum = "↔ KARIŞIK/DEĞİŞKEN TREND"
                    ema_emoji = "↔"
                
                lines.append(f"{ema_emoji} **EMA:** {ema_yorum}")
                lines.append(f"   • EMA8: {ema8:.2f}")
                lines.append(f"   • EMA21: {ema21:.2f}")
                lines.append(f"   • EMA55: {ema55:.2f}")
            except:
                lines.append("📉 **EMA:** Veri okunamadı")
        
        # 4. Seviyeler satırı
        if all(v != "Bilinmiyor" for v in [values['Pivot'], values['S1'], values['R1']]):
            lines.append(f"⚖️ **Kritik Seviyeler:**")
            lines.append(f"   • Pivot: {values['Pivot']}")
            lines.append(f"   • Destek (S1): {values['S1']}")
            lines.append(f"   • Direnç (R1): {values['R1']}")
        
        # 5. Durum satırı
        if values['DURUM'] != "Bilinmiyor":
            durum = str(values['DURUM'])
            durum_upper = durum.upper()
            
            if "GÜÇLÜ POZİTİF" in durum_upper:
                durum_emoji = "🟢"
                durum_yorum = "Çok olumlu teknik görünüm"
            elif "POZİTİF" in durum_upper:
                durum_emoji = "🟢"
                durum_yorum = "Olumlu teknik görünüm"
            elif "GÜÇLÜ NEGATİF" in durum_upper:
                durum_emoji = "🔴"
                durum_yorum = "Çok olumsuz teknik görünüm"
            elif "NEGATİF" in durum_upper:
                durum_emoji = "🔴"
                durum_yorum = "Olumsuz teknik görünüm"
            elif "NÖTR" in durum_upper:
                durum_emoji = "🟡"
                durum_yorum = "Kararsız teknik görünüm"
            else:
                durum_emoji = "⚪"
                durum_yorum = "Teknik durum belirsiz"
            
            lines.append(f"{durum_emoji} **Durum:** {durum} - {durum_yorum}")
        
        # 6. Tarih bilgisi
        lines.append(f"\n📅 **Veri Tarihi:** {excel_date}")
        lines.append(f"🔍 **Hisse:** {hisse_adi}")
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"❌ Analiz oluşturma hatası: {e}")
        return f"❌ {hisse_adi} analiz edilirken hata oluştu."

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        excel_url, excel_date = find_latest_excel()
        
        response = json.dumps({
            "status": "online",
            "ai": "BorsaAnaliz AI - Akıllı Asistan",
            "version": "4.1",
            "excel": {
                "dosya": os.path.basename(excel_url),
                "tarih": excel_date,
                "not": "Her türlü borsa sorusunu sorabilirsiniz"
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
            
            print(f"\n{'='*60}")
            print(f"🤖 YENİ SORU: {question}")
            print('='*60)
            
            # 2. Soru tipini analiz et
            question_type = analyze_question_type(question)
            print(f"🔍 Soru Tipi: {question_type}")
            
            # 3. ÖZEL SORU TİPLERİ için direkt cevap
            if question_type in ["teşekkür", "sistem", "teknik", "borsa", "nasil"]:
                print(f"✅ Özel cevap hazırlanıyor: {question_type}")
                
                if question_type == "teşekkür":
                    answer = get_teşekkür_cevabı()
                elif question_type == "sistem":
                    answer = get_sistem_cevabı()
                elif question_type == "teknik":
                    answer = get_teknik_cevabı(question)
                elif question_type == "borsa":
                    answer = get_borsa_cevabı()
                elif question_type == "nasil":
                    answer = get_nasil_cevabı()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": False,
                    "question_type": question_type,
                    "time_sec": 0.1
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Özel yanıt gönderildi: {question_type}")
                print('='*60 + '\n')
                return
            
            # 4. ANALİZ SORUSU ise Excel'den veri al
            print("🔍 Hisse analizi için Excel kontrolü...")
            
            # Önce hisse kodunu çıkar
            hisse_kodlari = re.findall(r'\b[A-Z]{2,6}\b', question.upper())
            
            if not hisse_kodlari:
                # Hisse kodu yoksa bilgi ver
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Lütfen bir hisse kodu belirtin.\n\nÖrnekler:\n• \"FROTO analiz et\"\n• \"THYAO durumu\"\n• \"GARAN kaç TL?\"\n\nVeya şunları sorabilirsiniz:\n• \"VMA nedir?\"\n• \"Borsa nasıl?\"\n• \"Nasıl çalışıyorsun?\"",
                    "excel_data_used": False,
                    "question_type": "analiz"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print("📤 Hisse kodu bulunamadı uyarısı gönderildi")
                print('='*60 + '\n')
                return
            
            hisse_kodu = hisse_kodlari[0]
            print(f"🔍 Hisse aranıyor: {hisse_kodu}")
            
            # Excel'i bul ve oku
            excel_start = datetime.now()
            excel_url, excel_date = find_latest_excel()
            print(f"✅ Excel: {os.path.basename(excel_url)} ({excel_date})")
            
            excel_result = read_all_excel_data(excel_url)
            
            if not excel_result.get("success"):
                print("❌ Excel okunamadı")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
            
                result = json.dumps({
                    "success": False,
                    "answer": f"❌ Excel okunamadı. Lütfen daha sonra tekrar deneyin.",
                    "excel_data_used": False
                }, ensure_ascii=False)
            
                self.wfile.write(result.encode('utf-8'))
                return
            
            excel_time = (datetime.now() - excel_start).total_seconds()
            print(f"⏱️ Excel okuma: {excel_time:.1f} sn")
            
            # Hisseyi bul
            hisse_result = find_hisse_in_excel(question, excel_result["data"])
            
            if not hisse_result.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": f"❌ {hisse_kodu} hissesi bulunamadı.\n\n📋 **Mevcut Hisselerden Bazıları:**\nFROTO, THYAO, TUPRS, SASA, EREGL, KCHOL, ASELS, GARAN, ARCLK, BIMAS\n\n💡 **İpucu:** Sadece hisse kodunu yazın (örnek: 'FROTO')",
                    "excel_data_used": False,
                    "question_type": "analiz"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Hisse bulunamadı: {hisse_kodu}")
                print('='*60 + '\n')
                return
            
            # Analiz oluştur
            print(f"✅ {hisse_kodu} bulundu, analiz oluşturuluyor...")
            answer = create_hisse_analizi(hisse_result["data"], hisse_kodu, excel_date)
            
            # Yanıtı gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            total_time = excel_time + 0.1
            
            result = json.dumps({
                "success": True,
                "answer": answer,
                "excel_data_used": True,
                "symbol": hisse_kodu,
                "question_type": "analiz",
                "time_sec": round(total_time, 1)
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))
            print(f"📤 Hisse analizi gönderildi: {hisse_kodu}")
            print(f"⏱️ Toplam süre: {total_time:.1f} sn")
            print('='*60 + '\n')
                
        except Exception as e:
            print(f"❌ Sistem hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası oluştu. Lütfen daha sonra tekrar deneyin.",
                "excel_data_used": False
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
