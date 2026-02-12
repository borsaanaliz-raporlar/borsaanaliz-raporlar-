#!/usr/bin/env python3
"""
BORSAANALİZ V11 UZMAN TEKNİK ANALİST
DeepSeek + Groq Hibrit - HİSSE LİSTESİ YOK, SAF REGEX!
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
    """Excel'deki TÜM verileri al - SADECE 3 SAYFA"""
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
                
                # Verileri al (satır 2-500)
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
    """
    🎯 HİSSE ADI BULUCU - LİSTE YOK, SAF REGEX!
    3-8 karakter, büyük harf, rakam içerebilir
    """
    words = re.findall(r'\b[A-Z0-9]{3,8}\b', question.upper())
    
    # İlk kelimeyi döndür, yoksa None
    return words[0] if words else None

def create_expert_analysis_prompt(question, excel_data, hisse_adi=None):
    """PROFESYONEL BORSAANALİZ V11 UZMANI - SADECE GERÇEK VERİLER"""
    
    timestamp = excel_data["timestamp"]
    data = excel_data["data"]
    
    # ============= BORSAANALİZ V11 SİSTEM TANITIMI =============
    system_intro = f"""🎯 **SEN: BORSAANALİZ V11 UZMAN TEKNİK ANALİST**
📊 **Excel tabanlı profesyonel analiz sistemi - 100+ gösterge**
📅 **Rapor Tarihi:** {timestamp}

═══════════════════════════════════════════
**📌 BORSAANALİZ V11 TEKNİK GÖSTERGELER:**

1️⃣ **WT (WaveTrend):** Aşırı alım/satım göstergesi (-100/+100 arası)
   • POZİTİF = Alım bölgesinden çıkış
   • NEGATİF = Satım bölgesinden çıkış

2️⃣ **VMA (Volume Moving Algorithm):** %94 DOĞRULUK!
   • POZİTİF(21) = 21 gündür yükselen hacim trendi
   • NEGATİF(07) = 7 gündür düşen hacim trendi
   • Parantez içi = Trendin devam ettiği GÜN SAYISI

3️⃣ **LSMA KAMA:** Least Squares Moving Average + Kaufman
   • POZİTİF(15) = 15 gündür yükseliş trendi
   • NEGATİF(08) = 8 gündür düşüş trendi
   • Parantez içi = Trendin devam ettiği GÜN SAYISI

4️⃣ **REGRESYON KANALLARI:** Pearson55/89/144/233
   • > 0.30 = GÜÇLÜ YÜKSELİŞ TRENDİ
   • < -0.30 = GÜÇLÜ DÜŞÜŞ TRENDİ
   • 0.10 ile 0.30 arası = ZAYIF YÜKSELİŞ
   • -0.10 ile -0.30 arası = ZAYIF DÜŞÜŞ
   • -0.10 ile 0.10 arası = YATAY/BELİRSİZ

5️⃣ **BOLLINGER BANTLARI (BB):** Volatilite göstergesi
   • Fiyat > Üst Bant = AŞIRI ALIM (düzeltme gelebilir)
   • Fiyat < Alt Bant = AŞIRI SATIM (tepki alımı gelebilir)
   • Fiyat bantlar içinde = NORMAL BÖLGE

6️⃣ **EMA HİYERARŞİSİ:** 8/13/21/34/55/89/144/233
   • 8 > 13 > 21 = KISA VADELİ YÜKSELİŞ TRENDİ
   • 8 < 13 < 21 = KISA VADELİ DÜŞÜŞ TRENDİ

7️⃣ **HACİM SENARYOLARI:**
   • POZITIF_YUKSELME = Hacim artışıyla yükseliş (GÜVENİLİR)
   • NEGATIF_DUSUS = Hacim düşüşüyle düşüş (GÜVENİLİR)
   • POZITIF_DUSUS = Hacim artışıyla düşüş (SATIŞ BASKISI)
   • NEGATIF_YUKSELME = Hacim düşüşüyle yükseliş (ZAYIF)

**🚫 BU SİSTEMDE KESİNLİKLE YOK:**
• RSI (Relatif Güç Endeksi)
• MACD (Moving Average Convergence Divergence)
• Stokastik (Stochastic Oscillator)
• Ichimoku Bulutları
• Fibonacci Düzeltmeleri
• ADX, CCI, Williams %R

**⚠️ BU GÖSTERGELERDEN ASLA BAHSETME, YORUMLAMA, KULLANMA!**
═══════════════════════════════════════════
"""
    
    # HİSSE ANALİZİ
    if hisse_adi:
        hisse_info = None
        sheet_name = None
        sheet_headers = None
        
        for sname, sinfo in data.items():
            for hisse in sinfo["data"]:
                hisse_name = hisse.get(sinfo["headers"][0], "")
                if hisse_name and hisse_adi.upper() in str(hisse_name).upper():
                    hisse_info = hisse
                    sheet_name = sname
                    sheet_headers = sinfo["headers"]
                    break
            if hisse_info:
                break
        
        if hisse_info:
            # === TÜM VERİLERİ ÇEK ===
            close = hisse_info.get("Close", "?")
            pivot = hisse_info.get("Pivot", "?")
            wt_sinyal = hisse_info.get("WT Sinyal", "?")
            wt1 = hisse_info.get("WT1", "?")
            wt2 = hisse_info.get("WT2", "?")
            
            # VMA - GÜN SAYISI AYRIŞTIR
            vma = hisse_info.get("VMA trend algo", "?")
            vma_raw = str(vma)
            vma_durum = "NÖTR"
            vma_gun = "0"
            if "POZİTİF" in vma_raw:
                vma_durum = "POZİTİF"
                vma_gun = re.findall(r'\d+', vma_raw)
                vma_gun = vma_gun[0] if vma_gun else "0"
            elif "NEGATİF" in vma_raw:
                vma_durum = "NEGATİF"
                vma_gun = re.findall(r'\d+', vma_raw)
                vma_gun = vma_gun[0] if vma_gun else "0"
            
            # LSMA - GÜN SAYISI AYRIŞTIR
            lsma = hisse_info.get("LSMA KAMA", "?")
            lsma_raw = str(lsma)
            lsma_durum = "NÖTR"
            lsma_gun = "0"
            if "POZİTİF" in lsma_raw:
                lsma_durum = "POZİTİF"
                lsma_gun = re.findall(r'\d+', lsma_raw)
                lsma_gun = lsma_gun[0] if lsma_gun else "0"
            elif "NEGATİF" in lsma_raw:
                lsma_durum = "NEGATİF"
                lsma_gun = re.findall(r'\d+', lsma_raw)
                lsma_gun = lsma_gun[0] if lsma_gun else "0"
            
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
            
            # PEARSON
            p55 = hisse_info.get("Pearson55", "0")
            p89 = hisse_info.get("Pearson89", "0")
            p144 = hisse_info.get("Pearson144", "0")
            p233 = hisse_info.get("Pearson233", "0")
            
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
            
            # AI YORUM (Excel'den)
            ai_yorum = hisse_info.get("AI_YORUM", "")
            
            # ============= PROFESYONEL ANALİZ PROMPT'U =============
            prompt = system_intro + f"""

═══════════════════════════════════════════
📋 **ANALİZ RAPORU: {hisse_adi}**
📌 **Kaynak:** {sheet_name} sayfası
═══════════════════════════════════════════

## 📈 **1. GENEL GÖRÜNÜM**

| Gösterge | Değer | Yorum |
|----------|-------|-------|
| **Fiyat** | {close} TL | - |
| **Pivot** | {pivot} TL | {'Pivot üstü = POZİTİF' if str(close).replace(',','.').replace('?','0') > str(pivot).replace(',','.').replace('?','0') else 'Pivot altı = NEGATİF'} |
| **WT Sinyal** | {wt_sinyal} | WT1: {wt1}, WT2: {wt2} |
| **LSMA Trend** | {lsma_durum} | **{lsma_gun} gündür** {lsma_durum} |
| **VMA Trend** | {vma_durum} | **{vma_gun} gündür** {vma_durum} (doğruluk %94) |
| **HMA_89** | {hma89} TL | {'Fiyat üzerinde = DESTEK' if str(close).replace(',','.').replace('?','0') > str(hma89).replace(',','.').replace('?','0') else 'Fiyat altında = DİRENÇ'} |

**📊 Excel AI Özeti:** {ai_yorum}

═══════════════════════════════════════════

## 🎯 **2. DESTEK VE DİRENÇ SEVİYELERİ**

| Seviye | Değer | Anlamı |
|--------|-------|--------|
| **S3** | {s3} | Güçlü destek (son kale) |
| **S2** | {s2} | Orta vadeli destek |
| **S1** | {s1} | Kısa vadeli destek |
| **PİVOT** | {pivot} | Dönüm noktası |
| **R1** | {r1} | Kısa vadeli direnç |
| **R2** | {r2} | Orta vadeli direnç |
| **R3** | {r3} | Güçlü direnç (hedef) |

**📊 PİVOT ANALİZİ:**
"""
            # Pivot analizi
            try:
                close_f = float(str(close).replace(',', '.'))
                pivot_f = float(str(pivot).replace(',', '.'))
                if close_f > pivot_f:
                    prompt += f"✅ **POZİTİF:** Fiyat pivot seviyesinin **ÜSTÜNDE** (+%{((close_f-pivot_f)/pivot_f*100):.2f})\n"
                else:
                    prompt += f"⚠️ **NEGATİF:** Fiyat pivot seviyesinin **ALTINDA** (-%{((pivot_f-close_f)/pivot_f*100):.2f})\n"
            except:
                prompt += "ℹ️ Pivot karşılaştırması yapılamadı\n"

            prompt += f"""

═══════════════════════════════════════════

## 📊 **3. EMA HİYERARŞİSİ ANALİZİ**

| EMA | Değer | Trend Yorumu |
|-----|-------|--------------|
| **EMA 8** | {ema8} | Kısa vadeli (1-3 gün) |
| **EMA 13** | {ema13} | Kısa vadeli (3-5 gün) |
| **EMA 21** | {ema21} | Orta vadeli (1 ay) |
| **EMA 34** | {ema34} | Orta vadeli (1.5 ay) |
| **EMA 55** | {ema55} | Orta vadeli (2.5 ay) |
| **EMA 89** | {ema89} | Uzun vadeli (4 ay) |
| **EMA 144** | {ema144} | Uzun vadeli (6 ay) |
| **EMA 233** | {ema233} | Ana trend (1 yıl) |

**📈 EMA HİYERARŞİSİ YORUMU:**
"""
            # EMA hiyerarşisi analizi
            try:
                close_f = float(str(close).replace(',', '.'))
                ema8_f = float(str(ema8).replace(',', '.')) if ema8 != '?' else 0
                ema13_f = float(str(ema13).replace(',', '.')) if ema13 != '?' else 0
                ema21_f = float(str(ema21).replace(',', '.')) if ema21 != '?' else 0
                
                # Fiyatın EMA'lara göre konumu
                if close_f > ema8_f:
                    prompt += f"✅ **Fiyat > EMA8:** Kısa vadeli trend POZİTİF\n"
                else:
                    prompt += f"⚠️ **Fiyat < EMA8:** Kısa vadeli trend NEGATİF\n"
                
                # EMA hiyerarşisi
                if ema8_f > ema13_f > ema21_f:
                    prompt += f"✅ **EMA HİYERARŞİSİ:** 8 > 13 > 21 = **GÜÇLÜ YÜKSELİŞ TRENDİ**\n"
                elif ema8_f < ema13_f < ema21_f:
                    prompt += f"⚠️ **EMA HİYERARŞİSİ:** 8 < 13 < 21 = **GÜÇLÜ DÜŞÜŞ TRENDİ**\n"
                else:
                    prompt += f"ℹ️ **EMA HİYERARŞİSİ:** Karmaşık = **YATAY/BELİRSİZ**\n"
            except:
                pass

            prompt += f"""

═══════════════════════════════════════════

## 📉 **4. REGRESYON KANAL ANALİZİ (PEARSON)**

| Periyot | Pearson | Trend | Güç |
|---------|---------|-------|-----|
| **55 Gün** | {p55} | { 'YÜKSELİŞ' if str(p55).replace(',','.').replace('?','0') > '0.3' else 'DÜŞÜŞ' if str(p55).replace(',','.').replace('?','0') < '-0.3' else 'YATAY' } | { 'GÜÇLÜ' if abs(float(str(p55).replace(',','.').replace('?','0'))) > 0.7 else 'ORTA' if abs(float(str(p55).replace(',','.').replace('?','0'))) > 0.3 else 'ZAYIF' } |
| **89 Gün** | {p89} | { 'YÜKSELİŞ' if str(p89).replace(',','.').replace('?','0') > '0.3' else 'DÜŞÜŞ' if str(p89).replace(',','.').replace('?','0') < '-0.3' else 'YATAY' } | - |
| **144 Gün** | {p144} | { 'YÜKSELİŞ' if str(p144).replace(',','.').replace('?','0') > '0.3' else 'DÜŞÜŞ' if str(p144).replace(',','.').replace('?','0') < '-0.3' else 'YATAY' } | - |
| **233 Gün** | {p233} | { 'YÜKSELİŞ' if str(p233).replace(',','.').replace('?','0') > '0.3' else 'DÜŞÜŞ' if str(p233).replace(',','.').replace('?','0') < '-0.3' else 'YATAY' } | - |

═══════════════════════════════════════════

## 📊 **5. BOLLINGER BANTLARI**

| Bant | Değer | Anlamı |
|------|-------|--------|
| **Üst Bant** | {bb_upper} | Aşırı alım bölgesi |
| **Orta Bant** | {bb_middle} | 20 günlük basit ortalama |
| **Alt Bant** | {bb_lower} | Aşırı satım bölgesi |

**📊 BOLLINGER YORUMU:**
"""
            # Bollinger yorumu
            try:
                close_f = float(str(close).replace(',', '.'))
                bb_upper_f = float(str(bb_upper).replace(',', '.')) if bb_upper != '?' else 0
                bb_lower_f = float(str(bb_lower).replace(',', '.')) if bb_lower != '?' else 0
                
                if close_f > bb_upper_f:
                    prompt += f"⚠️ **AŞIRI ALIM:** Fiyat üst bandın ÜZERİNDE - Düzeltme riski yüksek\n"
                elif close_f < bb_lower_f:
                    prompt += f"✅ **AŞIRI SATIM:** Fiyat alt bandın ALTINDA - Tepki alımı gelebilir\n"
                else:
                    prompt += f"ℹ️ **NORMAL:** Fiyat bantlar içinde - Volatilite normal seviyede\n"
            except:
                pass

            prompt += f"""

═══════════════════════════════════════════

## 💰 **6. HACİM ANALİZİ**

| Gösterge | Değer | Yorum |
|----------|-------|-------|
| **Hacim** | {hacim} | Son gün işlem hacmi |
| **Hacim Değişim** | {hacim_degisim} | Önceki güne göre değişim |
| **Hacim Senaryo** | {hacim_senaryo} | Trend-hacim ilişkisi |

**📊 HACİM YORUMU:**
"""
            hacim_senaryo_str = str(hacim_senaryo)
            if "POZITIF_YUKSELME" in hacim_senaryo_str:
                prompt += f"✅ **GÜVENİLİR YÜKSELİŞ:** Hacim artışıyla yükseliş - Trend sağlıklı\n"
            elif "NEGATIF_DUSUS" in hacim_senaryo_str:
                prompt += f"✅ **GÜVENİLİR DÜŞÜŞ:** Hacim düşüşüyle düşüş - Satış baskısı azalıyor\n"
            elif "POZITIF_DUSUS" in hacim_senaryo_str:
                prompt += f"⚠️ **SATIŞ BASKISI:** Hacim artışıyla düşüş - Panik satışı olabilir\n"
            elif "NEGATIF_YUKSELME" in hacim_senaryo_str:
                prompt += f"⚠️ **ZAYIF YÜKSELİŞ:** Hacim düşüşüyle yükseliş - Güven sorunu\n"

            prompt += f"""

═══════════════════════════════════════════

## 🎯 **7. VMA (VOLUME MOVING ALGORITHM)**

| Gösterge | Değer | Anlamı |
|----------|-------|--------|
| **VMA Sinyal** | {vma_durum} | **{vma_gun} gündür** {vma_durum} trendde |
| **Doğruluk** | %94 | Backtest sonucu |

**📊 VMA YORUMU:**
"""
            if vma_durum == "POZİTİF":
                prompt += f"✅ **POZİTİF VMA:** Hacim trendi {vma_gun} gündür YÜKSELİYOR - Alım baskısı devam ediyor\n"
                prompt += f"   📌 Bu sinyal %94 doğrulukla güvenilirdir.\n"
            elif vma_durum == "NEGATİF":
                prompt += f"⚠️ **NEGATİF VMA:** Hacim trendi {vma_gun} gündür DÜŞÜYOR - Satış baskısı azalıyor\n"
                prompt += f"   📌 Bu sinyal %94 doğrulukla güvenilirdir.\n"

            prompt += f"""

═══════════════════════════════════════════

## 📋 **8. TEKNİK ANALİZ SONUÇ ve ÖZET**

**Soru:** {question}

**{hisse_adi} İÇİN PROFESYONEL DEĞERLENDİRME:**

Lütfen yukarıdaki TÜM teknik göstergeleri kullanarak:

1️⃣ **KISA VADELİ GÖRÜNÜM** (1-5 gün)
   • WT sinyali, EMA8/21, VMA trendi, hacim senaryosu
   • Hızlı hareket beklentisi, destek/direnç seviyeleri

2️⃣ **ORTA VADELİ GÖRÜNÜM** (1-4 hafta)
   • Pearson55/89, EMA55/89, LSMA trend süresi
   • Ana trend yönü ve gücü

3️⃣ **KRİTİK SEVİYELER**
   • S1-R1 aralığı (günlük hareket bandı)
   • S3-R3 seviyeleri (stop-loss/hedef bölgeleri)

4️⃣ **HACİM ONAYI**
   • VMA trendi ve gün sayısı
   • Hacim senaryosu analizi

5️⃣ **RİSK DEĞERLENDİRMESİ**
   • Düşük/Orta/Yüksek
   • Nedenleriyle açıkla

**⚠️ ÖNEMLİ UYARILAR:**
• Bu analiz **BORSAANALİZ V11** Excel verilerine dayanmaktadır
• **RSI, MACD, Stokastik** gibi göstergeler KULLANILMAMIŞTIR
• Parantez içindeki rakamlar trendin **KAÇ GÜNDÜR** devam ettiğini gösterir
• Bu analiz **YATIRIM TAVSİYESİ DEĞİLDİR**

**ŞİMDİ {hisse_adi} İÇİN DETAYLI TEKNİK ANALİZ YAP:**
"""
            return prompt
    
    # ============= GENEL PİYASA ANALİZİ =============
    prompt = system_intro + f"""

═══════════════════════════════════════════
📋 **PİYASA GENEL ANALİZ RAPORU**
═══════════════════════════════════════════

## 📈 **ELİMDEKİ VERİLER:**

"""
    for sheet_name, sheet_info in data.items():
        prompt += f"""
### 📊 {sheet_name} SAYFASI
• **Hisse/Endeks Sayısı:** {sheet_info['count']}
• **Teknik Göstergeler:** WT, Pivot, LSMA, VMA, HMA, EMA(8-233)
• **Regresyon:** Pearson55/89/144/233
• **Bollinger:** BB_UPPER/MIDDLE/LOWER
• **Hacim:** Hacim, Değişim %, Senaryo
"""

    prompt += f"""

═══════════════════════════════════════════

**Soru:** {question}

**PROFESYONEL ANALİZ TALİMATI:**

Yukarıdaki BORSAANALİZ V11 verilerine dayanarak:

1️⃣ **Piyasa Genel Görünümü**
   • Endekslerin (XU100, XU030, XBANK) teknik durumu
   • WT sinyalleri, pivot seviyeleri, EMA hiyerarşisi

2️⃣ **Öne Çıkan Hisseler**
   • VMA trendi POZİTİF olanlar (gün sayısı ile)
   • LSMA trendi POZİTİF olanlar (gün sayısı ile)
   • Pearson55 > 0.30 olanlar

3️⃣ **Sektörel Değerlendirme**
   • ENDEKLER sayfasındaki sektör endeksleri
   • En güçlü/en zayıf endeksler

4️⃣ **Risk İştahı**
   • POZITIF_YUKSELME hacim senaryosu oranı
   • NEGATIF_DUSUS hacim senaryosu oranı

**⚠️ ÖNEMLİ UYARI:**
• Bu analiz **yatırım tavsiyesi değildir**
• **RSI, MACD** gibi göstergeler KULLANILMAMIŞTIR
• Parantez içindeki rakamlar **trend gün sayısıdır**

**ŞİMDİ ANALİZ YAP:**
"""
    return prompt

