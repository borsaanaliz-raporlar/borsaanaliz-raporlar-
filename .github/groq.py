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

# GROQ API
api_key = os.environ.get('GROQ_API_KEY', '')
if not api_key:
    print("❌ Groq API anahtarı bulunamadı!")
    exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
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
    "model": "llama-3.1-8b-instant",  # Groq'un ücretsiz, hızlı modeli
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    "max_tokens": 1024,
    "temperature": 0.7,
    "stream": False
}

try:
    print("⚡ Groq'a bağlanıyor (Llama 3 8B)...")
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
        
        # Fallback
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(f"Sorunuz: '{question}'. Şu anda destek modundayım. Excel'in 3. sayfasına bakın.")
            
except Exception as e:
    print(f"❌ Hata: {str(e)}")
    
    with open('answer.txt', 'w', encoding='utf-8') as f:
        f.write("Teknik sorun. Lütfen iletisimborsaanaliz@gmail.com adresine yazın.")
