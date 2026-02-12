#!/usr/bin/env python3
"""
BORSAANALİZ PROFESYONEL TEKNİK ANALİZ UZMANI AI
DeepSeek + Groq Hibrit Sistem - %100 ÇALIŞIR
"""
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

def get_excel_data_for_ai(excel_path):
    """Excel'deki TÜM verileri al - OPTİMİZE"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        target_sheets = ["Sinyaller", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
        
        for sheet_name in target_sheets:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = []
                
                # Başlıkları al (satır 1)
                headers = []
                col = 1
                while True:
                    cell_value = ws.cell(row=1, column=col).value
                    if cell_value:
                        headers.append(str(cell_value).strip())
                        col += 1
                    else:
                        break
                
                # Verileri al (satır 2-100)
                for row in ws.iter_rows(min_row=2, max_row=100, values_only=True):
                    if row and row[0]:
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
    """Soru içinden hisse kodunu bul"""
    words = re.findall(r'\b[A-Z0-9]{3,8}\b', question.upper())
    
    # BIST hisseleri
    hisse_list = [
        "A1CAP", "ACSEL", "ADEL", "ADESE", "AGHOL", "AKBNK", "AKCNS", "AKFGY",
        "AKSA", "AKSEN", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ANSGR",
        "ARCLK", "ARDYZ", "ASELS", "ASTOR", "AYGAZ", "BAGFS", "BAKAB", "BANVT",
        "BERA", "BFREN", "BIENY", "BIMAS", "BINHO", "BIOEN", "BRISA", "BRSAN",
        "BRYAT", "BTCIM", "BUCIM", "CANTE", "CCOLA", "CEMTS", "CLEBI", "CRDFA",
        "CWENE", "DAPGM", "DARDL", "DESA", "DOAS", "DOHOL", "DOKTA", "DURDO",
        "DYOBY", "ECILC", "ECZYT", "EGEEN", "EGGUB", "EKGYO", "EMNIS", "ENJSA",
        "ENKAI", "ERBOS", "EREGL", "EUPWR", "EUR", "EVCEN", "FADE", "FENER",
        "FROTO", "GARAN", "GESAN", "GIRIS", "GOODY", "GSDHO", "GSRAY", "GUBRF",
        "HALKB", "HATEK", "HEKTS", "HLGYO", "HURGZ", "ICBCT", "IHLAS", "IKTAS",
        "IPEKE", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "ISSEN", "IZENR", "IZMDC",
        "KRDMD", "KARSN", "KARTN", "KAYSE", "KCHOL", "KLSER", "KONKA", "KONTR",
        "KORDS", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRVGD", "KSKTC",
        "KYBKY", "LOGO", "MAVI", "MEGAP", "MGROS", "MIATK", "MPARK", "MSGYO",
        "MTRKS", "NATEN", "NETAS", "NTHOL", "ODAS", "ORGE", "OTKAR", "OYAKC",
        "OZSUB", "PAGS", "PAPIL", "PARSN", "PENTA", "PETKM", "PGSUS", "PKENT",
        "PSDMC", "QUAGR", "RGYAS", "SAHOL", "SASA", "SDTTR", "SELEC", "SISE",
        "SKBNK", "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN",
        "TKNSA", "TLMAN", "TMSN", "TOASO", "TRCAS", "TSKB", "TTKOM", "TTRAK",
        "TUKAS", "TUPRS", "TURSG", "ULKER", "ULUSE", "VAKBN", "VESTL", "VKGYO",
        "YALTI", "YATAS", "YBTAS", "YEOTK", "YKBNK", "YYLGD", "ZOREN"
    ]
    
    # ENDEKSLER
    endeks_list = ["XU100", "XU030", "XBANK", "XUSIN", "XHOLD", "XTEKS", "XINSA", "XGMYO", "XGIDA"]
    
    # FON/EMTIA/DOVIZ
    diger_list = ["GMSTR", "ALTIN", "XAUUSD", "XAGUSD", "BRENT", "USDTRY", "EURTRY"]
    
    for word in words:
        if word in hisse_list or word in endeks_list or word in diger_list:
            return word
    
    return words[0] if words else None

def create_expert_analysis_prompt(question, excel_data, hisse_adi=None):
    """PROFESYONEL ANALİZ UZMANI - TÜM GÖSTERGELERİ YORUMLAR"""
    
    timestamp = excel_data["timestamp"]
    data = excel_data["data"]
    
    # HİSSE ANALİZİ
    if hisse_adi:
        hisse_info = None
        sheet_name = None
        
        for sname, sinfo in data.items():
            for hisse in sinfo["data"]:
                hisse_name = hisse.get(sinfo["headers"][0], "")
                if hisse_name and hisse_adi.upper() in str(hisse_name).upper():
                    hisse_info = hisse
                    sheet_name = sname
                    headers = sinfo["headers"]
                    break
            if hisse_info:
                break
        
        if hisse_info:
            # TÜM TEKNİK GÖSTERGELERİ ÇIKAR
            close = hisse_info.get("Close", "?")
            pivot = hisse_info.get("Pivot", "?")
            wt_sinyal = hisse_info.get("WT Sinyal", "?")
            vma = hisse_info.get("VMA trend algo", "?")
            lsma = hisse_info.get("LSMA KAMA", "?")
            hma89 = hisse_info.get("HMA_89", "?")
            
            # DESTEK/DİRENÇ
            s3 = hisse_info.get("S3", "?")
            s2 = hisse_info.get("S2", "?")
            s1 = hisse_info.get("S1", "?")
            r1 = hisse_info.get("R1", "?")
            r2 = hisse_info.get("R2", "?")
            r3 = hisse_info.get("R3", "?")
            
            # EMA'lar
            ema8 = hisse_info.get("EMA_8", "?")
            ema13 = hisse_info.get("EMA_13", "?")
            ema21 = hisse_info.get("EMA_21", "?")
            ema34 = hisse_info.get("EMA_34", "?")
            ema55 = hisse_info.get("EMA_55", "?")
            ema89 = hisse_info.get("EMA_89", "?")
            ema144 = hisse_info.get("EMA_144", "?")
            ema233 = hisse_info.get("EMA_233", "?")
            
            # REGRESSION
            p55 = hisse_info.get("Pearson55", "?")
            p89 = hisse_info.get("Pearson89", "?")
            p144 = hisse_info.get("Pearson144", "?")
            p233 = hisse_info.get("Pearson233", "?")
            
            kanal55_ust = hisse_info.get("55Kanal_UST", "?")
            kanal55_alt = hisse_info.get("55Kanal_ALT", "?")
            
            # BOLLINGER
            bb_upper = hisse_info.get("BB_UPPER", "?")
            bb_middle = hisse_info.get("BB_MIDDLE", "?")
            bb_lower = hisse_info.get("BB_LOWER", "?")
            
            # HACİM
            hacim = hisse_info.get("Hacim", "?")
            hacim_degisim = hisse_info.get("Hacim_Değişim_%", "?")
            hacim_senaryo = hisse_info.get("Hacim_Senaryo", "?")
            
            # SMI
            smi = hisse_info.get("SMI", "?")
            smi_ema = hisse_info.get("SMI_EMA", "?")
            
            # AI_YORUM (Excel'deki hazır yorum)
            ai_yorum = hisse_info.get("AI_YORUM", "")
            
            # PROFESYONEL ANALİZ PROMPT'U
            prompt = f"""🎯 **SEN: BORSAANALİZ BAŞTEKNİK ANALİZ UZMANI**
