#!/usr/bin/env python3
"""
GERÇEK EXCEL ANALİST AI SİSTEMİ - VMA %94 DOĞRULUKLU
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

def safe_float(value, default=0):
    """Güvenli float dönüşümü"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        
        text = str(value).strip()
        text = text.replace(',', '.')
        
        if '(' in text and ')' in text:
            text = text.split('(')[0].strip()
        
        text = re.sub(r'[^\d.\-]', '', text)
        
        if text == '' or text == '-':
            return default
            
        return float(text)
    except:
        return default

def safe_int(value, default=0):
    """Güvenli int dönüşümü"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return int(value)
        
        text = str(value).strip()
        text = re.sub(r'[^\d\-]', '', text)
        
        if text == '' or text == '-':
            return default
            
        return int(text)
    except:
        return default

def parse_hisse_row(row, sheet_type):
    """Hisse satırını parse et"""
    try:
        if not row or not row[0]:
            return None
        
        hisse_raw = str(row[0]).strip()
        hisse = hisse_raw.split('(')[0].strip() if '(' in hisse_raw else hisse_raw
        
        # WT Sinyali
        wt_raw = str(row[1]) if len(row) > 1 and row[1] is not None else ""
        wt_signal = "NÖTR"
        if wt_raw:
            wt_upper = wt_raw.upper()
            if "POZİTİF" in wt_upper:
                wt_signal = "POZİTİF"
            elif "NEGATİF" in wt_upper:
                wt_signal = "NEGATİF"
        
        # Temel veriler
        close = safe_float(row[6]) if len(row) > 6 else 0
        pivot = safe_float(row[7]) if len(row) > 7 else 0
        lsma_raw = str(row[8]) if len(row) > 8 and row[8] is not None else "NÖTR"
        
        # VMA (EN ÖNEMLİ)
        vma_raw = str(row[9]) if len(row) > 9 and row[9] is not None else "NÖTR"
        vma_direction = "NÖTR"
        vma_days = 0
        
        if vma_raw and isinstance(vma_raw, str):
            vma_clean = vma_raw.strip()
            vma_upper = vma_clean.upper()
            
            if "POZİTİF" in vma_upper:
                vma_direction = "POZİTİF"
            elif "NEGATİF" in vma_upper:
                vma_direction = "NEGATİF"
            
            if "(" in vma_clean and ")" in vma_clean:
                try:
                    days_part = vma_clean.split("(")[1].split(")")[0]
                    vma_days = safe_int(days_part, 0)
                except:
                    vma_days = 0
        
        return {
            "HISSE": hisse,
            "WT_SINYAL": wt_signal,
            "CLOSE": close,
            "PIVOT": pivot,
            "LSMA": lsma_raw,
            "VMA": vma_raw,
            "VMA_YON": vma_direction,
            "VMA_GUN": vma_days,
            "HACIM": safe_int(row[12]) if len(row) > 12 else 0,
            "DURUM": str(row[15]) if len(row) > 15 and row[15] is not None else "NÖTR",
            "SAYFA": sheet_type
        }
        
    except Exception as e:
        return None

def find_hisse_in_excel(excel_path, hisse_adi):
    """Excel'de hisse ara"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        hisse_upper = hisse_adi.upper().strip()
        
        sheets_to_search = ["Sinyaller", "FON_EMTIA_COIN_DOVIZ", "ENDEKSLER"]
        
        for sheet_name in sheets_to_search:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                
                for row in ws.iter_rows(min_row=2, max_row=500, values_only=True):
                    if row and row[0]:
                        current_raw = str(row[0])
                        current_clean = current_raw.split('(')[0].strip().upper()
                        
                        if hisse_upper == current_clean:
                            wb.close()
                            return {sheet_name: parse_hisse_row(row, sheet_name)}
        
        wb.close()
        return {"error": f"'{hisse_adi}' bulunamadı"}
        
    except Exception as e:
        return {"error": f"Arama hatası: {str(e)}"}

