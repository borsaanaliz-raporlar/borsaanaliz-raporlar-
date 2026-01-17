#!/usr/bin/env python3
"""
EXCEL OKUYAN AI ANALİZ SİSTEMİ
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
    """Excel'den özet bilgileri çıkar"""
    excel_info = find_latest_excel()
    if not excel_info:
        return {"error": "Excel bulunamadı"}
    
    try:
        wb = load_workbook(excel_info['path'], data_only=True, read_only=True)
        sheets = wb.sheetnames
        
        # Önemli sayfaları kontrol et
        sheet_data = {}
        for sheet in ['Genel Bakış', 'Sektör Analizi', 'Teknik Göstergeler']:
            if sheet in sheets:
                ws = wb[sheet]
                sheet_data[sheet] = {
                    'rows': ws.max_row,
                    'cols': ws.max_column,
                    'has_data': ws.max_row > 1
                }
        
        wb.close()
        
        return {
            'success': True,
            'file': excel_info['name'],
            'date': excel_info['modified'].strftime('%d.%m.%Y'),
            'sheets': len(sheets),
            'sheet_data': sheet_data,
            'analyzed_sheets': list(sheet_data.keys())
        }
        
    except Exception as e:
        return {"error": f"Okuma hatası: {str(e)}"}

def call_ai_with_excel(question, excel_summary):
    """Excel verileriyle AI çağır"""
    if not GROQ_API_KEY:
        return "GROQ_API_KEY gerekli"
    
    system_prompt = f"""Sen BORSAANALIZ Excel raporlarının UZMAN ANALİSTİSİN.

📊 GERÇEK EXCEL BİLGİLERİ:
• Dosya: {excel_summary.get('file', 'Bilinmiyor')}
• Tarih: {excel_summary.get('date', 'Bilinmiyor')}
• Sayfa: {excel_summary.get('sheets', 0)} analiz sayfası
• Analiz edilen: {', '.join(excel_summary.get('analyzed_sheets', []))}

🎯 GÖREV:
1. Kullanıcının sorusunu Excel bağlamında yanıtla
2. Hangi sayfada ne olduğunu söyle
3. Pratik Excel kullanım ipuçları ver
4. MAX 5 cümle, net ve yardımcı ol

💡 FORMAT:
"Excel Tarihi: [TARİH]"
"[YANIT]"
"📊 Excel'de [SAYFA] sayfasında [NEREDE] bakabilirsiniz"

🚫 YAPMA:
• Excel'de olmayan verileri uydurma
• Yatırım tavsiyesi verme
• Çok teknik jargon kullanma"""
    
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
        "max_tokens": 500,
        "temperature": 0.3,
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
