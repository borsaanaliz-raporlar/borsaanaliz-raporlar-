
#!/usr/bin/env python3
"""
BORSAANALİZ V11 UZMAN TEKNİK ANALİST
⚡ HIZLI (DeepSeek) + 📋 DETAYLI (DeepSeek+Groq) BUTONLU SİSTEM
"""
# ============ ZORUNLU: ESKİ BİLGİLERİ UNUT ============
AI_TALIMAT = """ESKİ BİLGİLERİ UNUT! SADECE BUNU BİL:

VMA = HACİM AĞIRLIKLI TREND ALGORİTMASI
- POZİTİF(57) = 57 gündür yükselen trend
- NEGATİF(7) = 7 gündür düşen trend

ASLA "Volume Moving Average" deme!
ASLA MACD, RSI kullanma!
"""
# ===================================================
import os
import sys
import json
import re
from openpyxl import load_workbook
import requests
from datetime import datetime
from excel_finder import find_latest_excel

# API AYARLARI
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ============= MODE AYARI =============
# 📋 Web'den gelen soruda "detaylı" kelimesi varsa DETAYLI mod
def is_detailed_mode(question):
    """Detaylı analiz isteği kontrolü"""
    detailed_keywords = ["detaylı", "detayli", "kapsamlı", "kapsamli", "profesyonel", "uzun"]
    return any(keyword in question.lower() for keyword in detailed_keywords)

def get_excel_data_for_ai(excel_path):
    """Excel'deki TÜM verileri al"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        target_sheets = ["Sinyaller", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
        
        for sheet_name in target_sheets:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = []
                
                headers = []
                col = 1
                while True:
                    cell_value = ws.cell(row=1, column=col).value
                    if cell_value:
                        headers.append(str(cell_value).strip())
                        col += 1
                    else:
                        break
                
                for row in ws.iter_rows(min_row=2, max_row=500, values_only=True):
                    if row and row[0] and row[0] not in ["Toplam", "Genel", "Ortalama", "Sektör", "Hisse", "Sembol"]:
                        row_dict = {}
                        for i, val in enumerate(row):
                            if i < len(headers) and val is not None:
                                row_dict[headers[i]] = val
                        if row_dict:
                            sheet_data.append(row_dict)
                
                all_data[sheet_name] = {
                    "headers": headers,
                    "data": sheet_data,
                    "count": len(sheet_data)
                }
                print(f"✅ {sheet_name}: {len(sheet_data)} hisse, {len(headers)} kolon")
        
        wb.close()
        
        return {
            "data": all_data,
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "file": os.path.basename(excel_path)
        }
        
    except Exception as e:
        return {"error": f"Excel okuma hatası: {str(e)}"}

def extract_hisse_adi(question):
    """HİSSE ADI BULUCU - LİSTE YOK, SAF REGEX!"""
    words = re.findall(r'\b[A-Z0-9]{3,8}\b', question.upper())
    return words[0] if words else None

def get_hisse_raw_data(hisse_info, headers):
    """Hisse'nin ham verilerini formatlı şekilde döndür"""
    ham_veriler = ""
    kritik_kolonlar = [
        "Hisse", "Close", "Pivot", "WT Sinyal", "WT1", "WT2",
        "VMA trend algo", "LSMA KAMA", "HMA_89",
        "S3", "S2", "S1", "R1", "R2", "R3",
        "EMA_8", "EMA_13", "EMA_21", "EMA_34", "EMA_55", "EMA_89", "EMA_144", "EMA_233",
        "Pearson55", "Pearson89", "Pearson144", "Pearson233",
        "BB_UPPER", "BB_MIDDLE", "BB_LOWER",
        "Hacim", "Hacim_Değişim_%", "Hacim_Senaryo",
        "SMI", "SMI_EMA", "AI_YORUM"
    ]
    
    for kolon in kritik_kolonlar:
        if kolon in hisse_info and hisse_info[kolon] is not None:
            deger = hisse_info[kolon]
            ham_veriler += f"• **{kolon}:** {deger}\n"
    
    return ham_veriler

