#!/usr/bin/env python3
"""
GERÇEK EXCEL ANALİST AI SİSTEMİ - VMA %94 DOĞRULUKLU
TÜM sayfalarda hisse arayarak analiz yapar
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
        
        # Parantez içindeki sayıları temizle
        if '(' in text and ')' in text:
            text = text.split('(')[0].strip()
        
        # Sadece sayıları al
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
    if not row or not row[0]:
        return None
    
    # Hisse adını temizle
    hisse_raw = str(row[0]).strip()
    hisse = hisse_raw.split('(')[0].strip() if '(' in hisse_raw else hisse_raw
    
    # VMA parse et
    vma_raw = str(row[10]) if len(row) > 10 and row[10] is not None else "NÖTR"
    vma_direction = "NÖTR"
    vma_days = 0
    
    if vma_raw and isinstance(vma_raw, str):
        vma_upper = vma_raw.upper()
        if "POZİTİF" in vma_upper:
            vma_direction = "POZİTİF"
        elif "NEGATİF" in vma_upper:
            vma_direction = "NEGATİF"
        
        # Gün sayısını çıkar
        if "(" in vma_raw and ")" in vma_raw:
            try:
                days_text = vma_raw.split("(")[1].split(")")[0]
                vma_days = safe_int(days_text, 0)
            except:
                vma_days = 0
    
    # WT sinyali
    wt_signal = "NÖTR"
    if len(row) > 1 and row[1] is not None:
        wt_raw = str(row[1]).upper()
        if "POZİTİF" in wt_raw:
            wt_signal = "POZİTİF"
        elif "NEGATİF" in wt_raw:
            wt_signal = "NEGATİF"
    
    return {
        "HISSE": hisse,
        "WT_SINYAL": wt_signal,
        "WT_SINYAL_FIYAT": safe_float(row[2]) if len(row) > 2 else 0,
        "WT1": safe_float(row[3]) if len(row) > 3 else 0,
        "WT2": safe_float(row[4]) if len(row) > 4 else 0,
        "CLOSE": safe_float(row[6]) if len(row) > 6 else 0,
        "PIVOT": safe_float(row[7]) if len(row) > 7 else 0,
        "LSMA": str(row[8]) if len(row) > 8 and row[8] is not None else "NÖTR",
        "VMA": vma_raw,
        "VMA_YON": vma_direction,
        "VMA_GUN": vma_days,
        "HACIM": safe_int(row[11]) if len(row) > 11 else 0,
        "DURUM": str(row[15]) if len(row) > 15 and row[15] is not None else "NÖTR",
        "AI_YORUM": str(row[32])[:100] if len(row) > 32 and row[32] is not None else "",
        "SAYFA": sheet_type
    }

def parse_pivot_row(row):
    """Pivot satırını parse et"""
    if not row or not row[0]:
        return None
    
    sembol = str(row[0]).strip()
    return {
        "SEMBOL": sembol,
        "GUNLUK_CLOSE": safe_float(row[8]),
        "GUNLUK_P": safe_float(row[9]),
        "GUNLUK_R1": safe_float(row[10]),
        "GUNLUK_S1": safe_float(row[14]),
        "HAFTALIK_CLOSE": safe_float(row[16]),
        "HAFTALIK_P": safe_float(row[17]),
        "AYLIK_CLOSE": safe_float(row[24]),
        "AYLIK_P": safe_float(row[25])
    }

def find_hisse_in_excel(excel_path, hisse_adi):
    """Excel'de hisseyi TÜM sayfalarda ara"""
    print(f"🔍 '{hisse_adi}' aranıyor...")
    
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        hisse_upper = hisse_adi.upper().strip()
        all_data = {}
        
        # TÜM SAYFALARDA ARA
        sheets_to_search = ["Sinyaller", "FON_EMTIA_COIN_DOVIZ", "ENDEKSLER", "PIVOT_ANALIZ"]
        
        for sheet_name in sheets_to_search:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                found = False
                
                for row in ws.iter_rows(min_row=2, max_row=300, values_only=True):
                    if row and row[0]:
                        current_raw = str(row[0])
                        # Hisse adını temizle (tarih vb. kaldır)
                        current_clean = current_raw.split('(')[0].strip().upper()
                        
                        if hisse_upper == current_clean:
                            print(f"✅ '{hisse_adi}' bulundu: {sheet_name} sayfasında")
                            
                            if sheet_name in ["Sinyaller", "FON_EMTIA_COIN_DOVIZ", "ENDEKSLER"]:
                                all_data[sheet_name] = parse_hisse_row(row, sheet_name)
                            elif sheet_name == "PIVOT_ANALIZ":
                                all_data[sheet_name] = parse_pivot_row(row)
                            
                            found = True
                            break
                
                if found:
                    break
        
        wb.close()
        
        if not all_data:
            print(f"❌ '{hisse_adi}' hiçbir sayfada bulunamadı!")
            return {"error": f"'{hisse_adi}' bulunamadı"}
        
        return all_data
        
    except Exception as e:
        print(f"❌ Arama hatası: {str(e)}")
        return {"error": f"Arama hatası: {str(e)}"}

