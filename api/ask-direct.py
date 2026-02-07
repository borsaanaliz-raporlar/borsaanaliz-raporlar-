# /api/ask-direct.py (BASİT HATA AYIKLAMA VERSİYONU)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"API: {format%args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # Test: requests modülü çalışıyor mu?
        try:
            import requests
            requests_status = "✅ Çalışıyor"
        except:
            requests_status = "❌ Yüklü değil"
            
        try:
            import openpyxl
            openpyxl_status = "✅ Çalışıyor"
        except:
            openpyxl_status = "❌ Yüklü değil"
        
        response = json.dumps({
            "status": "online",
            "debug": {
                "requests": requests_status,
                "openpyxl": openpyxl_status,
                "python_version": "3.x"
            }
        }, ensure_ascii=False)
        
        self.wfile.write(response.encode('utf-8'))
    
    def do_POST(self):
        try:
            # 1. Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            print(f"🤖 Soru: {question}")
            
            # 2. Hangi hisse?
            hisse_adi = None
            hisseler = ["FROTO", "THYAO", "TUPRS", "GARAN", "ASELS", "EREGL", "SASA", "KCHOL", "TOASO", "AKBNK"]
            
            for hisse in hisseler:
                if hisse.upper() in question.upper():
                    hisse_adi = hisse
                    break
            
            # 3. HARDCODE VERİLER (Excel olmadan)
            veriler = {}
            if hisse_adi == "FROTO":
                veriler = {
                    "Hisse": "FROTO",
                    "Close": "115.70",
                    "Open": "115.82", 
                    "High": "117.10",
                    "Low": "114.40",
                    "Hacim": "2,109,464,371",
                    "VMA": "POZİTİF (54)",
                    "EMA_8": "113.66",
                    "EMA_21": "108.50",
                    "EMA_55": "101.63",
                    "Pivot": "115.49",
                    "Trend": "YÜKSELİŞ"
                }
            elif hisse_adi == "TUPRS":
                veriler = {
                    "Hisse": "TUPRS",
                    "Close": "156.20",
                    "Open": "155.80",
                    "High": "157.50",
                    "Low": "154.90",
                    "Hacim": "1,850,320,500",
                    "VMA": "POZİTİF (62)",
                    "EMA_8": "154.30",
                    "EMA_21": "152.10",
                    "EMA_55": "148.75",
                    "Pivot": "156.05",
                    "Trend": "YÜKSELİŞ"
                }
            
            # 4. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 5. Prompt hazırla
            prompt = f"""🎯 **BORSA ANALİZ UZMANI - GERÇEK VERİLERLE**

KULLANICI SORUSU: {question}

"""
            
            if veriler:
                prompt += f"""📈 **GERÇEK VERİLER ({hisse_adi}):**

"""
                for key, value in veriler.items():
                    prompt += f"- {key}: {value}\n"
                
                prompt += f"""
📅 Kaynak: BORSAANALIZ Excel Raporu (06.02.2026)
"""
            else:
                prompt += "⚠️ **NOT:** Bu hisse için örnek veri hazır değil.\n"
            
            prompt += """
🎯 **TALİMATLAR:**
1. Yukarıdaki GERÇEK verileri KULLANARAK analiz yap
2. Sayısal değerleri BELİRT (Örnek: FROTO Close: 115.70 TL)
3. VMA değerini yorumla
4. Kısa ve net olsun (max 150 kelime)
5. Yatırım tavsiyesi VERME

📊 **FORMAT:**
• Gerçek Veri Özeti
• VMA Yorumu
• Öneriler (bilgi amaçlı)

CEVAP:"""
            
            print(f"📝 Prompt hazır, veriler: {bool(veriler)}")
            
            # 6. DeepSeek API
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
                    'Content-Type': 'application/json'
                }
            )
            
            # 7. API'yi çağır
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # 8. Yanıt ver
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                    "excel_data_used": bool(veriler),
                    "hisse": hisse_adi,
                    "data_source": "hardcoded_sample" if veriler else "general_analysis"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                
            else:
                raise Exception("API geçersiz yanıt")
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "error": str(e),
                "help": "API bağlantı hatası"
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