def create_quick_prompt(question, excel_data, hisse_adi=None):
    """⚡ HIZLI ANALİZ - Sadece DeepSeek, kısa prompt"""
    
    timestamp = excel_data["timestamp"]
    data = excel_data["data"]
    
    system_intro = f"""🎯 **BORSAANALİZ V11 HIZLI ANALİZ**
📅 {timestamp}

**📊 KRİTİK GÖSTERGELER:**
• VMA: %94 doğruluk, parantez içi GÜN SAYISI
• POZİTİF(57) = 57 gündür yükselen trend, NEGATİF(7) = 7 gündür düşen trend
• LSMA: Trend göstergesi, parantez içi GÜN SAYISI
• Pearson: >0.3 yükseliş, <-0.3 düşüş

**🚫 YOK:** RSI, MACD, Stokastik
"""
    
    if hisse_adi and hisse_adi in str(excel_data):
        hisse_info = None
        sheet_name = None
        
        for sname, sinfo in data.items():
            for hisse in sinfo["data"]:
                hisse_name = hisse.get(sinfo["headers"][0], "")
                if hisse_name and hisse_adi.upper() in str(hisse_name).upper():
                    hisse_info = hisse
                    sheet_name = sname
                    break
        
        if hisse_info:
            ham_veri = get_hisse_raw_data(hisse_info, sinfo["headers"])
            
            prompt = system_intro + f"""

📊 **{hisse_adi} HAM VERİLER:**
{ham_veri}

**ŞU SORULARA CEVAP VER:**
1. Kısa vadeli görünüm (EMA8/21, WT)
2. Destek/direnç seviyeleri (S1/R1)
3. VMA trendi kaç gün? Ne anlama gelir?
4. Pearson regresyon analizi
5. Hacim senaryosu yorumu

⚠️ Yatırım tavsiyesi değildir.
"""
            return prompt
    
    # Genel analiz
    return system_intro + f"""

📊 **PİYASA GENEL GÖRÜNÜM**

**Soru:** {question}

Hızlı piyasa analizi yap:
- Endekslerin durumu
- Öne çıkan hisseler
- Genel trend yönü
"""