def extract_smart_data(excel_path):
    """Genel piyasa verisi çek"""
    print("📊 Genel piyasa verisi çekiliyor...")
    
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        # Sinyaller sayfasından özet
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            signals_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=30, values_only=True):
                if row and row[0]:
                    hisse_data = parse_hisse_row(row, "Sinyaller")
                    if hisse_data:
                        signals_data.append(hisse_data)
            
            all_data["sinyaller"] = signals_data[:10]  # İlk 10
            print(f"   ✅ Sinyaller: {len(signals_data)} hisse")
        
        # Varlıklar sayfasından özet (GMSTR BURADA!)
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            assets_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=20, values_only=True):
                if row and row[0]:
                    asset_data = parse_hisse_row(row, "Varlıklar")
                    if asset_data:
                        assets_data.append(asset_data)
            
            all_data["varliklar"] = assets_data[:8]
            print(f"   ✅ Varlıklar: {len(assets_data)} varlık")
        
        # Endeksler
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            index_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=15, values_only=True):
                if row and row[0]:
                    index_data.append(parse_hisse_row(row, "Endeksler"))
            
            all_data["endeksler"] = index_data[:5]
            print(f"   ✅ Endeksler: {len(index_data)} endeks")
        
        wb.close()
        
        # İstatistikler
        all_sinyaller = all_data.get("sinyaller", [])
        all_varliklar = all_data.get("varliklar", [])
        
        stats = {
            "toplam_hisse": len(all_sinyaller),
            "vma_pozitif": len([h for h in all_sinyaller if h.get("VMA_YON") == "POZİTİF"]),
            "vma_negatif": len([h for h in all_sinyaller if h.get("VMA_YON") == "NEGATİF"]),
            "toplam_varlik": len(all_varliklar),
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        all_data["istatistikler"] = stats
        print(f"📊 Özet: {stats['toplam_hisse']} hisse | {stats['toplam_varlik']} varlık")
        
        return all_data
        
    except Exception as e:
        print(f"❌ Veri çekme hatası: {str(e)}")
        return {"error": f"Veri çekme hatası: {str(e)}"}

def create_ai_prompt(question, excel_data, hisse_data=None):
    """AI için prompt oluştur"""
    
    # Hisse sorusu mu?
    is_hisse_query = False
    hisse_name = ""
    
    # Basit hisse tespiti
    common_hisses = ["GMSTR", "AKBNK", "GARAN", "THYAO", "ASELS", "EREGL", "TUPRS", "YKBNK"]
    for hisse in common_hisses:
        if hisse.lower() in question.lower():
            is_hisse_query = True
            hisse_name = hisse
            break
    
    if hisse_data and "error" not in hisse_data:
        # HISSE ÖZEL PROMPT
        hisse_info = ""
        for sheet_name, data in hisse_data.items():
            if data:
                hisse_info += f"\n📋 **{sheet_name} Sayfasından:**\n"
                hisse_info += f"• Hisse: {data.get('HISSE', 'N/A')}\n"
                hisse_info += f"• Fiyat: {data.get('CLOSE', 0):.2f}TL\n"
                hisse_info += f"• VMA: {data.get('VMA', 'NÖTR')} ({data.get('VMA_YON', 'NÖTR')})\n"
                hisse_info += f"• WT: {data.get('WT_SINYAL', 'NÖTR')}\n"
                hisse_info += f"• Pivot: {data.get('PIVOT', 0):.2f}TL\n"
                hisse_info += f"• LSMA: {data.get('LSMA', 'NÖTR')}\n"
                hisse_info += f"• Durum: {data.get('DURUM', 'NÖTR')}\n"
        
        prompt = f"""🎯 **SEN: BORSAANALIZ GERÇEK ANALİST - {hisse_name.upper()} ANALİZİ**

{hisse_info}

⚡ **VMA TREND ALGORİTMASI - %94 DOĞRULUK:**
• VMA "POZİTİF (X)": X gündür yukarı trend
• VMA "NEGATİF (X)": X gündür aşağı trend
• VMA > 30 gün: ÇOK GÜÇLÜ trend

📊 **ANALİZ KURALLARI:**
1. Önce VMA trendine bak (%94 doğruluk)
2. WT ile uyumunu kontrol et
3. Pivot seviyesini değerlendir
4. LSMA trendini göz önünde bulundur

📈 **DOĞRU ANALİZ FORMATI:**
📊 {hisse_name.upper()} ANALİZİ

🔥 VMA TREND (%94): [POZİTİF/NEGATİF] ([X] gün)
📈 WT SİNYALİ: [POZİTİF/NEGATİF]
🎯 FİYAT: [Close]TL vs Pivot: [Pivot]TL ([üstünde/altında])
📊 LSMA: [POZİTİF/NEGATİF]

💪 TREND GÜCÜ ANALİZİ:
• VMA: [X] gündür [yön] trend
• WT: [uyumlu/çatışmalı]
• Teknik durum: [güçlü/zayıf]

⚠️ **YAPMA:**
• "al", "sat" deme
• Excel'de olmayan veri uydurma

✅ **YAP:**
• VMA %94 doğruluğunu vurgula
• Sayısal verileri kullan
• Risk/fırsat dengesini göster

🔔 **SON UYARI:** Bilgi amaçlıdır.

**SORU: "{question}"**

🎯 **ŞİMDİ DETAYLI {hisse_name.upper()} ANALİZİ YAP:**
"""
        return prompt
    
    else:
        # GENEL PROMPT
        stats = excel_data.get("istatistikler", {})
        
        # Öne çıkan hisseler
        top_hisses = []
        for h in excel_data.get("sinyaller", [])[:5]:
            top_hisses.append(f"• {h['HISSE']}: {h['CLOSE']:.2f}TL, VMA: {h['VMA']}")
        
        # Varlıklar
        top_assets = []
        for a in excel_data.get("varliklar", [])[:5]:
            top_assets.append(f"• {a['HISSE']}: {a['CLOSE']:.2f}TL, VMA: {a['VMA']}")
        
        prompt = f"""🎯 **SEN: BORSAANALIZ GERÇEK ANALİST**

📊 **PİYASA ÖZETİ ({stats.get('tarih', 'Bugün')}):**
• Analiz edilen: {stats.get('toplam_hisse', 0)} hisse
• VMA POZİTİF: {stats.get('vma_pozitif', 0)} hisse
• Varlıklar: {stats.get('toplam_varlik', 0)} adet

🔍 **ÖNE ÇIKAN HİSSELER:**
{chr(10).join(top_hisses) if top_hisses else '• Veri yok'}

💰 **ÖNEMLİ VARLIKLAR:**
{chr(10).join(top_assets) if top_assets else '• Veri yok'}

⚡ **VMA TREND ALGORİTMASI - %94 DOĞRULUK:**
• "POZİTİF (X)": X gündür yukarı trend
• "NEGATİF (X)": X gündür aşağı trend
• EN GÜVENİLİR gösterge

📋 **ANALİZ KURALLARI:**
1. VMA'ya ÖNCELİK ver (%94 doğruluk)
2. Sayısal veriler kullan
3. Risk/fırsat dengesini göster

**SORU: "{question}"**

🎯 **ŞİMDİ ANALİZ YAP:**
"""
        return prompt

def call_ai_analyst(question, excel_data, hisse_data=None):
    """AI çağır"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY eksik"
    
    system_prompt = create_ai_prompt(question, excel_data, hisse_data)
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
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
        print("🤖 AI analiz yapıyor...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
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
        answer = "⚠️ Excel dosyası bulunamadı"
    else:
        print(f"📖 Excel: {excel_info['name']}")
        
        # Hisse sorusu mu?
        hisse_data = None
        common_hisses = ["GMSTR", "AKBNK", "GARAN", "THYAO", "ASELS"]
        for hisse in common_hisses:
            if hisse.lower() in question.lower():
                print(f"🎯 {hisse} hissesi aranıyor...")
                hisse_data = find_hisse_in_excel(excel_info['path'], hisse)
                break
        
        # Genel veri çek
        excel_data = extract_smart_data(excel_info['path'])
        
        if "error" in excel_data:
            answer = f"⚠️ {excel_data['error']}"
        else:
            answer = call_ai_analyst(question, excel_data, hisse_data)
    
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("✅ Analiz tamamlandı!")
    print(f"📄 Yanıt: {answer[:200]}...")
    
    return answer

if __name__ == "__main__":
    main()