def call_deepseek(prompt, question):
    """DeepSeek AI çağrısı - ÖNCELİKLİ"""
    if not DEEPSEEK_API_KEY:
        print("⚠️ DeepSeek API anahtarı yok")
        return None
    
    try:
        print("🚀 DeepSeek AI deneniyor...")
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
            timeout=30   # ⚡ 60'tan 30'a düşür!
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # YASAKLI KELİME KONTROLÜ
            answer = answer.replace("RSI", "⚠️ RSI (Bu gösterge BORSAANALİZ V11'de YOKTUR)")
            answer = answer.replace("MACD", "⚠️ MACD (Bu gösterge BORSAANALİZ V11'de YOKTUR)")
            answer = answer.replace("Stokastik", "⚠️ Stokastik (Bu gösterge BORSAANALİZ V11'de YOKTUR)")
            answer = answer.replace("stochastic", "⚠️ stochastic (Not available in BORSAANALİZ V11)")
            
            if "yatırım tavsiyesi" not in answer.lower():
                answer += "\n\n⚠️ **YASAL UYARI:** Bu analiz BORSAANALİZ V11 Excel verilerine dayanmaktadır ve yatırım tavsiyesi değildir."
            
            return answer
        else:
            print(f"⚠️ DeepSeek hata {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ DeepSeek bağlantı hatası: {str(e)}")
        return None

