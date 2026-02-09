#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# api/ask-direct.py - BASİT API WRAPPER
"""
ÇALIŞAN excel_ai_analyzer.py'yi API olarak sunar
"""

import os
import sys
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import subprocess
import tempfile

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Sistem durumu"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "version": "Excel AI Analyzer API",
            "backend": ".github/workflows/excel_ai_analyzer.py",
            "message": "POST: {'question': 'GARAN analiz et', 'mode': 'hibrit'}"
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
    
    def do_POST(self):
        """Analiz yap - ÇALIŞAN analyzer'ı çağır"""
        try:
            # 1. İstek verilerini al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            question = data.get('question', '').strip()
            mode = data.get('mode', 'hibrit')  # hizli, detayli, hibrit
            
            if not question:
                self.send_error_response("Soru gerekli")
                return
            
            print(f"🔍 Soru: {question}", file=sys.stderr)
            print(f"🎮 Mod: {mode}", file=sys.stderr)
            
            # 2. Python subprocess ile ÇALIŞAN analyzer'ı çağır
            # Bu KESİN ÇALIŞIR çünkü excel_ai_analyzer.py zaten çalışıyor!
            
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write(question)
                question_file = tmp.name
            
            try:
                # ÇALIŞAN analyzer'ı subprocess ile çağır
                if mode == "hizli":
                    # DeepSeek modu (hızlı)
                    cmd = ['python3', '.github/workflows/excel_ai_analyzer.py', question]
                else:
                    # Groq modu (detaylı) - use_deepseek=False
                    cmd = ['python3', '.github/workflows/excel_ai_analyzer.py', question, '--use_deepseek', 'false']
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 dakika timeout
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    answer = result.stdout
                    
                    # Başarılı
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        "success": True,
                        "answer": answer[-5000:],  # Son 5000 karakter
                        "mode": mode,
                        "backend": "excel_ai_analyzer.py",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                else:
                    # Hata
                    error_msg = result.stderr[:200] if result.stderr else "Bilinmeyen hata"
                    print(f"❌ Analyzer hatası: {error_msg}", file=sys.stderr)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        "success": False,
                        "answer": f"❌ Analyzer hatası: {error_msg}",
                        "mode": mode,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except subprocess.TimeoutExpired:
                # Timeout
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "success": False,
                    "answer": "⏱️ **Analiz zaman aşımı!**\n\nLütfen daha kısa bir soru deneyin veya 'hizli' modunu kullanın.",
                    "mode": mode,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                # Diğer hatalar
                print(f"❌ Subprocess hatası: {e}", file=sys.stderr)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "success": False,
                    "answer": f"❌ Sistem hatası: {str(e)[:100]}",
                    "mode": mode,
                    "timestamp": datetime.now().isoformat()
                }
            
            finally:
                # Temizlik
                if os.path.exists(question_file):
                    os.unlink(question_file)
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            # Ana hata
            print(f"❌ API hatası: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "success": False,
                "answer": f"❌ API hatası: {str(e)[:100]}",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
    
    def send_error_response(self, error):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"success": False, "answer": f"❌ Hata: {error}"}
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

# Test için
if __name__ == "__main__":
    from http.server import HTTPServer
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 API Başlatıldı: http://localhost:{port}")
    print("📂 Backend: .github/workflows/excel_ai_analyzer.py")
    server.serve_forever()
