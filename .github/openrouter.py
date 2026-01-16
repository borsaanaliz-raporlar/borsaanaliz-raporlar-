import os
import json
import requests

# GitHub'dan gelen soruyu al
event_path = os.environ.get('GITHUB_EVENT_PATH', '')
if event_path and os.path.exists(event_path):
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    question = event_data.get('client_payload', {}).get('question', 'Merhaba')
else:
    question = "Merhaba, BORSAANALIZ V11 Excel raporu hakkında nasıl yardımcı olabilirim?"

print(f"🔍 Soru: {question}")

# OPENROUTER API
api_key = os.environ.get('OPENROUTER_API_KEY', '')
if not api_key:
    print("❌ OpenRouter API anahtarı bulunamadı!")
    exit(1)

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://borsaanaliz.com",
    "X-Title": "BORSAANALIZ V11"
}

# BORSAANALIZ SYSTEM PROMPT
system_prompt = """Sen BORSAANALIZ V11 Excel rapor asistanısın.

📊 EXCEL DOSYASI: BORSAANALIZ_V11_TAM_[TARIH].xlsm
9 SAYFA:
1. Genel Bakış
2. Sektör Analizi  
3. Teknik Göstergeler (RSI, MACD, Stokastik)
4. Mum Grafikleri
5. Hacim Analizi
6. Destek-Direnç
7. Trend Analizi
8. Volatilite
9. Özel Filtreler

Kullanıcılara Excel kullanımı, MACRO açma, teknik gösterge yorumlama konularında yardım et.
Türkçe, kısa, net, yardımsever ol.
Yatırım tavsiyesi VERME."""

data = {
    "model": "google/gemini-2.0-flash-exp:free",  # ÜCRETSİZ MODEL
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    "max_tokens": 800,
    "temperature": 0.7
}

try:
    print("🤖 OpenRouter'a bağlanıyor (Gemini 2.0 Flash)...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']
        print(f"✅ Yanıt: {answer[:200]}...")
        
        # Yanıtı dosyaya yaz
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(answer)
        
        print("📁 answer.txt dosyası oluşturuldu")
        
    else:
        print(f"❌ API hatası: {response.status_code}")
        print(f"📝 Hata: {response.text[:300]}")
        
        # Fallback: basit yanıt
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(f"Sorunuz alındı: '{question}'. Şu anda teknik destek modundayım. Lütfen Excel'in 3. sayfasına bakın.")
            
except Exception as e:
    print(f"❌ Hata: {str(e)}")
    
    with open('answer.txt', 'w', encoding='utf-8') as f:
        f.write("Teknik bir sorun oluştu. Lütfen iletisimborsaanaliz@gmail.com adresine yazın.")
