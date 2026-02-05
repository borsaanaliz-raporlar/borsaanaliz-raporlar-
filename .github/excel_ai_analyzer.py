#!/usr/bin/env python3
"""
MÜKEMMEL EXCEL ANALİST - TÜM VERİLERLE DETAYLI ANALİZ
"""
import os
import sys
import json
import re
from openpyxl import load_workbook
import requests
from datetime import datetime
from excel_finder import find_latest_excel

# AYARLAR
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

def get_excel_data_for_ai(excel_path):
    """AI için Excel verilerini hazırla - DETAYLI"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        target_sheets = ["Sinyaller", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
        
        for sheet_name in target_sheets:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = []
                
                # TÜM başlıkları al
                headers = []
                for col in range(1, 150):  # Daha fazla kolon
                    cell_value = ws.cell(row=1, column=col).value
                    if cell_value:
                        headers.append(f"{cell_value}")
                    else:
                        break
                
                # TÜM hisseleri al (daha fazla)
                for row in ws.iter_rows(min_row=2, max_row=300, values_only=True):
                    if row and row[0]:
                        row_dict = {}
                        for i, cell_value in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = cell_value
                        sheet_data.append(row_dict)
                
                all_data[sheet_name] = {
                    "headers": headers,
                    "data": sheet_data,
                    "row_count": len(sheet_data)
                }
                print(f"📊 {sheet_name}: {len(sheet_data)} hisse, {len(headers)} kolon")
        
        wb.close()
        
        return {
            "data": all_data,
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        
    except Exception as e:
        return {"error": f"Excel okuma hatası: {str(e)}"}

def extract_hisse_adi(question):
    """Soru içinden hisse adını çıkar"""
    # Büyük harf ve 3-6 karakterli kelimeleri bul
    words = re.findall(r'\b[A-Z]{3,6}\b', question.upper())
    
    # Hisse olma ihtimali yüksek kelimeler
    hisse_keywords = ["FROTO", "THYAO", "ASELS", "EREGL", "SASA", "KCHOL", 
                     "TOASO", "TUPRS", "AKBNK", "GARAN", "YKBNK", "XU100",
                     "GMSTR", "ALTIN", "XAUUSD", "XAGUSD", "XINSA", "XHOLD",
                     "XTEKS", "A1CAP", "ACSEL", "ADEL", "XU030"]
    
    for word in words:
        if word in hisse_keywords:
            return word
    
    # Eğer bulamazsa, ilk büyük harfli kelimeyi dene
    if words:
        return words[0]
    
    return None

def get_hisse_analysis_data(hisse_info):
    """Hissenin analiz için gerekli TÜM verilerini çıkar"""
    hisse_data = hisse_info["hisse"]
    headers = hisse_info["headers"]
    
    analysis_data = {
        "TEMEL": {},
        "PİVOT_DESTEK_DİRENÇ": {},
        "HACİM": {},
        "EMA": {},
        "REGRESSION": {},
        "BOLLINGER": {},
        "DİĞER": {}
    }
    
    # TÜM verileri kategorilere ayır
    for header in headers:
        if header in hisse_data:
            value = hisse_data[header]
            if value is None:
                continue
            
            header_upper = header.upper()
            
            # 1. TEMEL VERİLER
            if any(keyword in header_upper for keyword in ["HİSSE", "SEMBOL", "CLOSE", "OPEN", "HIGH", "LOW"]):
                analysis_data["TEMEL"][header] = value
            
            # 2. PİVOT ve DESTEK/DİRENÇ
            elif any(keyword in header_upper for keyword in ["PİVOT", "S1", "S2", "S3", "R1", "R2", "R3"]):
                analysis_data["PİVOT_DESTEK_DİRENÇ"][header] = value
            
            # 3. HACİM VERİLERİ
            elif any(keyword in header_upper for keyword in ["HACİM", "VOLUME"]):
                analysis_data["HACİM"][header] = value
            
            # 4. EMA'lar
            elif "EMA_" in header_upper:
                analysis_data["EMA"][header] = value
            
            # 5. REGRESSION
            elif any(keyword in header_upper for keyword in ["PEARSON", "KANAL", "UZAKLIK"]):
                analysis_data["REGRESSION"][header] = value
            
            # 6. BOLLINGER BANDS
            elif header_upper.startswith("BB_"):
                analysis_data["BOLLINGER"][header] = value
            
            # 7. DİĞER TEKNİK GÖSTERGELER
            elif any(keyword in header_upper for keyword in ["VMA", "LSMA", "WT", "HMA", "SMI", "DURUM", "SİNYAL"]):
                analysis_data["DİĞER"][header] = value
    
    return analysis_data

def create_detailed_hisse_prompt(question, hisse_info, analysis_data):
    """DETAYLI hisse analizi için prompt"""
    
    hisse_name = hisse_info["hisse"].get(hisse_info["headers"][0], "HISSE")
    sheet_name = hisse_info["sheet"]
    
    prompt = f"""🎯 **SEN: BORSAANALIZ PROFESYONEL TEKNİK ANALİST**