📊 **25+ YIL DENEYİM - PROFESYONEL PİYASA ANALİSTİ**

═══════════════════════════════════════════
📋 **ANALİZ RAPORU: {hisse_adi}**
📅 **Tarih:** {timestamp}
📌 **Kaynak:** {sheet_name}
═══════════════════════════════════════════

## 📈 **1. GENEL GÖRÜNÜM**

**Fiyat:** {close} TL
**Pivot Seviyesi:** {pivot} TL
**WT Sinyal:** {wt_sinyal}
**LSMA Trend:** {lsma}
**VMA (Volume Moving Algorithm):** {vma}
**HMA_89:** {hma89}

**Excel AI Yorumu:** {ai_yorum}

═══════════════════════════════════════════

## 🎯 **2. DESTEK VE DİRENÇ SEVİYELERİ**

**🔻 DESTEKLER:**
• S3 (Güçlü Destek): {s3}
• S2: {s2}  
• S1: {s1}

**🔺 DİRENÇLER:**
• R1: {r1}
• R2: {r2}
• R3 (Güçlü Direnç): {r3}

**📊 PİVOT ANALİZİ:**
"""

            # Pivot analizi
            try:
                close_f = float(str(close).replace(',', '.'))
                pivot_f = float(str(pivot).replace(',', '.'))
                if close_f > pivot_f:
                    prompt += f"✅ Fiyat pivotun **ÜSTÜNDE** (+%{((close_f-pivot_f)/pivot_f*100):.2f}) - POZİTİF\n"
                else:
                    prompt += f"⚠️ Fiyat pivotun **ALTINDA** (-%{((pivot_f-close_f)/pivot_f*100):.2f}) - NEGATİF\n"
            except:
                prompt += "ℹ️ Pivot karşılaştırması yapılamadı\n"

            prompt += f"""
