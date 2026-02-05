#!/usr/bin/env python3
"""
AKILLI EXCEL ANALİST - TÜM VERİYİ AI'YA GÖNDER
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
    """AI için Excel verilerini hazırla - KOLON BAŞLIKLARIYLA BİRLİKTE"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        # Sadece ilgili sayfaları al
        target_sheets = ["Sinyaller", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
        
        for sheet_name in target_sheets:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = []
                
                # BAŞLIK SATIRINI AL (ÇOK ÖNEMLİ!)
                headers = []
                for col in range(1, 100):  # İlk 100 kolon
                    cell_value = ws.cell(row=1, column=col).value
                    if cell_value:
                        headers.append(f"{cell_value}")
                    else:
                        break
                
                # İlk 30 hisse ve tüm kolonları al
                row_count = 0
                for row in ws.iter_rows(min_row=2, max_row=32, values_only=True):
                    if row and row[0]:
                        row_dict = {}
                        for i, cell_value in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = cell_value
                        
                        sheet_data.append(row_dict)
                        row_count += 1
                
                all_data[sheet_name] = {
                    "headers": headers,
                    "data": sheet_data[:30],  # İlk 30 hisse
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
    """AI için akıllı prompt oluştur - TÜM VERİYİ VER"""
    
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
• ÖNEMLİ KOLON BAŞLIKLARI: {', '.join(headers[:15])}..."""
        
        if len(headers) > 15:
            prompt += f"\n• DİĞER KOLONLAR: {', '.join(headers[15:30])}..."
        
        # İlk 3 hissenin özeti
        prompt += "\n• **İLK 3 HİSSE ÖRNEĞİ:**"
        for i, hisse in enumerate(sheet_info.get("data", [])[:3]):
            hisse_name = hisse.get(headers[0] if headers else "Sembol", "Bilinmeyen")
            prompt += f"\n  {i+1}. {hisse_name}: "
            
            # Önemli alanları göster
            important_fields = []
            for field in ["WT Sinyal", "Close", "Pivot", "LSMA KAMA", "VMA trend algo"]:
                if field in hisse:
                    important_fields.append(f"{field}: {hisse[field]}")
            
            prompt += " | ".join(important_fields[:3])
    
    prompt += f"""

---

**TEKNİK TERİM AÇIKLAMALARI:**

1. **VMA trend algo = Volume Moving Algorithm** (Hacim Ağırlıklı Trend)
   - %94 doğruluk oranı
   - POZİTİF (X): X gündür yükseliş trendi
   - NEGATİF (X): X gündür düşüş trendi

2. **LSMA KAMA = Least Squares Moving Average ve Kaufman Adaptive Moving Average**
   - Trend yönünü gösterir

3. **Pearson55 / Pearson144 / Pearson233 = Regression Katsayıları**
   - > 0.3: Yükseliş trendi
   - < -0.3: Düşüş trendi
   - -0.3 ile 0.3 arası: Nötr/Range

4. **55Kanal_UST / 55Kanal_ALT = 55 günlük regression kanalı üst/alt bandı**
   - 55%_ALT_Uzaklik: Fiyatın alt banda yakınlığı (%)
   - Yüksek değer = Yakın, Düşük değer = Uzak

5. **144Kanal_UST / 144Kanal_ALT = 144 günlük regression kanalı**
6. **233Kanal_UST / 233Kanal_ALT = 233 günlük regression kanalı**

---

**KULLANICI SORUSU:**
"{question}"

---

**📝 ANALİZ TALİMATLARIM:**

**YAPACAKLARIN:**
1. Yukarıdaki Excel verilerini KULLAN
2. Regression kanal analizi sorulduysa: Pearson55, Pearson144, Pearson233'ü kontrol et
3. Hisse isimlerini GERÇEK olarak yaz (Sembol kolonundan)
4. Kolon başlıklarını referans al
5. Teknik terimleri DOĞRU kullan
6. VMA = Volume Moving Algorithm (ASLA Volkswagen deme!)

**YAPMAYACAKLARIN:**
1. Uydurma veri kullanma
2. "Hisse1, Hisse2" gibi isimler yazma
3. Yatırım tavsiyesi verme
4. Tahmin yapma

**CEVAP FORMATI:**
1. Özet Analiz
2. Bulunan Hisseler (GERÇEK isimlerle)
3. Teknik Detaylar
4. Risk Uyarısı

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
        "max_tokens": 2000,  # Daha fazla token (veri çok)
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
            timeout=90  # Daha uzun timeout
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # Kontroller
            answer_lower = answer.lower()
            
            # Volkswagen kontrolü
            if "volkswagen" in answer_lower:
                answer = answer.replace("Volkswagen", "Volume Moving Algorithm")
                answer = answer.replace("volkswagen", "Volume Moving Algorithm")
            
            # Risk uyarısı kontrolü
            if "yatırım tavsiyesi değildir" not in answer_lower:
                answer += "\n\n⚠️ **ÖNEMLİ UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir. Yatırım kararlarınızı kendi araştırmanızla alınız."
            
            return answer
        else:
            return f"❌ API hatası: {response.status_code}"
            
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"

def main():
    """Ana fonksiyon"""
    question = sys.argv[1] if len(sys.argv) > 1 else "Bugün piyasa durumu nasıl?"
    
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
    return answer

if __name__ == "__main__":
    main()
