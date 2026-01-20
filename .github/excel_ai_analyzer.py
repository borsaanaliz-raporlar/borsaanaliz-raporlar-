#!/usr/bin/env python3
"""
GERÇEK EXCEL ANALİST AI SİSTEMİ - VMA %94 DOĞRULUKLU
4 ana sayfadan AKILLI veri çekerek analiz yapar
"""
import os
import sys
import json
import pandas as pd
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
        
        # Metin ise temizle
        text = str(value).strip()
        # Virgülü noktaya çevir
        text = text.replace(',', '.')
        # Parantez içindeki sayıları temizle (örn: "NEGATİF (48)" -> "48")
        if '(' in text and ')' in text:
            # Sadece parantez içindeki sayıyı al
            try:
                number_text = text.split('(')[1].split(')')[0]
                return float(number_text)
            except:
                pass
        
        # Diğer karakterleri temizle
        text = ''.join(c for c in text if c.isdigit() or c == '.' or c == '-')
        
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
        # Sadece sayıları al
        text = ''.join(c for c in text if c.isdigit() or c == '-')
        
        if text == '' or text == '-':
            return default
            
        return int(float(text)) if '.' in text else int(text)
    except:
        return default

def extract_smart_data(excel_path):
    """4 ana sayfadan AKILLI veri çek"""
    print("🔍 Akıllı veri çekiliyor...")
    
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        all_data = {}
        
        # 1. SİNYALLER SAYFASI - En önemli 25 hisse
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            signals_data = []
            row_count = 0
            
            for row in ws.iter_rows(min_row=2, max_row=100, values_only=True):
                if row and row[0] and row_count < 25:
                    hisse = str(row[0]).strip()
                    if hisse and hisse != "None" and hisse != "":
                        # VMA değerini parse et
                        vma_raw = str(row[10]) if row[10] is not None else "NÖTR"
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
                        
                        # WT sinyalini kontrol et
                        wt_signal = "NÖTR"
                        if row[1] is not None:
                            wt_raw = str(row[1]).upper()
                            if "POZİTİF" in wt_raw:
                                wt_signal = "POZİTİF"
                            elif "NEGATİF" in wt_raw:
                                wt_signal = "NEGATİF"
                        
                        signals_data.append({
                            "HISSE": hisse,
                            "WT_SINYAL": wt_signal,
                            "WT_SINYAL_FIYAT": safe_float(row[2]),
                            "WT1": safe_float(row[3]),
                            "WT2": safe_float(row[4]),
                            "CLOSE": safe_float(row[7]),
                            "PIVOT": safe_float(row[8]),
                            "LSMA": str(row[9]) if row[9] is not None else "NÖTR",
                            "VMA": vma_raw,
                            "VMA_YON": vma_direction,
                            "VMA_GUN": vma_days,
                            "HACIM": safe_int(row[12]),
                            "DURUM": str(row[15]) if row[15] is not None else "NÖTR",
                            "AI_YORUM": str(row[32])[:100] if row[32] is not None else ""
                        })
                        row_count += 1
            
            all_data["sinyaller"] = signals_data
            print(f"   ✅ Sinyaller: {len(signals_data)} hisse")
        
        # 2. PIVOT_ANALIZ SAYFASI - En önemli 20 hisse
        if "PIVOT_ANALIZ" in wb.sheetnames:
            ws = wb["PIVOT_ANALIZ"]
            pivot_data = []
            row_count = 0
            
            for row in ws.iter_rows(min_row=2, max_row=50, values_only=True):
                if row and row[0] and row_count < 20:
                    sembol = str(row[0]).strip()
                    if sembol and sembol != "None" and sembol != "":
                        pivot_data.append({
                            "SEMBOL": sembol,
                            "GUNLUK_CLOSE": safe_float(row[8]),
                            "GUNLUK_P": safe_float(row[9]),
                            "GUNLUK_R1": safe_float(row[10]),
                            "GUNLUK_R2": safe_float(row[11]),
                            "GUNLUK_S1": safe_float(row[14]),
                            "GUNLUK_S2": safe_float(row[15]),
                            "HAFTALIK_CLOSE": safe_float(row[16]),
                            "HAFTALIK_P": safe_float(row[17]),
                            "AYLIK_CLOSE": safe_float(row[24]),
                            "AYLIK_P": safe_float(row[25])
                        })
                        row_count += 1
            
            all_data["pivot"] = pivot_data
            print(f"   ✅ Pivot Analiz: {len(pivot_data)} sembol")
        
        # 3. ENDEKSLER SAYFASI - Tüm endeksler
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            index_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=50, values_only=True):
                if row and row[0]:
                    sembol_raw = str(row[0])
                    # Tarih kısmını temizle
                    sembol = sembol_raw.split('(')[0].strip() if '(' in sembol_raw else sembol_raw.strip()
                    if sembol and sembol != "None" and sembol != "":
                        index_data.append({
                            "ENDEKS": sembol,
                            "WT_SINYAL": "POZİTİF" if row[1] and "POZİTİF" in str(row[1]).upper() else "NEGATİF" if row[1] and "NEGATİF" in str(row[1]).upper() else "NÖTR",
                            "CLOSE": safe_float(row[6]),
                            "PIVOT": safe_float(row[7]),
                            "LSMA": str(row[8]) if row[8] is not None else "NÖTR",
                            "VMA": str(row[9]) if row[9] is not None else "NÖTR",
                            "DURUM": str(row[15]) if row[15] is not None else "NÖTR"
                        })
            
            all_data["endeksler"] = index_data
            print(f"   ✅ Endeksler: {len(index_data)} endeks")
        
        # 4. FON_EMTIA_COIN_DOVIZ SAYFASI - Önemli varlıklar
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            asset_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=30, values_only=True):
                if row and row[0]:
                    sembol_raw = str(row[0])
                    sembol = sembol_raw.split('(')[0].strip() if '(' in sembol_raw else sembol_raw.strip()
                    if sembol and sembol != "None" and sembol != "":
                        asset_data.append({
                            "VARLIK": sembol,
                            "WT_SINYAL": "POZİTİF" if row[1] and "POZİTİF" in str(row[1]).upper() else "NEGATİF" if row[1] and "NEGATİF" in str(row[1]).upper() else "NÖTR",
                            "CLOSE": safe_float(row[6]),
                            "PIVOT": safe_float(row[7]),
                            "LSMA": str(row[8]) if row[8] is not None else "NÖTR",
                            "VMA": str(row[9]) if row[9] is not None else "NÖTR",
                            "DURUM": str(row[15]) if row[15] is not None else "NÖTR",
                            "AI_YORUM": str(row[32])[:80] if row[32] is not None else ""
                        })
            
            all_data["varliklar"] = asset_data
            print(f"   ✅ Varlıklar: {len(asset_data)} varlık")
        
        wb.close()
        
        # İSTATİSTİKLER
        stats = {
            "toplam_hisse": len(all_data.get("sinyaller", [])),
            "vma_pozitif": len([h for h in all_data.get("sinyaller", []) 
                               if h.get("VMA_YON") == "POZİTİF"]),
            "vma_negatif": len([h for h in all_data.get("sinyaller", []) 
                               if h.get("VMA_YON") == "NEGATİF"]),
            "wt_pozitif": len([h for h in all_data.get("sinyaller", []) 
                              if h.get("WT_SINYAL") == "POZİTİF"]),
            "wt_negatif": len([h for h in all_data.get("sinyaller", []) 
                              if h.get("WT_SINYAL") == "NEGATİF"]),
            "toplam_endeks": len(all_data.get("endeksler", [])),
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        all_data["istatistikler"] = stats
        print(f"📊 Özet: {stats['toplam_hisse']} hisse | VMA+: {stats['vma_pozitif']} | VMA-: {stats['vma_negatif']}")
        
        return all_data
        
    except Exception as e:
        print(f"❌ Veri çekme hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Veri çekme hatası: {str(e)}"}

def create_ai_prompt(question, excel_data):
    """AI için AKILLI prompt oluştur - VMA %94 ÖZEL"""
    
    vma_strong = []
    for h in excel_data.get("sinyaller", []):
        if h.get("VMA_YON") == "POZİTİF":
            vma_strong.append({
                "hisse": h["HISSE"],
                "vma": h["VMA"],
                "vma_gun": h.get("VMA_GUN", 0),
                "close": h["CLOSE"],
                "wt": h["WT_SINYAL"],
                "pivot": h["PIVOT"]
            })
    
    vma_weak = []
    for h in excel_data.get("sinyaller", []):
        if h.get("VMA_YON") == "NEGATİF":
            vma_weak.append({
                "hisse": h["HISSE"],
                "vma": h["VMA"],
                "vma_gun": h.get("VMA_GUN", 0),
                "close": h["CLOSE"],
                "wt": h["WT_SINYAL"]
            })
    
    signals_summary = []
    for h in excel_data.get("sinyaller", [])[:8]:
        pivot = h.get('PIVOT', 0)
        close = h.get('CLOSE', 0)
        pivot_fark = 0
        if pivot > 0:
            pivot_fark = ((close - pivot) / pivot * 100)
        
        signals_summary.append(
            f"{h['HISSE']}: {close:.2f}TL | VMA: {h.get('VMA', 'NÖTR')} | "
            f"WT: {h.get('WT_SINYAL', 'NÖTR')} | Pivot: {pivot:.2f} "
            f"({'üstünde' if close > pivot else 'altında' if close < pivot else 'aynı'})"
        )
    
    vma_section = f"""
⚡ **VMA TREND ALGORİTMASI - %94 DOĞRULUK ORANI:**
TradingView'de özel geliştirilmiş, piyasadaki EN GÜVENİLİR trend göstergesi.

📊 **VMA YORUM KURALLARI:**
• "POZİTİF (X)": X gündür YUKARI trend (%94 güvenle)
  - X > 30: ÇOK GÜÇLÜ trend (uzun süredir)
  - X 15-30: GÜÇLÜ trend
  - X < 15: YENİ başlayan trend
• "NEGATİF (X)": X gündür AŞAĞI trend
• VMA diğer tüm göstergelerden DAHA ÖNEMLİDİR

🔥 **VMA POZİTİF HİSSELER ({len(vma_strong)} adet):**
"""
    
    vma_top = []
    for v in vma_strong[:6]:
        vma_top.append(f"• {v['hisse']}: {v['close']:.2f}TL | VMA: {v['vma']} | WT: {v['wt']}")
    
    vma_section += chr(10).join(vma_top) if vma_top else "• VMA POZİTİF hisse bulunamadı"
    
    vma_section += f"\n\n📉 **VMA NEGATİF HİSSELER ({len(vma_weak)} adet):**"
    vma_weak_top = []
    for v in vma_weak[:4]:
        vma_weak_top.append(f"• {v['hisse']}: {v['close']:.2f}TL | VMA: {v['vma']}")
    
    vma_section += chr(10).join(vma_weak_top) if vma_weak_top else "• VMA NEGATİF hisse bulunamadı"
    
    stats = excel_data.get("istatistikler", {})
    
    prompt = f"""🎯 **SEN: BORSAANALIZ GERÇEK ANALİST - VMA %94 DOĞRULUKLU**

{vma_section}

📊 **PİYASA ÖZETİ ({stats.get('tarih', 'Bugün')}):**
• Toplam Analiz: {stats.get('toplam_hisse', 0)} hisse
• VMA POZİTİF: {stats.get('vma_pozitif', 0)} hisse
• VMA NEGATİF: {stats.get('vma_negatif', 0)} hisse
• WT POZİTİF: {stats.get('wt_pozitif', 0)} hisse
• WT NEGATİF: {stats.get('wt_negatif', 0)} hisse

🔍 **ÖNE ÇIKAN HİSSELER (İlk 8):**
{chr(10).join(signals_summary)}

📋 **ANALİZ ÖNCELİK SIRASI (EN ÖNEMLİDEN):**

1. 🔥 **VMA TREND ALGORİTMASI (%94 DOĞRULUK)** - EN ÖNEMLİ!
   - VMA "POZİTİF (X)": X gündür yukarı trend (çok güvenilir)
   - VMA "NEGATİF (X)": X gündür aşağı trend
   - VMA > 30 gün: ÇOK GÜÇLÜ trend

2. 📈 **WT (WAVE TREND) - KISA VADE**
   - WT POZİTİF: Kısa vadeli alım sinyali
   - WT NEGATİF: Kısa vadeli satım/dikkat sinyali

3. 🎯 **PIVOT ANALİZİ - TEKNİK SEVİYELER**
   - Close > Pivot: Teknik olarak GÜÇLÜ
   - Close < Pivot: Teknik olarak ZAYIF
   - R1/R2/R3: Direnç seviyeleri
   - S1/S2/S3: Destek seviyeleri

4. 📊 **LSMA KAMA - ORTA VADE**
   - LSMA POZİTİF: Orta vadeli trend yukarı
   - LSMA NEGATİF: Orta vadeli trend aşağı

⚠️ **SİNYAL ÇATIŞMASI DURUMU:**
• VMA POZİTİF + WT NEGATİF = "ANA TREND YUKARI, kısa vadede düzeltme"
• VMA NEGATİF + WT POZİTİF = "ANA TREND AŞAĞI, kısa vadeli toparlanma"
• HER ZAMAN VMA'ya DAHA FAZLA ÖNEM VER!

✅ **DOĞRU ANALİZ FORMATI:**
📊 [HİSSE] ANALİZİ - {stats.get('tarih', 'Bugün')}

🔥 VMA TREND (%94): [POZİTİF/NEGATİF] ([X] gün)
📈 WT SİNYALİ: [POZİTİF/NEGATİF] (WT1: [değer])
🎯 PIVOT: [Close]TL vs [Pivot]TL ([üstünde/altında])
📊 LSMA: [POZİTİF/NEGATİF]

💪 TREND GÜCÜ:
• VMA [X] gündür [yön] trend
• WT sinyali: [uyumlu/çatışmalı]
• Pivot durumu: [güçlü/zayıf]

🛡️ DESTEK/DİRENÇ: S1: [A]TL, R1: [B]TL
⚡ VMA YORUMU: [X] gündür %94 güvenle [yön] trend
🎯 ÖNERİ: [VMA trendine göre takip önerisi]

text

🚫 **YAPMA:**
• Yatırım tavsiyesi VERME ("al", "sat" deme)
• Excel'de olmayan veri UYDURMA
• Sadece "X sayfasında Y var" deme - ANALİZ YAP!

✅ **YAP:**
• VMA trendini MUTLAKA vurgula
• Sayısal verileri KULLAN (fiyat, yüzde, gün sayısı)
• Trend çatışmasını AÇIKLA
• Risk/fırsat dengesini GÖSTER

📝 **SPESİFİK SORULAR İÇİN:**

A) **HİSSE SORUSU** ("GMSTR analizi?"):
   - Önce VMA'sını BUL: POZİTİF/NEGATİF? Kaç gün?
   - WT ile karşılaştır: Uyumlu mu?
   - Pivot durumunu HESAPLA
   - VMA trendine göre YORUM yap

B) **GENEL DURUM** ("Piyasa nasıl?"):
   - VMA POZİTİF/NEGATİF oranını SÖYLE
   - En güçlü VMA trendli hisseleri LİSTELE
   - Genel trend yorumu YAP

C) **VMA SORUSU** ("VMA nedir? Nasıl yorumlanır?"):
   - %94 doğruluk oranını VURGULA
   - "POZİTİF (X)" formatını AÇIKLA
   - Diğer göstergelerden FARKINI belirt
   - Örneklerle GÖSTER

D) **KARŞILAŞTIRMA** ("AKBNK vs GARAN?"):
   - Her ikisinin VMA trendini KARŞILAŞTIR
   - Hangi trend DAHA GÜÇLÜ?
   - WT ve Pivot farklarını GÖSTER

🔔 **SON UYARI:** Tüm analizler bilgi amaçlıdır. %94 doğruluklu VMA trendi EN GÜVENİLİR göstergedir.

📋 **KULLANICI SORUSU: "{question}"**

🎯 **ŞİMDİ DETAYLI ANALİZ YAP VE YANIT VER:**
"""
    
    return prompt

def call_ai_analyst(question, excel_data):
    """GERÇEK analiz yapan AI çağır"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY eksik!")
        return "GROQ_API_KEY eksik. Lütfen GitHub Secrets'ta GROQ_API_KEY ayarlayın."
    
    system_prompt = create_ai_prompt(question, excel_data)
    
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
        "max_tokens": 1000,
        "temperature": 0.15,
        "stream": False
    }
    
    try:
        print("🤖 AI VMA analizi yapıyor...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ API Hatası: {response.status_code}")
            return f"API hatası: {response.status_code} - {response.text[:200]}"
            
    except Exception as e:
        print(f"❌ Bağlantı hatası: {str(e)}")
        return f"Bağlantı hatası: {str(e)}"

def main():
    """Ana fonksiyon"""
    question = sys.argv[1] if len(sys.argv) > 1 else "Bugün VMA trendine göre piyasa nasıl?"
    
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        answer = "⚠️ Excel dosyası bulunamadı"
    else:
        print(f"📖 Excel okunuyor: {excel_info['name']}")
        excel_data = extract_smart_data(excel_info['path'])
        
        if "error" in excel_data:
            answer = f"⚠️ {excel_data['error']}"
        else:
            answer = call_ai_analyst(question, excel_data)
    
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("✅ VMA analizi tamamlandı!")
    print(f"📄 Yanıt uzunluğu: {len(answer)} karakter")
    
    return answer

if __name__ == "__main__":
    main()