═══════════════════════════════════════════

## 📊 **3. HAREKETLİ ORTALAMALAR (EMA) ANALİZİ**

**KISA VADELİ:**
• EMA 8: {ema8}
• EMA 13: {ema13}
• EMA 21: {ema21}

**ORTA VADELİ:**
• EMA 34: {ema34}
• EMA 55: {ema55}
• EMA 89: {ema89}

**UZUN VADELİ:**
• EMA 144: {ema144}
• EMA 233: {ema233}

**EMA YORUMU:**
"""

            # EMA analizi
            try:
                close_f = float(str(close).replace(',', '.'))
                ema8_f = float(str(ema8).replace(',', '.')) if ema8 != '?' else 0
                ema21_f = float(str(ema21).replace(',', '.')) if ema21 != '?' else 0
                
                if close_f > ema8_f:
                    prompt += "✅ **EMA 8:** Fiyat üzerinde = Kısa vadeli trend POZİTİF\n"
                else:
                    prompt += "⚠️ **EMA 8:** Fiyat altında = Kısa vadeli trend NEGATİF\n"
                    
                if close_f > ema21_f:
                    prompt += "✅ **EMA 21:** Fiyat üzerinde = Orta vadeli trend POZİTİF\n"
                else:
                    prompt += "⚠️ **EMA 21:** Fiyat altında = Orta vadeli trend NEGATİF\n"
            except:
                pass

            prompt += f"""
═══════════════════════════════════════════

## 📉 **4. REGRESYON KANAL ANALİZİ**

**55 GÜNLÜK:**
• Pearson55: {p55}
• Kanal Üst: {kanal55_ust}
• Kanal Alt: {kanal55_alt}
"""

            # Pearson yorumu
            try:
                p55_f = float(str(p55).replace(',', '.')) if p55 != '?' else 0
                if p55_f > 0.3:
                    prompt += f"✅ **55 GÜN TREND:** YÜKSELİŞ (Pearson: {p55_f:.3f})\n"
                elif p55_f < -0.3:
                    prompt += f"⚠️ **55 GÜN TREND:** DÜŞÜŞ (Pearson: {p55_f:.3f})\n"
                else:
                    prompt += f"ℹ️ **55 GÜN TREND:** YATAY/BELİRSİZ (Pearson: {p55_f:.3f})\n"
            except:
                pass

            prompt += f"""
**89 GÜNLÜK:**
• Pearson89: {p89}

**144 GÜNLÜK:**
• Pearson144: {p144}

**233 GÜNLÜK:**
• Pearson233: {p233}

═══════════════════════════════════════════

## 📊 **5. BOLLINGER BANTLARI (BB)**

