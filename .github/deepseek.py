import os
import json
import requests
from datetime import datetime

# GitHub'dan gelen soruyu al
event_path = os.environ.get('GITHUB_EVENT_PATH', '')
if event_path and os.path.exists(event_path):
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    question = event_data.get('client_payload', {}).get('question', 'Merhaba')
else:
    question = "Merhaba, nasıl yardımcı olabilirim?"

print(f"🔍 Soru: {question}")

# DEEPSEEK API
api_key = os.environ.get('DEEPSEEK_API_KEY', '')
if not api_key:
    print("❌ API anahtarı bulunamadı!")
    exit(1)

url = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# SYSTEM PROMPT - BORSAANALIZ V11 UZMANI
system_prompt = """
Sen BORSAANALIZ V11 Excel raporlarının uzman asistanısın.

📁 MEVCUT DOSYALAR (sitede görünen):
1. BORSAANALIZ_V11_TAM_15012026.xlsm - 15 Ocak 2026 (EN GÜNCEL)
2. BORSAANALIZ_V11_TAM_14012026.xlsm - 14 Ocak 2026
3. BORSAANALIZ_V11_TAM_13012026.xlsm - 13 Ocak 2026
4. BORSAANALIZ_V11_TAM_12012026.xlsm - 12 Ocak 2026
5. BORSAANALIZ_V11_TAM_09012026.xlsm - 09 Ocak 2026

📊 EXCEL'DE 9 SAYFA:
1. GENEL BAKIŞ - Piyasa özeti, endeksler
2. SEKTÖR ANALİZİ - 28 sektör performansı
3. TEKNİK GÖSTERGELER - RSI, MACD, Stokastik, CCI, Bollinger
4. MUM GRAFİKLERİ - Günlük/Haftalık/Aylık
5. HACİM ANALİZİ - Hacim trendleri, anormal hacim
6. DESTEK-DİRENÇ - Fibonacci, Pivot, önemli seviyeler
7. TREND ANALİZİ - MA'lar, trend çizgileri
8. VOLATİLİTE - ATR, Beta, standart sapma
9. ÖZEL FİLTRELER - Kişisel stratejiler, özel taramalar

💡 YANIT FORMATI:
1. Soruyu anladığını belirt
2. Hangi Excel sayfasında olduğunu söyle (örn: "3. sayfada RSI...")
3. Pratik adımlar ver
4. Excel'deki konumunu belirt (sütun, satır)
5. Türkçe, net, yardımsever ol

🚫 YAPMA: Yatırım tavsiyesi verme, kesin öngörüde bulunma.
"""

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    "max_tokens": 1500,
    "temperature": 0.7
}

try:
    print("🤖 DeepSeek'e bağlanıyor...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    if response.status_code == 200:
        answer = response.json()['choices'][0]['message']['content']
        print(f"✅ Yanıt: {answer[:200]}...")
        
        # Yanıtı dosyaya yaz
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(answer)
        
        print("📁 answer.txt dosyası oluşturuldu")
    else:
        print(f"❌ API hatası: {response.status_code}")
        print(response.text)
        
        # Hata durumunda basit yanıt
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(f"Üzgünüm, şu anda teknik bir sorun var. Sorunuz: '{question}'")
            
except Exception as e:
    print(f"❌ Hata: {str(e)}")
    with open('answer.txt', 'w', encoding='utf-8') as f:
        f.write("Teknik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
