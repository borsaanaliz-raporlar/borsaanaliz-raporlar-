#!/usr/bin/env python3
"""
AKILLI EXCEL ANALİST - TÜM VERİYİ AI'YA GÖNDER (BOLLINGER EKLİ)
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
    """AI için Excel verilerini hazırla"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        # Sadece ilgili sayfaları al
        target_sheets = ["Sinyaller", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
        
        for sheet_name in target_sheets:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = []
                
                # BAŞLIK SATIRINI AL
                headers = []
                for col in range(1, 100):  # İlk 100 kolon
                    cell_value = ws.cell(row=1, column=col).value
                    if cell_value:
                        headers.append(f"{cell_value}")
                    else:
                        break
                
                # İlk 30 hisse ve tüm kolonları al
                row_count = 0
                for row in ws.iter_rows(min_row=2, max_row=52, values_only=True):
                    if row and row[0]:
                        row_dict = {}
                        for i, cell_value in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = cell_value
                        
                        sheet_data.append(row_dict)
                        row_count += 1
                        if row_count >= 30:  # Maksimum 30 hisse
                            break
                
                all_data[sheet_name] = {
                    "headers": headers,
                    "data": sheet_data,
                    "row_count": row_count
                }
                print(f"📊 {sheet_name}: {row_count} hisse, {len(headers)} kolon")
        
        wb.close()
        
        # Excel yapısı hakkında bilgi
        excel_info = {
            "total_sheets": len(all_data),
            "sheets_analyzed": list(all_data.keys()),
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        return {
            "excel_info": excel_info,
            "data": all_data
        }
        
    except Exception as e:
        return {"error": f"Excel okuma hatası: {str(e)}"}

def create_smart_prompt(question, excel_data):
    """AI için akıllı prompt oluştur - BOLLINGER EKLİ"""
    
    if "error" in excel_data:
        return f"""❌ Excel verisi alınamadı: {excel_data['error']}"""
    
    excel_info = excel_data.get("excel_info", {})
    data = excel_data.get("data", {})
    
    # Prompt'u oluştur
    prompt = f"""🎯 **SEN: BORSAANALIZ PROFESYONEL TEKNİK ANALİST**

📊 **ELİMDEKİ EXCEL VERİLERİ:**

**Excel Yapısı:**
• Analiz edilen sayfalar: {', '.join(excel_info.get('sheets_analyzed', []))}
• Tarih: {excel_info.get('timestamp', 'Bilinmiyor')}

---

**DETAYLI VERİ YAPISI:**
"""

    # Her sayfa için detaylı bilgi
    for sheet_name, sheet_info in data.items():
        headers = sheet_info.get("headers", [])
        sample_count = len(sheet_info.get("data", []))
        
        prompt += f"""
**{sheet_name.upper()} SAYFASI:**
• Toplam kolon: {len(headers)}
• Analiz edilen hisse: {sample_count}
• **TÜM KOLON BAŞLIKLARI:** {', '.join(headers)}"""
        
        # Sayfadaki hisseleri listele
        prompt += f"\n• **SAYFADAKİ HİSSELER:**"
        hisse_list = []
        for hisse in sheet_info.get("data", []):
            hisse_name = hisse.get(headers[0] if headers else "Sembol", "Bilinmeyen")
            hisse_list.append(hisse_name)
        prompt += f" {', '.join(hisse_list[:10])}"
        if len(hisse_list) > 10:
            prompt += f" ... ve {len(hisse_list)-10} hisse daha"
    
    prompt += f"""

---

**TEKNİK TERİM AÇIKLAMALARI (EXCEL'DE OLANLAR):**

1. **VMA trend algo = Volume Moving Algorithm** (Hacim Ağırlıklı Trend Algoritması)
   - %94 doğruluk oranı
   - POZİTİF (X): X gündür yükseliş trendi
   - NEGATİF (X): X gündür düşüş trendi

2. **LSMA KAMA = Least Squares Moving Average** (En Küçük Kareler Hareketli Ortalama)
   - Trend yönünü gösterir

3. **WT Sinyal = Wave Trend Oscillator**
   - Aşırı alım/satım seviyelerini gösterir
   - -80 altı: Aşırı alım (Alış sinyali)
   - +80 üstü: Aşırı satım (Satış sinyali)

4. **BB_UPPER, BB_MIDDLE, BB_LOWER = Bollinger Bands**
   - Üst, orta ve alt bantlar
   - Fiyat üst bandın üstünde: Aşırı alım
   - Fiyat alt bandın altında: Aşırı satım
   - Bantlar daralıyorsa: Volatilite düşük
   - Bantlar genişliyorsa: Volatilite yüksek

5. **Pearson55 / Pearson144 / Pearson233 = Regression Katsayıları**
   - > 0.3: Yükseliş trendi
   - < -0.3: Düşüş trendi
   - -0.3 ile 0.3 arası: Nötr/Range

6. **55Kanal_UST / 55Kanal_ALT = 55 günlük regression kanalı üst/alt bandı**
7. **144Kanal_UST / 144Kanal_ALT = 144 günlük regression kanalı**
8. **233Kanal_UST / 233Kanal_ALT = 233 günlük regression kanalı**

9. **XX%_ALT_Uzaklik:** Fiyatın alt banda yakınlığı %
   - Yüksek değer = YAKIN, Düşük değer = UZAK
   - Örnek: 55%_ALT_Uzaklik: 15.5 = Fiyat 55 günlük alt bandına %15.5 yakın

10. **EMA_8, EMA_13, EMA_21, ... = Exponential Moving Average**
    - Kısa vadeli trend göstergeleri

11. **HMA_89 = Hull Moving Average (89 gün)**
    - Orta vadeli trend

12. **SMI ve SMI_EMA = Stochastic Momentum Index**
    - Momentum göstergesi

13. **Volume_Spike = Hacim Artışı**
    - Normal: Normal hacim
    - Hacim SPIKE (X.Xx): X kat hacim artışı

---

**⚠️ EXCEL'DE OLMAYAN TERİMLER (KULLANMA!):**
- RSI yok
- MACD yok  

---

**KULLANICI SORUSU:**
"{question}"

---

**📝 ANALİZ TALİMATLARIM:**

**YAPACAKLARIN:**
1. SADECE yukarıdaki Excel verilerini kullan
2. Regression sorulursa: Pearson55, Pearson144, Pearson233 kontrol et
3. Hisse isimlerini TAM OLARAK yaz (Sembol kolonundan)
4. Teknik terimleri DOĞRU kullan (VMA = Volume Moving Algorithm)
5. Bollinger Bands analizi yap (BB_UPPER, BB_MIDDLE, BB_LOWER)
6. Eğer hisse bulamazsan: "❌ [Hisse adı] bulunamadı" de

**YAPMAYACAKLARIN:**
1. ASLA "Volkswagen" deme! (VMA = Volume Moving Algorithm)
2. Uydurma veri kullanma
3. "Hisse1, Hisse2" gibi isimler yazma
4. Yatırım tavsiyesi verme
5. RSI, MACD gibi OLMAYAN göstergelerden bahsetme

**REGRESSION ANALİZİ İÇİN ÖZEL:**
1. Pearson55 > 0.3 = 55 günlük kanal YÜKSELİŞ
2. Pearson144 > 0.3 = 144 günlük kanal YÜKSELİŞ  
3. Pearson233 > 0.3 = 233 günlük kanal YÜKSELİŞ
4. XX%_ALT_Uzaklik yüksek = alt banda YAKIN

**BOLLINGER BANDS ANALİZİ:**
1. Fiyat > BB_UPPER = Aşırı alım (düzeltme beklenebilir)
2. Fiyat < BB_LOWER = Aşırı satım (toparlanma beklenebilir)
3. Fiyat BB_MIDDLE civarı = Nötr bölge

---

**CEVAP FORMATI:**
1. 📊 Analiz Özeti
2. 📈 Bulunan Hisseler (GERÇEK isimlerle)
3. 🔍 Teknik Detaylar (VMA, LSMA, WT, BB, Regression)
4. ⚠️ Risk Uyarısı

---

**ŞİMDİ YUKARIDAKİ EXCEL VERİLERİNE GÖRE SORUYU CEVAPLA:**
"""
    
    return prompt

def call_ai_with_full_data(question, excel_data):
    """Tüm Excel verisini AI'ya gönder"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY eksik"
    
    prompt = create_smart_prompt(question, excel_data)
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": prompt
            },
            {
                "role": "user", 
                "content": "Lütfen Excel verilerine dayanarak soruyu cevapla."
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
        "top_p": 0.9,
        "stream": False
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # Kontroller
            answer_lower = answer.lower()
            
            # Volkswagen kontrolü
            if "volkswagen" in answer_lower:
                answer = answer.replace("Volkswagen", "Volume Moving Algorithm")
                answer = answer.replace("volkswagen", "Volume Moving Algorithm")
            
            # RSI/MACD uyarısı (olmayan göstergeler)
            if "rsi" in answer_lower or "macd" in answer_lower:
                answer += "\n\n⚠️ **NOT:** Excel'de RSI ve MACD göstergeleri bulunmamaktadır."
            
            # Risk uyarısı
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
    
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        return "⚠️ Excel dosyası bulunamadı"
    
    print(f"📖 Excel: {excel_info['name']}")
    
    # TÜM Excel verisini AI için hazırla
    print("📊 Excel verileri AI için hazırlanıyor...")
    excel_data = get_excel_data_for_ai(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"❌ {excel_data['error']}"
    else:
        answer = call_ai_with_full_data(question, excel_data)
    
    # Sonucu kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("✅ Analiz tamamlandı!")
    print(f"\n{'='*50}\n📊 AI YANITI:\n{'='*50}")
    print(answer[:500] + "..." if len(answer) > 500 else answer)
    
    return answer

if __name__ == "__main__":
    main()
