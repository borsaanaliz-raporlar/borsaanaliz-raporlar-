# /api/ask-direct.py (SON VERSİYON - DEEPSEEK EKLİ)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import ssl

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = json.dumps({
            "status": "online",
            "message": "BorsaAnaliz Direct API v2.0",
            "ai": "DeepSeek Chat entegre",
            "usage": "POST {'question': 'sorunuz'}",
            "example": "FROTO teknik analizi"
        })
        
        self.wfile.write(response.encode())
    
    def do_POST(self):
        """DeepSeek ile AI analizi"""
        try:
            # 1. Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                self.send_error(400, "Body boş")
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"🤖 Soru: {question}")
            
            # 2. API Key kontrolü
            api_key = os.environ.get('DEEPSEEK_API_KEY', '')
            if not api_key:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    "success": False,
                    "error": "DEEPSEEK_API_KEY eksik",
                    "help": "Vercel Environment Variables'a ekleyin"
                })
                self.wfile.write(response.encode())
                return
            
            # 3. Prompt hazırla
            prompt = f"""🎯 BORSA ANALİZ UZMANI

KULLANICI SORUSU: {question}

TALİMATLAR:
1. Borsa analiz uzmanı olarak cevap ver
2. VMA = Volume Moving Algorithm (ASLA Volkswagen deme)
3. Excel'de RSI/MACD yok, onlardan bahsetme
4. Kısa ve net cevap (max 200 kelime)
5. Yatırım tavsiyesi VERME

FORMAT:
• 📊 Analiz
• ⚠️ Riskler
• 💡 Öneri

CEVAP:"""
            
            # 4. DeepSeek API çağrısı
            url = "https://api.deepseek.com/chat/completions"
            
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 600,
                "temperature": 0.1,
                "stream": False
            }
            
            # 5. Request gönder
            json_data = json.dumps(request_data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz/1.0'
                },
                method='POST'
            )
            
            # SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # 6. Yanıtı al
            with urllib.request.urlopen(req, context=context, timeout=30) as api_response:
                response_data = json.loads(api_response.read().decode('utf-8'))
                
                if 'choices' in response_data and response_data['choices']:
                    answer = response_data['choices'][0]['message']['content']
                    
                    # Uyarı ekle
                    if "yatırım tavsiyesi değildir" not in answer.lower():
                        answer += "\n\n⚠️ **ÖNEMLİ UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
                    
                    # Başarılı yanıt
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    result = json.dumps({
                        "success": True,
                        "answer": answer,
                        "model": "deepseek-chat",
                        "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                        "response_time": "anlık"
                    }, ensure_ascii=False)
                    
                    self.wfile.write(result.encode('utf-8'))
                else:
                    raise Exception(f"API yanıt hatası: {response_data}")
                    
        except urllib.error.HTTPError as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f"HTTP Hatası {e.code}: {e.reason}"
            response = json.dumps({"error": error_msg})
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "error": str(e),
                "type": type(e).__name__
            })
            self.wfile.write(response.encode())
