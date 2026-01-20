#!/usr/bin/env python3
"""
EXCEL OKUYAN AI ANALİZ SİSTEMİ - GERÇEK EXCEL YAPILI
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

def read_excel_summary():
    """Excel'den GERÇEK ve ÖZEL bilgileri çıkar"""
    excel_info = find_latest_excel()
    if not excel_info:
        return {"error": "Excel bulunamadı"}
    
    try:
        wb = load_workbook(excel_info['path'], data_only=True, read_only=True)
        
        # EXCEL'DEKİ GERÇEK SAYFALAR (TAM LİSTE)
        real_sheets = [
            "MENU", "Sinyaller", "DIP_YUKSELIS", "REGRESSION_ANALIZ", 
            "AI_SECIMLERI", "PIVOT_ANALIZ", "BISTTUM_TEORIK", "AL-SAT Seviyeleri", 
            "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ", "AI_MODEL_PORTFOY", 
            "KULLANIM_KILAVUZU", "AÇIKLAMALAR", "YASAL_UYARI"
        ]
        
        # Hangi sayfalar Excel'de VAR?
        existing_sheets = []
        for sheet in real_sheets:
            if sheet in wb.sheetnames:
                existing_sheets.append(sheet)
        
        wb.close()
        
        return {
            'success': True,
            'file': excel_info['name'],
            'date': excel_info['modified'].strftime('%d.%m.%Y'),
            'total_sheets': len(existing_sheets),
            'real_sheets': existing_sheets,  # SADECE GERÇEKTE OLAN SAYFALAR
            'all_sheets': wb.sheetnames
        }
        
    except Exception as e:
        return {"error": f"Okuma hatası: {str(e)}"}

def call_ai_with_excel(question, excel_summary):
    """Excel verileriyle AI çağır - GERÇEK YAPILI ve WT BİLEN"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY gerekli"
    
    # GERÇEK SAYFA AÇIKLAMALARI (WT = WAVE TREND)
    sheet_descriptions = {
        "MENU": "Ana menü ve navigasyon - Excel'in başlangıç sayfası",
        "Sinyaller": "Alım-satım sinyalleri, teknik göstergeler (WT - Wave Trend dahil)",
        "DIP_YUKSELIS": "Dip/Yükseliş tespitleri, destek/direnç seviyeleri",
        "REGRESSION_ANALIZ": "Regresyon analizi, istatistiksel tahminler, korelasyon",
        "AI_SECIMLERI": "AI seçimleri, önerilen hisseler, AI filtre sonuçları",
        "PIVOT_ANALIZ": "Pivot noktaları, 120 dakikalık/günlük/haftalık/aylık/yıllık/seviye analiz, pivot hesaplamaları",
        "BISTTUM_TEORIK": "BIST teorik eşleşme fiyatları, ertesi gün yükselebilecek hisseler, piyasa analizi",
        "AL-SAT Seviyeleri": "Alım-satım seviyeleri, kar satış, ek alım , stop seviyeleri, fiyat aralıkları",
        "ENDEKSLER": "Endeks analizleri (XU100, banka, sanayi vb. endeksler)",
        "FON_EMTIA_COIN_DOVIZ": "Fon, emtia, kripto, döviz analizleri, alternatif yatırım",
        "AI_MODEL_PORTFOY": "AI model portföy önerileri, portföy takibi,  risk dağılımı",
        "KULLANIM_KILAVUZU": "Excel kullanım kılavuzu, formül açıklamaları",
        "AÇIKLAMALAR": "Analiz açıklamaları, notlar, metodoloji",
        "YASAL_UYARI": "Yasal uyarılar, risk bildirimleri, sorumluluk reddi"
    }
    
    # Sadece var olan sayfalar için açıklama
    available_descriptions = []
    for sheet in excel_summary.get('real_sheets', []):
        if sheet in sheet_descriptions:
            available_descriptions.append(f"📌 {sheet}: {sheet_descriptions[sheet]}")
    
    # SYSTEM PROMPT - AI'nın BEYNİ
    system_prompt = f"""🎯 **SEN: BORSAANALIZ V11 EXCEL UZMAN ANALİSTİ**
Gerçek Excel dosyasını biliyorsun. SADECE GERÇEK veri ver.

📊 **EXCEL DOSYASI:**
• Dosya: {excel_summary.get('file', 'Bilinmiyor')}
• Tarih: {excel_summary.get('date', 'Bilinmiyor')}
• Sayfa: {excel_summary.get('total_sheets', 0)} gerçek analiz sayfası

🔍 **GERÇEK SAYFALAR ve İÇERİKLERİ:**
{chr(10).join(available_descriptions) if available_descriptions else "• Excel sayfaları yükleniyor..."}

⚠️ **WT (WAVE TREND) NOTU:**
Excel'de RSI YOK, onun yerine WT (Wave Trend) göstergesi var.
WT, RSI'ya benzer ama daha gelişmiş bir trend göstergesidir.
WT sinyalleri 'Sinyaller' sayfasında bulunur.

🚫 **KESİNLİKLE YASAK:**
1. Excel'de OLMAYAN sayfa ismi UYDURMA (Örnek: "Hisse Yorumları", "Hisseler" YOK)
2. "15. sayfa" gibi numara söyleme, SAYFA İSMİ söyle
3. Hayali bilgi VERME
4. Yatırım tavsiyesi VERME
5. "RSI" deme, "WT (Wave Trend)" de

✅ **DOĞRU YANIT FORMATI:**
"📌 [SAYFA_ADI] sayfasında: [SPESİFİK_BİLGİ] bulunur"
"⚠️ [İSTENEN_BİLGİ] Excel'de mevcut değil"
"💡 İlgili bilgi [SAYFA_ADI] sayfasında: [BENZER_BİLGİ]"

📝 **ÖRNEK SORU-YANITLAR:**
• Soru: "GMSTR hissesini yorumlar mısın?"
• Yanıt: "📌 GMSTR hissesi için 'AI_SECIMLERI' sayfasında AI önerilerine veya 'Sinyaller' sayfasında WT (Wave Trend) sinyallerine bakabilirsiniz."

• Soru: "RSI değerleri nerede?"
• Yanıt: "⚠️ Excel'de RSI yok. 📌 Onun yerine WT (Wave Trend) göstergesi 'Sinyaller' sayfasında bulunur."

• Soru: "Bugün öne çıkan hisseler?"
• Yanıt: "📌 'AI_SECIMLERI' sayfasında AI'nın önerdiği hisselere veya 'Sinyaller' sayfasında güçlü WT sinyali olan hisselere bakabilirsiniz."

• Soru: "Teknik analiz nasıl yapılır?"
• Yanıt: "📌 'Sinyaller' sayfasında WT göstergeleri, 'DIP_YUKSELIS' sayfasında destek/direnç, 'PIVOT_ANALIZ' sayfasında pivot seviyeleri bulunur."

Şimdi Kullanıcı Sorusu: "{question}"
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": 450,
        "temperature": 0.1,  # DÜŞÜK - daha tutarlı yanıtlar
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"API hatası: {response.status_code}"
    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Excel'de son durum nedir?"
    
    print("📖 Excel okunuyor...")
    excel_data = read_excel_summary()
    
    if "error" in excel_data:
        answer = f"⚠️ {excel_data['error']}"
    else:
        print("🤖 AI analiz ediyor...")
        answer = call_ai_with_excel(question, excel_data)
    
    # Yanıtı kaydet
    with open('ai_response.txt', 'w', encoding='utf-8') as f:
        f.write(answer)
    
    print("✅ Yanıt hazır!")