• Üst Bant: {bb_upper}
• Orta Bant: {bb_middle}
• Alt Bant: {bb_lower}
"""

            # Bollinger yorumu
            try:
                close_f = float(str(close).replace(',', '.'))
                bb_upper_f = float(str(bb_upper).replace(',', '.')) if bb_upper != '?' else 0
                bb_lower_f = float(str(bb_lower).replace(',', '.')) if bb_lower != '?' else 0
                
                if close_f > bb_upper_f:
                    prompt += "⚠️ **BOLLINGER:** Fiyat ÜST bandın üzerinde = AŞIRI ALIM bölgesi\n"
                elif close_f < bb_lower_f:
                    prompt += "✅ **BOLLINGER:** Fiyat ALT bandın altında = AŞIRI SATIM bölgesi (potansiyel tepki)\n"
                else:
                    prompt += "ℹ️ **BOLLINGER:** Fiyat bantlar içinde = NORMAL bölge\n"
            except:
                pass

            prompt += f"""
═══════════════════════════════════════════

## 💰 **6. HACİM ANALİZİ**

• **Hacim:** {hacim}
• **Hacim Değişim:** {hacim_degisim}
• **Hacim Senaryo:** {hacim_senaryo}

**HACİM YORUMU:**
"""

            if "POZITIF_YUKSELME" in str(hacim_senaryo):
                prompt += "✅ **POZİTİF:** Hacim artışıyla yükseliş - GÜÇLÜ SİNYAL\n"
            elif "NEGATIF_DUSUS" in str(hacim_senaryo):
                prompt += "⚠️ **NEGATİF:** Hacim düşüşü - ZAYIFLAMA\n"

            prompt += f"""
═══════════════════════════════════════════

## 📊 **7. SMI (Stokastik Momentum Index)**

• **SMI:** {smi}
• **SMI EMA:** {smi_ema}

═══════════════════════════════════════════

## 🎯 **8. VMA (VOLUME MOVING ALGORITHM)**

• **VMA Sinyal:** {vma}
• **Doğruluk Oranı:** %94

**VMA YORUMU:**
"""

            if "POZİTİF" in str(vma):
                prompt += "✅ **VMA POZİTİF:** Hacim trendi yükselişi onaylıyor - GÜVENİLİR SİNYAL\n"
            elif "NEGATİF" in str(vma):
                prompt += "⚠️ **VMA NEGATİF:** Hacim trendi düşüşü işaret ediyor\n"

            prompt += f"""
═══════════════════════════════════════════

## 📋 **9. TEKNİK ANALİZ SONUÇ ve ÖZET**

**Soru:** {question}

**{hisse_adi} İÇİN PROFESYONEL DEĞERLENDİRME:**

Lütfen yukarıdaki TÜM teknik göstergeleri kullanarak:

1️⃣ **KISA VADELİ GÖRÜNÜM** (1-5 gün)
2️⃣ **ORTA VADELİ GÖRÜNÜM** (1-4 hafta)
3️⃣ **DESTEK/DİRENÇ SEVİYELERİ** (Kritik seviyeler)
4️⃣ **TREND ANALİZİ** (Yükseliş/Düşüş/Yatay)
5️⃣ **HACİM ONAYI** (Güvenilirlik)
6️⃣ **RİSK SEVİYESİ** (Düşük/Orta/Yüksek)
7️⃣ **YATIRIMCI NOTU** (İzlenecek seviyeler)

**⚠️ ÖNEMLİ UYARI:** Bu analiz teknik göstergelere dayanmaktadır. Yatırım tavsiyesi değildir.
"""
            return prompt

    # GENEL PİYASA ANALİZİ (hisse adı yoksa)
    prompt = f"""🎯 **SEN: BORSAANALİZ BAŞTEKNİK ANALİZ UZMANI**
📊 **25+ YIL DENEYİM - PROFESYONEL PİYASA ANALİSTİ**

═══════════════════════════════════════════
📋 **PİYASA GENEL ANALİZ RAPORU**
📅 **Tarih:** {timestamp}
═══════════════════════════════════════════

## 📈 **ELİMDEKİ VERİLER:**

"""
    for sheet_name, sheet_info in data.items():
        prompt += f"""