📊 **{hisse_name} DETAYLI TEKNİK ANALİZ RAPORU**

**Veri Kaynağı:** {sheet_name} sayfası
**Soru:** {question}

---

## 📈 **1. TEMEL VERİLER:**
"""
    
    # TEMEL veriler
    for key, value in analysis_data["TEMEL"].items():
        prompt += f"- **{key}:** {value}\n"
    
    prompt += f"""
## 📊 **2. PİVOT ve DESTEK/DİRENÇ ANALİZİ:**
"""
    
    # PİVOT ve destek/direnç
    for key, value in analysis_data["PİVOT_DESTEK_DİRENÇ"].items():
        prompt += f"- **{key}:** {value}\n"
    
    # Pivot analizi yap
    close = analysis_data["TEMEL"].get("Close")
    pivot = analysis_data["PİVOT_DESTEK_DİRENÇ"].get("Pivot")
    if close and pivot:
        try:
            close_f = float(str(close).replace(',', '.'))
            pivot_f = float(str(pivot).replace(',', '.'))
            if close_f > pivot_f:
                prompt += f"- **PIVOT ANALİZİ:** Fiyat pivotun ÜSTÜNDE (+%{((close_f-pivot_f)/pivot_f)*100:.2f})\n"
            else:
                prompt += f"- **PIVOT ANALİZİ:** Fiyat pivotun ALTINDA (-%{((pivot_f-close_f)/pivot_f)*100:.2f})\n"
        except:
            pass
    
    prompt += f"""
## 📊 **3. HACİM ANALİZİ:**
"""
    
    # HACİM analizi
    for key, value in analysis_data["HACİM"].items():
        prompt += f"- **{key}:** {value}\n"
    
    prompt += f"""
## 📊 **4. EMA (Exponential Moving Average) ANALİZİ:**
"""
    
    # EMA analizi
    ema_items = sorted(analysis_data["EMA"].items())
    for key, value in ema_items:
        prompt += f"- **{key}:** {value}\n"
    
    # EMA yorumu
    close = analysis_data["TEMEL"].get("Close")
    if close and analysis_data["EMA"]:
        try:
            close_f = float(str(close).replace(',', '.'))
            for ema_key, ema_value in analysis_data["EMA"].items():
                try:
                    ema_f = float(str(ema_value).replace(',', '.'))
                    if "EMA_8" in ema_key and close_f > ema_f:
                        prompt += f"- **EMA_8 YORUM:** Fiyat EMA_8'in ÜSTÜNDE (Kısa vadeli trend POZİTİF)\n"
                        break
                except:
                    pass
        except:
            pass
    
    prompt += f"""
## 📊 **5. REGRESSION KANAL ANALİZİ:**
"""
    
    # REGRESSION analizi
    for key, value in analysis_data["REGRESSION"].items():
        prompt += f"- **{key}:** {value}\n"
    
    # Pearson katsayısı analizi
    pearson55 = analysis_data["REGRESSION"].get("Pearson55")
    pearson144 = analysis_data["REGRESSION"].get("Pearson144")
    pearson233 = analysis_data["REGRESSION"].get("Pearson233")
    
    if pearson55:
        try:
            p55 = float(str(pearson55).replace(',', '.'))
            if p55 > 0.3:
                prompt += f"- **55 GÜN REGRESSION:** Pearson={p55:.3f} > 0.3 = YÜKSELİŞ TRENDİ\n"
            elif p55 < -0.3:
                prompt += f"- **55 GÜN REGRESSION:** Pearson={p55:.3f} < -0.3 = DÜŞÜŞ TRENDİ\n"
            else:
                prompt += f"- **55 GÜN REGRESSION:** Pearson={p55:.3f} = NÖTR/RANGE\n"
        except:
            pass
    
    prompt += f"""
