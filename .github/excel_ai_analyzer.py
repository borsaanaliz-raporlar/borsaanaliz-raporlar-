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
                    if hisse and hisse != "None":
                        vma_raw = str(row[10]) if row[10] else "NÖTR"
                        vma_direction = "POZİTİF" if "POZİTİF" in vma_raw.upper() else "NEGATİF" if "NEGATİF" in vma_raw.upper() else "NÖTR"
                        vma_days = 0
                        if "(" in vma_raw and ")" in vma_raw:
                            try:
                                vma_days = int(vma_raw.split("(")[1].split(")")[0])
                            except:
                                vma_days = 0
                        
                        signals_data.append({
                            "HISSE": hisse,
                            "WT_SINYAL": str(row[1]) if row[1] else "NÖTR",
                            "WT_SINYAL_FIYAT": float(str(row[2]).replace(',', '.')) if row[2] else 0,
                            "WT1": float(str(row[3]).replace(',', '.')) if row[3] else 0,
                            "WT2": float(str(row[4]).replace(',', '.')) if row[4] else 0,
                            "CLOSE": float(str(row[7]).replace(',', '.')) if row[7] else 0,
                            "PIVOT": float(str(row[8]).replace(',', '.')) if row[8] else 0,
                            "LSMA": str(row[9]) if row[9] else "NÖTR",
                            "VMA": vma_raw,
                            "VMA_YON": vma_direction,
                            "VMA_GUN": vma_days,
                            "HACIM": int(float(str(row[12]))) if row[12] else 0,
                            "DURUM": str(row[15]) if row[15] else "NÖTR",
                            "AI_YORUM": str(row[32])[:100] if row[32] else ""
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
                    if sembol and sembol != "None":
                        pivot_data.append({
                            "SEMBOL": sembol,
                            "GUNLUK_CLOSE": float(str(row[8]).replace(',', '.')) if row[8] else 0,
                            "GUNLUK_P": float(str(row[9]).replace(',', '.')) if row[9] else 0,
                            "GUNLUK_R1": float(str(row[10]).replace(',', '.')) if row[10] else 0,
                            "GUNLUK_R2": float(str(row[11]).replace(',', '.')) if row[11] else 0,
                            "GUNLUK_S1": float(str(row[14]).replace(',', '.')) if row[14] else 0,
                            "GUNLUK_S2": float(str(row[15]).replace(',', '.')) if row[15] else 0,
                            "HAFTALIK_CLOSE": float(str(row[16]).replace(',', '.')) if row[16] else 0,
                            "HAFTALIK_P": float(str(row[17]).replace(',', '.')) if row[17] else 0,
                            "AYLIK_CLOSE": float(str(row[24]).replace(',', '.')) if row[24] else 0,
                            "AYLIK_P": float(str(row[25]).replace(',', '.')) if row[25] else 0
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
                    sembol = str(row[0]).split()[0] if ' ' in str(row[0]) else str(row[0])
                    if sembol and sembol != "None":
                        index_data.append({
                            "ENDEKS": sembol,
                            "WT_SINYAL": str(row[1]) if row[1] else "NÖTR",
                            "CLOSE": float(str(row[6]).replace(',', '.')) if row[6] else 0,
                            "PIVOT": float(str(row[7]).replace(',', '.')) if row[7] else 0,
                            "LSMA": str(row[8]) if row[8] else "NÖTR",
                            "VMA": str(row[9]) if row[9] else "NÖTR",
                            "DURUM": str(row[15]) if row[15] else "NÖTR"
                        })
            
            all_data["endeksler"] = index_data
            print(f"   ✅ Endeksler: {len(index_data)} endeks")
        
        # 4. FON_EMTIA_COIN_DOVIZ SAYFASI - Önemli varlıklar
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            asset_data = []
            
            for row in ws.iter_rows(min_row=2, max_row=30, values_only=True):
                if row and row[0]:
                    sembol = str(row[0]).split()[0] if ' ' in str(row[0]) else str(row[0])
                    if sembol and sembol != "None":
                        asset_data.append({
                            "VARLIK": sembol,
                            "WT_SINYAL": str(row[1]) if row[1] else "NÖTR",
                            "CLOSE": float(str(row[6]).replace(',', '.')) if row[6] else 0,
                            "PIVOT": float(str(row[7]).replace(',', '.')) if row[7] else 0,
                            "LSMA": str(row[8]) if row[8] else "NÖTR",
                            "VMA": str(row[9]) if row[9] else "NÖTR",
                            "DURUM": str(row[15]) if row[15] else "NÖTR",
                            "AI_YORUM": str(row[32])[:80] if row[32] else ""
                        })
            
            all_data["varliklar"] = asset_data
            print(f"   ✅ Varlıklar: {len(asset_data)} varlık")
        
        wb.close()
        
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
        pivot_fark = ((h['CLOSE'] - h['PIVOT']) / h['PIVOT'] * 100) if h['PIVOT'] > 0 else 0
        signals_summary.append(
            f"{h['HISSE']}: {h['CLOSE']:.2f}TL | VMA: {h['VMA']} | WT: {h['WT_SINYAL']} | "
            f"Pivot: {h['PIVOT']:.2f} ({'+' if pivot_fark > 0 else '-'}{abs(pivot_fark):.1f}%)"
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
• VMA POZİTİF: {stats.get('vma_pozitif', 0)} hisse (%{int((stats.get('vma_pozitif', 0)/stats.get('toplam_hisse', 1))*100) if stats.get('toplam_hisse', 0) > 0 else 0})
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
        return "GROQ_API_KEY gerekli"
    
    system_prompt = create_ai_prompt(question, excel_data)
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mixtral-8x7b-32768",
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
            return f"API hatası: {response.status_code}"
            
    except Exception as e:
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
    return answer

if __name__ == "__main__":
    main()