def call_groq(prompt, question):
    """Groq AI çağrısı - YEDEK"""
    if not GROQ_API_KEY:
        print("⚠️ Groq API anahtarı yok")
        return None
    
    try:
        print("⚡ Groq AI deneniyor...")
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
            answer = response.json()['choices'][0]['message']['content']
            
            # YASAKLI KELİME KONTROLÜ
            answer = answer.replace("RSI", "⚠️ RSI (Bu gösterge BORSAANALİZ V11'de YOKTUR)")
            answer = answer.replace("MACD", "⚠️ MACD (Bu gösterge BORSAANALİZ V11'de YOKTUR)")
            
            if "yatırım tavsiyesi" not in answer.lower():
                answer += "\n\n⚠️ **YASAL UYARI:** Bu analiz BORSAANALİZ V11 Excel verilerine dayanmaktadır ve yatırım tavsiyesi değildir."
            
            return answer
        else:
            print(f"⚠️ Groq hata {response.status_code}")
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
    
    # Excel bul
    print("🔍 Excel dosyası aranıyor...")
    excel_info = find_latest_excel()
    
    if not excel_info:
        print("❌ Excel dosyası bulunamadı!")
        answer = "⚠️ Üzgünüm, Excel dosyası bulunamadı. Lütfen raporlar/ klasörünü kontrol edin."
        
        with open('ai_response.txt', 'w', encoding='utf-8') as f:
            f.write(answer)
        return
    
    print(f"📁 Excel: {excel_info['name']}")
    
    # Excel verilerini oku
    excel_data = get_excel_data_for_ai(excel_info['path'])
    
    if "error" in excel_data:
        answer = f"❌ {excel_data['error']}"
    else:
        # HİSSE LİSTESİ YOK - SAF REGEX!
        hisse_adi = extract_hisse_adi(question)
        
        if hisse_adi:
            print(f"🎯 Hisse tespit edildi: {hisse_adi}")
        else:
            print("📊 Genel piyasa analizi yapılıyor...")
        
        # Prompt oluştur
        prompt = create_expert_analysis_prompt(question, excel_data, hisse_adi)
        
        # ÖNCE DEEPSEEK
        answer = call_deepseek(prompt, question)
        
        # DeepSeek çalışmazsa GROQ
        if not answer:
            print("⚠️ DeepSeek çalışmadı, Groq deneniyor...")
            answer = call_groq(prompt, question)
        
        # İkisi de çalışmazsa FALLBACK
        if not answer:
            answer = f"""⚠️ **AI SERVİSLERİNE ULAŞILAMADI**

**BORSAANALİZ V11 VERİLERİ:**

📁 Excel: {excel_info['name']}
📅 Tarih: {excel_data['timestamp']}

"""
            if hisse_adi:
                answer += f"\n🎯 **{hisse_adi}** hissesi için veriler Excel'de mevcut.\n"
                answer += "Lütfen API anahtarlarını kontrol edin:\n"
                answer += "• DEEPSEEK_API_KEY\n"
                answer += "• GROQ_API_KEY\n"
            else:
                answer += "📊 Genel piyasa analizi için veriler hazır.\n"
    
    # Yanıtı kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print(f"\n✅ ANALİZ TAMAMLANDI!")
    print(f"📝 Yanıt kaydedildi: ai_response.txt")
    print(f"📏 Yanıt uzunluğu: {len(answer)} karakter")

if __name__ == "__main__":
    main()