## 📊 **6. BOLLINGER BANDS ANALİZİ:**
"""
    
    # BOLLINGER analizi
    for key, value in analysis_data["BOLLINGER"].items():
        prompt += f"- **{key}:** {value}\n"
    
    # Bollinger yorumu
    bb_upper = analysis_data["BOLLINGER"].get("BB_UPPER")
    bb_middle = analysis_data["BOLLINGER"].get("BB_MIDDLE")
    bb_lower = analysis_data["BOLLINGER"].get("BB_LOWER")
    close = analysis_data["TEMEL"].get("Close")
    
    if all([bb_upper, bb_middle, bb_lower, close]):
        try:
            close_f = float(str(close).replace(',', '.'))
            upper_f = float(str(bb_upper).replace(',', '.'))
            lower_f = float(str(bb_lower).replace(',', '.'))
            
            if close_f > upper_f:
                prompt += f"- **BOLLINGER YORUM:** Fiyat üst bandın ÜSTÜNDE = AŞIRI ALIM\n"
            elif close_f < lower_f:
                prompt += f"- **BOLLINGER YORUM:** Fiyat alt bandın ALTINDA = AŞIRI SATIM\n"
            else:
                prompt += f"- **BOLLINGER YORUM:** Fiyat bantlar İÇİNDE = NORMAL\n"
        except:
            pass
    
    prompt += f"""
## 📊 **7. DİĞER TEKNİK GÖSTERGELER:**
"""
    
    # DİĞER göstergeler
    for key, value in analysis_data["DİĞER"].items():
        prompt += f"- **{key}:** {value}\n"
    
    # VMA analizi
    vma_value = None
    for key, value in analysis_data["DİĞER"].items():
        if "VMA" in key.upper():
            vma_value = str(value)
            break
    
    if vma_value:
        if "POZİTİF" in vma_value.upper():
            prompt += f"- **VMA YORUM:** {vma_value} = Hacim trendi YÜKSELİŞ (%94 doğruluk)\n"
        elif "NEGATİF" in vma_value.upper():
            prompt += f"- **VMA YORUM:** {vma_value} = Hacim trendi DÜŞÜŞ (%94 doğruluk)\n"
    
    prompt += f"""

---

## 📋 **TEKNİK ANALİZ TALİMATLARI:**

**MUTLAKA YAP:**
1. Yukarıdaki TÜM verilere göre detaylı analiz yap
2. Her bölümü tek tek değerlendir
3. Sayısal verileri YORUMLA
4. Trendleri belirle
5. Risk seviyesini değerlendir

**YAPMA:**
1. ASLA "Volkswagen" deme (VMA = Volume Moving Algorithm)
2. RSI/MACD'den bahsetme (yok!)
3. Yatırım tavsiyesi verme

**ANALİZ BAŞLIKLARI:**
1. Genel Teknik Durum Özeti
2. Pivot ve Destek/Direnç Analizi
3. Hacim Analizi
4. EMA Trend Analizi
5. Regression Kanal Analizi
6. Bollinger Bands Analizi
7. VMA ve Diğer Göstergeler
8. Risk Değerlendirmesi

---

**ŞİMDİ {hisse_name} İÇİN DETAYLI TEKNİK ANALİZ YAP:**
"""
    
    return prompt

def create_general_prompt(question, excel_data):
    """Genel analiz için prompt"""
    
    data = excel_data["data"]
    timestamp = excel_data["timestamp"]
    
    prompt = f"""🎯 **SEN: BORSAANALIZ PROFESYONEL TEKNİK ANALİST**

📊 **PİYASA ANALİZ RAPORU**
**Tarih:** {timestamp}
**Soru:** {question}

---

## 📈 **ELİMDEKİ VERİLER:**

"""

    for sheet_name, sheet_info in data.items():
        headers = sheet_info["headers"]
        hisse_sayisi = len(sheet_info["data"])
        
        prompt += f"""
