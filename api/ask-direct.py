# /api/ask-direct.py (FINAL VERSION - DEEPSEEK EKLİ)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Logları Vercel'e gönder"""
        print(f"API_LOG: {format%args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({
            "status": "online",
            "ai": "DeepSeek Chat",
            "usage": "POST {'question':'borsa sorusu'}",
            "example": "FROTO teknik analizi"
        })
        self.wfile.write(response.encode())
    
    def do_POST(self):
        try:
            print("DEEPSEEK: POST başladı")
            
            # 1. Body'yi oku
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"DEEPSEEK: Soru: {question}")
            
            # 2. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("DEEPSEEK_API_KEY bulunamadı")
            
            print(f"DEEPSEEK: API Key hazır (ilk 8): {api_key[:8]}...)")
            
            # 3. Prompt hazırla
            prompt = f"""Borsa analiz uzmanı olarak cevapla: {question}

Önemli kurallar:
1. VMA = Volume Moving Algorithm (ASLA Volkswagen deme)
2. Excel'de RSI/MACD göstergeleri yok
3. Kısa ve net cevap ver (max 150 kelime)
4. Yatırım tavsiyesi VERME

Cevap:"""
            
            # 4. DeepSeek API isteği
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
            
            # JSON'ı hazırla
            json_data = json.dumps(request_data).encode('utf-8')
            
            # Request oluştur
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
            
            # 5. API'yi çağır
            print("DEEPSEEK: API çağrısı başlıyor...")
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            
            print(f"DEEPSEEK: API yanıt aldı, choices: {len(response_data.get('choices', []))}")
            
            # 6. Yanıtı işle
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # Uyarı ekle
                if "yatırım tavsiyesi" not in answer.lower():
                    answer += "\n\n⚠️ **UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
                
                # Başarılı yanıt
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0)
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print("DEEPSEEK: Başarılı yanıt gönderildi")
                
            else:
                error_msg = f"API geçersiz yanıt: {response_data}"
                print(f"DEEPSEEK ERROR: {error_msg}")
                raise Exception(error_msg)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if hasattr(e, 'read') else str(e)
            print(f"DEEPSEEK HTTP Error {e.code}: {error_body}")
            self.send_error(500, f"DeepSeek API hatası: {e.code}")
            
        except urllib.error.URLError as e:
            print(f"DEEPSEEK URL Error: {str(e)}")
            self.send_error(500, f"Bağlantı hatası: {str(e)}")
            
        except Exception as e:
            print(f"DEEPSEEK General Error: {type(e).__name__}: {str(e)}")
            self.send_error(500, f"{type(e).__name__}: {str(e)}")