def create_detailed_prompt(question, excel_data, hisse_adi=None):
    """📋 DETAYLI ANALİZ - DeepSeek + Groq, uzun prompt"""
    
    timestamp = excel_data["timestamp"]
    data = excel_data["data"]
    
    system_intro = f"""🎯 **BORSAANALİZ V11 PROFESYONEL ANALİST**
📅 {timestamp}

═══════════════════════════════════════════
**📌 GÖSTERGE YORUM KILAVUZU:**

1️⃣ **WT (WaveTrend):** 
   • >60 = Aşırı alım
   • <-60 = Aşırı satım
   • POZİTİF/NEGATİF = Trend yönü

2️⃣ **VMA (hacim ağırlıklı trend algoritmasıdır):**
   • VMA %94 doğrulukla sinyal üreten özel bir algoritmadır
   • Bu, basit bir hareketli ortalama DEĞİLDİR!
   • POZİTİF(57) = 57 gündür yükselen trend devam ediyor
   • NEGATİF(7) = 7 gündür düşen trend devam ediyor
   • ASLA "Volume Moving Average" olarak yorumlama!
   • ASLA fiyatla karşılaştırma, sadece HACİM AĞIRLIKLI TREND olarak yorumla!

3️⃣ **LSMA KAMA:**
   • POZİTİF(48) = 48 gündür yükseliş trendi devam ediyor 
   • NEGATİF(5) = 5 gündür düşüş trendi devam ediyor

4️⃣ **PEARSON KATSAYISI:**
   • 0.70-1.00 = ÇOK GÜÇLÜ trend
   • 0.30-0.70 = GÜÇLÜ trend
   • 0.10-0.30 = ZAYIF trend
   • -0.10-0.10 = YATAY/BELİRSİZ

5️⃣ **EMA HİYERARŞİSİ:**
   • 8>13>21 = YÜKSELİŞ
   • 8<13<21 = DÜŞÜŞ
   • Karmaşık = YATAY

6️⃣ **HACİM SENARYOLARI:**
   • POZITIF_YUKSELME = Hacim artışıyla yükseliş (GÜVENİLİR)
   • NEGATIF_DUSUS = Hacim düşüşüyle düşüş (GÜVENİLİR)
   • POZITIF_DUSUS = Hacim artışıyla düşüş (SATIŞ BASKISI)
   • NEGATIF_YUKSELME = Hacim düşüşüyle yükseliş (ZAYIF)

7️⃣ **BOLLINGER BANTLARI:**
   • Fiyat > Üst bant = AŞIRI ALIM
   • Fiyat < Alt bant = AŞIRI SATIM
   • Bant içinde = NORMAL

**🚫 KESİNLİKLE YOK:** RSI, MACD, Stokastik - SAKIN KULLANMA!
**📌 PARANTEZ İÇİNDEKİ RAKAMLAR:** Trendin kaç gündür devam ettiğini gösterir!
═══════════════════════════════════════════
"""
    
    if hisse_adi:
        hisse_info = None
        sheet_name = None
        
        for sname, sinfo in data.items():
            for hisse in sinfo["data"]:
                hisse_name = hisse.get(sinfo["headers"][0], "")
                if hisse_name and hisse_adi.upper() in str(hisse_name).upper():
                    hisse_info = hisse
                    sheet_name = sname
                    break
        
        if hisse_info:
            ham_veri = get_hisse_raw_data(hisse_info, sinfo["headers"])
            
            prompt = system_intro + f"""

═══════════════════════════════════════════
📋 **DETAYLI ANALİZ: {hisse_adi}**
📌 **Kaynak:** {sheet_name}
═══════════════════════════════════════════

**📊 HAM VERİLER:**
{ham_veri}

**🔍 ŞU BAŞLIKLARDA DETAYLI ANALİZ YAP:**

1️⃣ **KISA VADELİ GÖRÜNÜM (1-5 GÜN)**
   • WT sinyali ve seviyesi
   • EMA8/EMA21 ilişkisi
   • VMA gün sayısı yorumu
   • İlk hedef direnç (R1)

2️⃣ **ORTA VADELİ GÖRÜNÜM (1-4 HAFTA)**
   • LSMA trend süresi (kaç gün?)
   • Pearson55/89 değerleri ve gücü
   • EMA hiyerarşisi analizi
   • Ana trend yönü

3️⃣ **KRİTİK SEVİYELER**
   • S1-R1 günlük hareket bandı
   • S3 (stop-loss bölgesi)
   • R3 (hedef bölgesi)
   • Pivot'a göre konum

4️⃣ **HACİM ANALİZİ**
   • VMA trendi ve süresi
   • Hacim senaryosu yorumu
   • Hacim değişim yüzdesi
   • Güvenilirlik değerlendirmesi

5️⃣ **REGRESYON ANALİZİ**
   • Pearson55 trend gücü
   • Kanal üst/alt seviyeleri
   • Fiyatın kanaldaki konumu

6️⃣ **RİSK DEĞERLENDİRMESİ**
   • Düşük/Orta/Yüksek
   • Nedenleriyle açıkla
   • Volatilite durumu

7️⃣ **YATIRIMCI NOTU**
   • İzlenecek seviyeler
   • Olası senaryolar
   • Strateji önerisi

⚠️ **YASAL UYARI:** Yatırım tavsiyesi değildir.
"""
            return prompt
    
    # Genel detaylı analiz
    return system_intro + f"""

═══════════════════════════════════════════
📋 **PİYASA DETAYLI ANALİZ**
═══════════════════════════════════════════

**Soru:** {question}

**🔍 DETAYLI PİYASA ANALİZİ:**

1️⃣ **ENDERSLERİN TEKNİK DURUMU**
   • XU100, XU030, XBANK analizi
   • WT sinyalleri
   • VMA trendleri

2️⃣ **ÖNE ÇIKAN HİSSELER**
   • En uzun VMA POZİTİF olanlar
   • Pearson55 > 0.85 olanlar
   • Hacim senaryosu güçlü olanlar

3️⃣ **SEKTÖREL DEĞERLENDİRME**
   • En güçlü sektör endeksleri
   • En zayıf sektör endeksleri
   • Sektör rotasyonu var mı?

4️⃣ **RİSK İŞTAHI**
   • POZITIF_YUKSELME oranı
   • NEGATIF_DUSUS oranı
   • Genel piyasa hissiyatı

⚠️ **YASAL UYARI:** Yatırım tavsiyesi değildir.
"""

