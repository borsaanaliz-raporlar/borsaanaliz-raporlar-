import os
import json
import requests
import time

# GitHub'dan gelen soruyu al
event_path = os.environ.get('GITHUB_EVENT_PATH', '')
if event_path and os.path.exists(event_path):
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    question = event_data.get('client_payload', {}).get('question', 'Merhaba')
else:
    question = "Merhaba, nasıl yardımcı olabilirim?"

print(f"🔍 Soru: {question}")

# Rate limit koruması - 1 saniye bekle
time.sleep(1)

# DEEPSEEK API
api_key = os.environ.get('DEEPSEEK_API_KEY', '')
if not api_key:
    print("❌ API anahtarı bulunamadı!")
    exit(1)

# DOĞRU ENDPOINT
url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "BORSAANALIZ-V11/1.0"
}

# KISA ve ÖZ SYSTEM PROMPT
system_prompt = """Sen BORSAANALIZ V11 Excel asistanısın. 
Excel'de 9 sayfa var: 1. Genel, 2. Sektör, 3. Teknik Göstergeler, 
4. Mumlar, 5. Hacim, 6. Destek-Direnç, 7. Trend, 8. Volatilite, 9. Filtreler.

Kısa ve net cevap ver. Max 3 cümle. Excel'de hangi sayfada olduğunu söyle."""

data = {
    "model": "deepseek-chat",  # Temel model
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    "max_tokens": 500,  # AZ TOKEN KULLAN
    "temperature": 0.7,
    "stream": False
}

try:
    print("🤖 DeepSeek'e bağlanıyor...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']
        print(f"✅ Yanıt: {answer[:150]}...")
        
        # Token kullanımı
        usage = result.get('usage', {})
        print(f"📈 Token kullanımı: {usage.get('total_tokens', 0)}")
        
        # Yanıtı dosyaya yaz
        with open('answer.txt', 'w', encoding='utf-8') as f:
            f.write(answer)
        
        print("📁 answer.txt dosyası oluşturuldu")
        
    elif response.status_code == 429:
        print("⚠️ Rate limit aşıldı! 60 saniye bekle...")
        time.sleep(60)
        print("⏳ Yeniden deniyor...")
        # Yeniden dene
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            with open('answer.txt', 'w', encoding='utf-8') as f:
                f.write(answer)
            print("✅ İkinci deneme başarılı!")
        else:
            print(f"❌ İkinci deneme de başarısız: {response.status_code}")
            raise Exception(f"API Error: {response.status_code}")
            
    else:
        print(f"❌ API hatası: {response.status_code}")
        print(f"📝 Hata detayı: {response.text[:200]}")
        
        # Alternatif model dene
        print("🔄 Alternatif model deneniyor...")
        data["model"] = "deepseek-reasoner"
        response2 = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response2.status_code == 200:
            answer = response2.json()['choices'][0]['message']['content']
            with open('answer.txt', 'w', encoding='utf-8') as f:
                f.write(answer)
            print("✅ Alternatif model çalıştı!")
        else:
            # Son çare: basit yanıt
            with open('answer.txt', 'w', encoding='utf-8') as f:
                f.write(f"Üzgünüm, teknik bir sorun var. Sorunuz: '{question}'. Lütfen daha sonra tekrar deneyin.")
            
except Exception as e:
    print(f"❌ Beklenmeyen hata: {str(e)}")
    import traceback
    traceback.print_exc()
    
    with open('answer.txt', 'w', encoding='utf-8') as f:
        f.write("Teknik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
