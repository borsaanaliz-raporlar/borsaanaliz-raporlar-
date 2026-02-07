# /api/ask-direct.py (ENCODING DÜZELTİLMİŞ)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"API: {format%args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = json.dumps({
            "status": "online",
            "ai": "DeepSeek Chat",
            "endpoint": "POST {'question':'sorunuz'}",
            "charset": "utf-8"
        }, ensure_ascii=False)
        
        self.wfile.write(response.encode('utf-8'))
    
    def do_POST(self):
        try:
            # 1. Body'yi oku
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"AI Soru: {question}")
            
            # 2. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 3. Prompt
            prompt = f"""Borsa analiz uzmanı olarak cevapla: {question}

Kurallar:
1. VMA = Volume Moving Algorithm
2. RSI/MACD yok
3. Kısa ve net (max 150 kelime)
4. Yatırım tavsiyesi VERME

Cevap:"""
            
            # 4. API İsteği
            url = "https://api.deepseek.com/chat/completions"
            
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 400,
                "temperature": 0.1
            }
            
            json_data = json.dumps(request_data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz/1.0'
                }
            )
            
            # 5. Yanıtı al
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # Uyarı ekle
                if "yatırım tavsiyesi" not in answer.lower():
                    answer += "\n\n⚠️ **UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
                
                # 6. UTF-8 encoding ile yanıt ver
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                    "encoding": "utf-8"
                }, ensure_ascii=False)  # ← BU ÇOK ÖNEMLİ!
                
                self.wfile.write(result.encode('utf-8'))
                print(f"AI Yanıt: {len(answer)} karakter")
                
            else:
                raise Exception("API geçersiz yanıt")
                
        except Exception as e:
            print(f"AI Hata: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "error": str(e),
                "encoding": "utf-8"
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
