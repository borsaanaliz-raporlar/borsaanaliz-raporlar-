# /api/ask-direct.py (DEBUG VERSION)
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Tüm istekleri logla"""
        print(f"LOG: {self.address_string()} - {format%args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({
            "status": "debug_mode",
            "endpoint": "POST /api/ask-direct",
            "test_command": "curl -X POST -H \"Content-Type: application/json\" -d '{\"question\":\"test\"}' https://borsaanaliz-raporlar.vercel.app/api/ask-direct"
        })
        self.wfile.write(response.encode())
        print("DEBUG: GET isteği alındı")
    
    def do_POST(self):
        try:
            print("DEBUG: POST isteği başladı")
            
            # Headers'ı logla
            print(f"DEBUG Headers: {dict(self.headers)}")
            
            # Body'yi oku
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"DEBUG Content-Length: {content_length}")
            
            if content_length == 0:
                print("DEBUG ERROR: Content-Length 0")
                self.send_error(400, "Body boş")
                return
            
            post_data = self.rfile.read(content_length)
            print(f"DEBUG Raw data (ilk 100): {post_data[:100]}")
            
            data = json.loads(post_data)
            question = data.get('question', 'NO_QUESTION')
            print(f"DEBUG Parsed question: {question}")
            
            # API Key kontrolü
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            api_key_exists = api_key is not None and api_key != ""
            print(f"DEBUG API Key exists: {api_key_exists}")
            if api_key_exists:
                print(f"DEBUG API Key prefix: {api_key[:8]}...")
            
            # Yanıt ver
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = json.dumps({
                "success": True,
                "debug_info": {
                    "question_received": question,
                    "api_key_exists": api_key_exists,
                    "content_length": content_length,
                    "timestamp": "2026-02-07T18:15:00Z"
                },
                "message": "Debug başarılı! DeepSeek testine hazır."
            })
            
            self.wfile.write(response.encode())
            print("DEBUG: POST başarıyla tamamlandı")
            
        except json.JSONDecodeError as e:
            print(f"DEBUG JSON Error: {str(e)}")
            self.send_error(400, f"Geçersiz JSON: {str(e)}")
        except Exception as e:
            print(f"DEBUG General Error: {type(e).__name__}: {str(e)}")
            self.send_error(500, f"{type(e).__name__}: {str(e)}")
