#!/usr/bin/env python3
"""
BORSAANALIZ - DİREKT AI API (HIZLI YANIT)
Adım 1: Sadece temel direkt API
"""
import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# API Key - Vercel'den al
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

@app.route('/api/ask-direct', methods=['POST'])
def ask_direct():
    """Direkt AI sorusu - BASİT VERSİYON"""
    try:
        # 1. Soruyu al
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Soru gerekli"}), 400
        
        print(f"🤖 Direkt soru: {question[:50]}...")
        
        # 2. Basit prompt hazırla
        prompt = f"""🎯 BORSA ANALİZ ASİSTANI

KULLANICI SORUSU: {question}

KURALLAR:
1. Borsa analiz uzmanısın
2. VMA = Volume Moving Algorithm (ASLA Volkswagen deme)
3. RSI/MACD yok, onlardan bahsetme
4. Max 300 kelime
5. Yatırım tavsiyesi VERME

CEVAP FORMATI:
• Teknik analiz
• Risk faktörleri
• Genel değerlendirme

CEVAP:"""
        
        # 3. DeepSeek'e sor
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 800,
                "temperature": 0.1
            },
            timeout=30  # 30 saniye timeout
        )
        
        # 4. Yanıtı işle
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            
            # Uyarı ekle
            if "yatırım tavsiyesi değildir" not in answer.lower():
                answer += "\n\n⚠️ **UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
            
            return jsonify({
                "success": True,
                "answer": answer,
                "response_time": "anlık",
                "model": "deepseek-chat"
            })
        else:
            error_msg = f"API hatası: {response.status_code}"
            print(f"❌ {error_msg}")
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        error_msg = f"Sistem hatası: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/direct-health', methods=['GET'])
def health_check():
    """Sağlık kontrolü"""
    return jsonify({
        "status": "online",
        "service": "direct-ai-api",
        "timestamp": "2025-02-07T10:00:00Z"
    })

if __name__ == '__main__':
    app.run(debug=True)