def call_deepseek(prompt, question, detailed=False):
    """DeepSeek AI çağrısı - hızlı veya detaylı"""
    if not DEEPSEEK_API_KEY:
        return None
    
    timeout = 45 if detailed else 30  # Detaylı analizde biraz daha uzun süre
    
    try:
        print(f"🚀 DeepSeek AI {'📋 DETAYLI' if detailed else '⚡ HIZLI'} modda deneniyor...")
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "SEN BORSAANALİZ V11 ASİSTANISIN. SADECE verilen prompt'taki bilgileri kullan. SAKIN kendi bildiklerini anlatma!"},
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.0,
                "max_tokens": 2000 if detailed else 1000
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # YASAKLI KELİME KONTROLÜ
            answer = answer.replace("RSI", "⚠️ RSI (BORSAANALİZ V11'de YOK)")
            answer = answer.replace("MACD", "⚠️ MACD (BORSAANALİZ V11'de YOK)")
            answer = answer.replace("Stokastik", "⚠️ Stokastik (BORSAANALİZ V11'de YOK)")
            
            if "yatırım tavsiyesi" not in answer.lower():
                answer += "\n\n⚠️ **YASAL UYARI:** Bu analiz BORSAANALİZ V11 Excel verilerine dayanmaktadır ve yatırım tavsiyesi değildir."
            
            print(f"✅ DeepSeek {'DETAYLI' if detailed else 'HIZLI'} başarılı!")
            return answer
        else:
            print(f"⚠️ DeepSeek hata {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ DeepSeek bağlantı hatası: {str(e)}")
        return None

def call_groq(prompt, question):
    """Groq AI çağrısı - SADECE detaylı modda"""
    if not GROQ_API_KEY:
        return None
    
    try:
        print("⚡ Groq AI (zenginleştirme için) deneniyor...")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Sen BORSAANALİZ V11 uzmanısın. Verilen analizi daha anlaşılır ve akıcı hale getir, ek yorum ekle."},
                    {"role": "user", "content": f"Bu analizi zenginleştir, daha profesyonel hale getir:\n\n{question}"}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
            
    except Exception as e:
        print(f"⚠️ Groq bağlantı hatası: {str(e)}")
        return None

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("❌ Hata: Soru girmediniz!")
        return
    
    question = sys.argv[1]
    print(f"❓ SORU: {question}")
    
    # MOD BELİRLEME
    detailed_mode = is_detailed_mode(question)
    print(f"📋 MOD: {'DETAYLI' if detailed_mode else 'HIZLI'}")
    
    # Excel bul
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        print("❌ Excel dosyası bulunamadı!")
        answer = "⚠️ Excel dosyası bulunamadı. Lütfen raporlar/ klasörünü kontrol edin."
        
        with open('ai_response.txt', 'w', encoding='utf-8') as f:
            f.write(answer)
        return
    
    print(f"📁 Excel: {excel_info['name']}")
    
    # Excel verilerini oku
    excel_data = get_excel_data_for_ai(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"❌ {excel_data['error']}"
    else:
        hisse_adi = extract_hisse_adi(question)
        
        if hisse_adi:
            print(f"🎯 Hisse: {hisse_adi}")
        else:
            print("📊 Genel piyasa analizi")
        
        # MOD'A GÖRE PROMPT OLUŞTUR
        if detailed_mode:
            prompt = create_detailed_prompt(question, excel_data, hisse_adi)
            
            # 1. DeepSeek ile detaylı analiz
            answer = call_deepseek(prompt, question, detailed=True)
            
            # 2. Groq ile zenginleştir (DeepSeek başarılı olduysa)
            if answer and GROQ_API_KEY:
                print("✨ Groq ile analiz zenginleştiriliyor...")
                enriched = call_groq(prompt, answer)
                if enriched:
                    answer = enriched + "\n\n---\n📌 *Groq ile zenginleştirilmiştir.*"
        else:
            # HIZLI MOD - Sadece DeepSeek
            prompt = create_quick_prompt(question, excel_data, hisse_adi)
            answer = call_deepseek(prompt, question, detailed=False)
            
            # DeepSeek çalışmazsa Groq'u dene
            if not answer:
                print("⚠️ DeepSeek çalışmadı, Groq deneniyor...")
                prompt = create_quick_prompt(question, excel_data, hisse_adi)
                answer = call_groq(prompt, question)
        
        # HİÇBİRİ ÇALIŞMAZSA
        if not answer:
            answer = f"""⚠️ **AI SERVİSLERİNE ULAŞILAMADI**

📁 Excel: {excel_info['name']}
📅 Tarih: {excel_data['timestamp']}
📋 Mod: {'DETAYLI' if detailed_mode else 'HIZLI'}

Lütfen API anahtarlarını kontrol edin."""
    
    # Yanıtı kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print(f"\n✅ ANALİZ TAMAMLANDI!")
    print(f"📝 Yanıt kaydedildi: ai_response.txt")
    print(f"📏 Yanıt uzunluğu: {len(answer)} karakter")

if __name__ == "__main__":
    main()