def extract_smart_data(excel_path):
    """Genel piyasa verisi çek"""
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            signals_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=30, values_only=True):
                if row and row[0]:
                    hisse_data = parse_hisse_row(row, "Sinyaller")
                    if hisse_data:
                        signals_data.append(hisse_data)
            
            all_data["sinyaller"] = signals_data[:8]
        
        wb.close()
        
        # İstatistikler
        all_sinyaller = all_data.get("sinyaller", [])
        stats = {
            "toplam_hisse": len(all_sinyaller),
            "vma_pozitif": len([h for h in all_sinyaller if h.get("VMA_YON") == "POZİTİF"]),
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        all_data["istatistikler"] = stats
        return all_data
        
    except Exception as e:
        return {"error": f"Veri çekme hatası: {str(e)}"}

def detect_hisse_from_question(question):
    """Sorudan hisse adını tespit et"""
    # Büyük harfli kelimeleri bul (hisse isimleri genelde büyük harf)
    words = question.upper().split()
    
    # Türk hisse pattern'leri (3-5 harf, genelde)
    hisse_candidates = []
    for word in words:
        # Kelimeyi temizle
        clean_word = re.sub(r'[^A-Z]', '', word)
        
        # Hisse kriterleri
        if 3 <= len(clean_word) <= 6:
            # Yaygın hisse uzunlukları
            hisse_candidates.append(clean_word)
    
    # Öncelik sırası
    common_hisses = ["GMSTR", "AKBNK", "GARAN", "THYAO", "ASELS", "EREGL", 
                     "FROTO", "SASA", "KCHOL", "TOASO", "TUPRS", "YKBNK",
                     "XU100", "BIST100", "USDTRY", "EURTRY", "ALTIN"]
    
    # Önce yaygın hisselerde ara
    for hisse in common_hisses:
        if hisse in question.upper():
            return hisse
    
    # Sonra diğer adaylarda ara
    for candidate in hisse_candidates:
        if candidate in common_hisses or len(candidate) == 4:  # 4 harfli hisseler yaygın
            return candidate
    
    return None

def create_ai_prompt(question, excel_data, hisse_data=None):
    """AI için prompt"""
    
    if hisse_data and "error" not in hisse_data:
        # HISSE ANALİZİ
        for sheet_name, data in hisse_data.items():
            if data:
                hisse_name = data.get("HISSE", "")
                vma_raw = data.get("VMA", "NÖTR")
                vma_direction = data.get("VMA_YON", "NÖTR")
                vma_days = data.get("VMA_GUN", 0)
                close = data.get("CLOSE", 0)
                pivot = data.get("PIVOT", 0)
                wt_signal = data.get("WT_SINYAL", "NÖTR")
                lsma = data.get("LSMA", "NÖTR")
                
                hisse_info = f"""📋 **{hisse_name} ANALİZ VERİLERİ:**
• Fiyat: {close:.2f}TL
• Pivot: {pivot:.2f}TL ({'üstünde' if close > pivot else 'altında' if close < pivot else 'aynı'})
• WT Sinyali: {wt_signal}
• LSMA: {lsma}
• VMA: {vma_raw}"""
                
                vma_analysis = f"""🔥 **VMA TREND (%94 DOĞRULUK):** {vma_direction}"""
                if vma_days > 0:
                    vma_analysis += f" ({vma_days} gün)"
                
                if vma_days > 30:
                    vma_analysis += "\n• 📈 TREND GÜCÜ: ÇOK GÜÇLÜ (30+ gün)"
                elif vma_days > 15:
                    vma_analysis += "\n• 📈 TREND GÜCÜ: GÜÇLÜ (15-30 gün)"
                
                break
        
        prompt = f"""🎯 **SEN: BORSAANALIZ GERÇEK ANALİST**

{hisse_info}

{vma_analysis}

⚡ **ANALİZ KURALLARI:**
1. VMA %94 doğruluğunu VURGULA
2. Sayısal verileri KULLAN
3. Trend çatışmasını AÇIKLA

**SORU: "{question}"**

🎯 **ANALİZ YAP:**
"""
        return prompt
    
    else:
        # GENEL ANALİZ
        stats = excel_data.get("istatistikler", {})
        
        prompt = f"""🎯 **SEN: BORSAANALIZ GERÇEK ANALİST**

📊 **PİYASA DURUMU ({stats.get('tarih', 'Bugün')}):**
• Analiz edilen: {stats.get('toplam_hisse', 0)} hisse
• VMA POZİTİF: {stats.get('vma_pozitif', 0)} hisse

⚡ **VMA TREND: %94 doğruluk oranı**

**SORU: "{question}"**

🎯 **ANALİZ YAP:**
"""
        return prompt

def call_ai_analyst(question, excel_data, hisse_data=None):
    """AI çağır"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY eksik"
    
    system_prompt = create_ai_prompt(question, excel_data, hisse_data)
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": 800,
        "temperature": 0.15,
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
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API hatası: {response.status_code}"
            
    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"

def main():
    """Ana fonksiyon"""
    question = sys.argv[1] if len(sys.argv) > 1 else "Bugün piyasa durumu nasıl?"
    
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        return "⚠️ Excel dosyası bulunamadı"
    
    print(f"📖 Excel: {excel_info['name']}")
    
    # Hisse tespit et
    hisse_adi = detect_hisse_from_question(question)
    hisse_data = None
    
    if hisse_adi:
        print(f"🎯 Hisse tespit edildi: {hisse_adi}")
        hisse_data = find_hisse_in_excel(excel_info['path'], hisse_adi)
    
    # Genel veri
    excel_data = extract_smart_data(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"⚠️ {excel_data['error']}"
    else:
        answer = call_ai_analyst(question, excel_data, hisse_data)
    
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("✅ Analiz tamamlandı!")
    return answer

if __name__ == "__main__":
    main()