### {sheet_name.upper()} SAYFASI:
• **Hisse Sayısı:** {hisse_sayisi}
• **Kolon Sayısı:** {len(headers)}
• **Önemli Göstergeler:**"""
        
        important_indicators = []
        for header in headers:
            if any(keyword in header.upper() for keyword in 
                   ["VMA", "LSMA", "WT", "EMA", "PEARSON", "KANAL", 
                    "PIVOT", "HACİM", "BB_", "HMA", "SMI"]):
                important_indicators.append(header)
        
        prompt += f" {', '.join(important_indicators[:10])}"
        if len(important_indicators) > 10:
            prompt += f" ..."
        
        # İlk 5 hisse
        prompt += f"\n• **İlk 5 Hisse:** "
        hisse_list = []
        for hisse in sheet_info["data"][:5]:
            hisse_name = hisse.get(headers[0], "")
            if hisse_name:
                hisse_list.append(hisse_name)
        prompt += f"{', '.join(hisse_list)}"
    
    prompt += f"""

---

## 📋 **ANALİZ TALİMATLARI:**

**SADECE yukarıdaki verileri kullanarak:**
1. {question} sorusunu cevapla
2. Hisse isimlerini GERÇEK yaz
3. Teknik göstergeleri doğru kullan
4. Regression sorulursa: Pearson55, Pearson144, Pearson233 kontrol et
5. VMA = Volume Moving Algorithm (%94 doğruluk)

**YAPMA:**
1. RSI/MACD deme (yok!)
2. Yatırım tavsiyesi verme

---

**CEVAP FORMATI:**
1. 📊 Analiz Özeti
2. 📈 Teknik Bulgular
3. 🔍 Detaylı Analiz
4. ⚠️ Risk Uyarısı

---

**ŞİMDİ ANALİZ YAP:**
"""
    
    return prompt

def call_ai_analyst(prompt):
    """AI çağır"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY eksik"
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Lütfen detaylı teknik analiz yap."}
        ],
        "max_tokens": 2500,  # Daha fazla token (detaylı analiz)
        "temperature": 0.1,
        "top_p": 0.9,
        "stream": False
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # Kontroller
            answer_lower = answer.lower()
            
            if "volkswagen" in answer_lower:
                answer = answer.replace("Volkswagen", "Volume Moving Algorithm")
            
            if "rsi" in answer_lower or "macd" in answer_lower:
                answer += "\n\n⚠️ **NOT:** Excel'de RSI ve MACD göstergeleri bulunmamaktadır."
            
            if "yatırım tavsiyesi değildir" not in answer_lower:
                answer += "\n\n⚠️ **ÖNEMLİ UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir. Yatırım kararlarınızı kendi araştırmanızla alınız."
            
            return answer
        else:
            return f"❌ API hatası: {response.status_code}"
            
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("❌ Kullanım: python excel_ai_analyzer.py 'SORUNUZ'")
        return
    
    question = sys.argv[1]
    print(f"❓ Soru: {question}")
    
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        return "⚠️ Excel dosyası bulunamadı"
    
    print(f"📖 Excel: {excel_info['name']}")
    
    # Excel verilerini al
    excel_data = get_excel_data_for_ai(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"❌ {excel_data['error']}"
    else:
        # Hisse analizi mi?
        hisse_adi = extract_hisse_adi(question)
        
        if hisse_adi:
            print(f"🎯 Hisse analizi: {hisse_adi}")
            
            # Hisseyi bul
            hisse_info = None
            for sheet_name, sheet_info in excel_data["data"].items():
                headers = sheet_info["headers"]
                for hisse in sheet_info["data"]:
                    hisse_name = hisse.get(headers[0], "")
                    if hisse_name and hisse_adi in str(hisse_name).upper():
                        hisse_info = {
                            "hisse": hisse,
                            "headers": headers,
                            "sheet": sheet_name
                        }
                        break
                if hisse_info:
                    break
            
            if hisse_info:
                # DETAYLI analiz verilerini hazırla
                analysis_data = get_hisse_analysis_data(hisse_info)
                
                # DETAYLI prompt oluştur
                prompt = create_detailed_hisse_prompt(question, hisse_info, analysis_data)
                answer = call_ai_analyst(prompt)
            else:
                answer = f"❌ {hisse_adi} hissesi Excel'de bulunamadı"
        else:
            # Genel analiz
            prompt = create_general_prompt(question, excel_data)
            answer = call_ai_analyst(prompt)
    
    # Sonucu kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("\n" + "="*60)
    print("✅ ANALİZ TAMAMLANDI!")
    print("="*60)
    print(f"\n📊 AI YANITI:\n")
    print(answer[:800] + "..." if len(answer) > 800 else answer)
    print("\n" + "="*60)
    
    return answer

if __name__ == "__main__":
    main()
