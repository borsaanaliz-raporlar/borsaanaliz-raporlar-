# api/index.py - ANA ENTRY POINT
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "online",
            "service": "BorsaAnaliz API",
            "version": "2.0",
            "path": self.path,
            "endpoints": {
                "/api/query": "Sorgulama Motoru",
                "/api/ask": "AI Asistanı"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Gelen isteği yönlendir
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "success": True,
            "message": "API is working",
            "received_data": post_data.decode()[:100] if post_data else None
        }
        
        self.wfile.write(json.dumps(response).encode())
