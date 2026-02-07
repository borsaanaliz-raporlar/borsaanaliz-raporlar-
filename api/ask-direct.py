# /api/ask-direct.py (REQUESTS OLMADAN)
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = json.dumps({
            "status": "online",
            "message": "BorsaAnaliz Direct API v1.0",
            "endpoint": "POST /api/ask-direct için soru gönderin"
        })
        
        self.wfile.write(response.encode())
    
    def do_POST(self):
        """Basit POST - DeepSeek olmadan"""
        try:
            # Body'yi oku
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
            
            print(f"🤖 Soru alındı: {question[:50]}...")
            
            # Basit cevap (requests olmadan)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = json.dumps({
                "success": True,
                "answer": f"✅ Sorunuz alındı: '{question}'. Direct API çalışıyor!",
                "note": "Requests modülü yüklenene kadar basit modda.",
                "next_step": "requirements.txt eklendikten sonra DeepSeek entegre edilecek."
            })
            
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "error": str(e),
                "help": "requirements.txt kontrol edin"
            })
            self.wfile.write(response.encode())