### 📊 {sheet_name} SAYFASI
• **Hisse/Endeks Sayısı:** {sheet_info['count']}
• **Teknik Göstergeler:** WT, Pivot, LSMA, VMA, HMA, EMA(8,13,21,34,55,89,144,233)
• **Regresyon:** Pearson55/89/144/233
• **Bollinger:** BB_UPPER/MIDDLE/LOWER
• **Hacim:** Hacim, Hacim_Değişim_%, Hacim_Senaryo
"""

    prompt += f"""
═══════════════════════════════════════════

**Soru:** {question}

**PROFESYONEL ANALİZ TALİMATI:**

Yukarıdaki Excel verilerine dayanarak:

1️⃣ Piyasanın genel teknik durumunu değerlendir
2️⃣ En güçlü/En zayıf sektörleri belirt
3️⃣ Dikkat çeken hisseleri analiz et
4️⃣ Kısa/Orta vadeli beklentini paylaş

**⚠️ UYARI:** Bu analiz yatırım tavsiyesi değildir.
"""
    return prompt

def call_deepseek(prompt, question):
    """DeepSeek AI çağrısı"""
    if not DEEPSEEK_API_KEY:
        return None
    
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"⚠️ DeepSeek hata {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"⚠️ DeepSeek bağlantı hatası: {str(e)}")
        return None

def call_groq(prompt, question):
    """Groq AI çağrısı (LLaMA 3.3)"""
    if not GROQ_API_KEY:
        return None
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            },
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"⚠️ Groq hata {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ Groq bağlantı hatası: {str(e)}")
        return None

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("❌ Hata: Soru girmediniz")
        print("Örnek: python excel_ai_analyzer.py 'THYAO analiz'")
        return
    
    question = sys.argv[1]
    print(f"❓ SORU: {question}")
    print("🔍 Excel dosyası aranıyor...")
    
    # Excel'i bul
    excel_info = find_latest_excel()
    if not excel_info:
        print("❌ Excel dosyası bulunamadı!")
        return
    
    print(f"📁 Excel: {excel_info['name']}")
    
    # Excel verilerini oku
    excel_data = get_excel_data_for_ai(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"❌ {excel_data['error']}"
    else:
        # Hisse adını çıkar
        hisse_adi = extract_hisse_adi(question)
        print(f"🎯 Hissenin adı: {hisse_adi}")
        
        # Profesyonel prompt oluştur
        prompt = create_expert_analysis_prompt(question, excel_data, hisse_adi)
        
        # ÖNCE DEEPSEEK DENE
        print("🚀 DeepSeek AI deneniyor...")
        answer = call_deepseek(prompt, question)
        
        # DeepSeek çalışmazsa GROQ dene
        if not answer:
            print("⚡ DeepSeek çalışmadı, Groq deneniyor...")
            answer = call_groq(prompt, question)
        
        # İkisi de çalışmazsa
        if not answer:
            answer = """⚠️ **AI SERVİSLERİNE ULAŞILAMADI**

**Olası Nedenler:**
1. DeepSeek API anahtarı geçersiz veya bakiye yetersiz
2. Groq API anahtarı geçersiz
3. İnternet bağlantısı sorunu

**Excel'den Alınan Veriler:**
"""
            # Excel'den özet bilgi ekle
            if hisse_adi:
                for sheet_name, sheet_info in excel_data["data"].items():
                    for hisse in sheet_info["data"]:
                        hisse_name = hisse.get(sheet_info["headers"][0], "")
                        if hisse_name and hisse_adi.upper() in str(hisse_name).upper():
                            close = hisse.get("Close", "?")
                            wt = hisse.get("WT Sinyal", "?")
                            vma = hisse.get("VMA trend algo", "?")
                            answer += f"""
**{hisse_adi} Teknik Veriler:**
• Fiyat: {close} TL
• WT Sinyal: {wt}
• VMA: {vma}
"""
                            break
    
    # Yanıtı kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("\n✅ ANALİZ TAMAMLANDI!")
    print(f"📝 Yanıt kaydedildi: ai_response.txt")
    print(f"📏 Yanıt uzunluğu: {len(answer)} karakter")

if __name__ == "__main__":
    main()
