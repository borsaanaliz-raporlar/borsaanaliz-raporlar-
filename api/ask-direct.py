# /api/ask-direct.py (EXCEL ENTEGRELİ)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from openpyxl import load_workbook
from datetime import datetime

def get_froto_data():
    """Excel'den FROTO verilerini çek"""
    try:
        # Son Excel dosyasını bul
        import glob
        excel_files = glob.glob('excel-files/*.xlsm')
        if not excel_files:
            return {"error": "Excel dosyası bulunamadı"}
        
        latest_excel = max(excel_files, key=os.path.getmtime)
        
        # Excel'i aç
        wb = load_workbook(latest_excel, data_only=True, read_only=True)
        
        # Sinyaller sayfasında FROTO'yu bul
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            
            # Başlıkları bul
            headers = []
            for col in range(1, 100):
                cell = ws.cell(row=1, column=col).value
                if cell:
                    headers.append(str(cell))
                else:
                    break
            
            # FROTO'yu ara
            froto_data = {}
            for row in ws.iter_rows(min_row=2, max_row=300, values_only=True):
                if row and row[0] and "FROTO" in str(row[0]).upper():
                    for i, value in enumerate(row):
                        if i < len(headers):
                            froto_data[headers[i]] = value
                    break
            
            wb.close()
            
            if froto_data:
                return {
                    "success": True,
                    "data": froto_data,
                    "excel_file": os.path.basename(latest_excel),
                    "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
            else:
                return {"error": "FROTO bulunamadı"}
        else:
            return {"error": "Sinyaller sayfası bulunamadı"}
            
    except Exception as e:
        return {"error": f"Excel okuma hatası: {str(e)}"}

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = json.dumps({
            "status": "online",
            "ai": "DeepSeek Chat + Excel Data",
            "test": "FROTO analizi için Excel verileri entegre"
        }, ensure_ascii=False)
        
        self.wfile.write(response.encode('utf-8'))
    
    def do_POST(self):
        try:
            # 1. Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"🤖 Soru: {question}")
            
            # 2. Excel verilerini çek (FROTO için)
            excel_info = {}
            if "FROTO" in question.upper():
                excel_info = get_froto_data()
                print(f"📊 Excel verisi: {excel_info.get('success', False)}")
            
            # 3. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 4. Prompt hazırla (Excel verileriyle)
            prompt = f"""🎯 BORSA ANALİZ UZMANI - EXCEL VERİLERİ

KULLANICI SORUSU: {question}

"""
            
            # Excel verileri varsa ekle
            if excel_info.get('success'):
                prompt += f"""EXCEL VERİLERİ (FROTO):
{json.dumps(excel_info['data'], indent=2, ensure_ascii=False)}

Kaynak: {excel_info['excel_file']} ({excel_info['timestamp']})
"""
            else:
                prompt += "NOT: Excel verisi bulunamadı, genel analiz yapılacak.\n"
            
            prompt += """
TALİMATLAR:
1. Yukarıdaki Excel verilerine GÖRE analiz yap
2. Sayısal değerleri KULLAN (Örnek: Close: 115.70)
3. VMA = Volume Moving Algorithm
4. RSI/MACD YOK, onlardan bahsetme
5. Yatırım tavsiyesi VERME

FORMAT:
• 📊 Excel Veri Analizi
• 📈 Teknik Yorum
• ⚠️ Riskler
• 💡 Öneri

CEVAP:"""
            
            # 5. DeepSeek API
            url = "https://api.deepseek.com/chat/completions"
            
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 600,
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
            
            # 6. API'yi çağır
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # Uyarı ekle
                if "yatırım tavsiyesi" not in answer.lower():
                    answer += "\n\n⚠️ **UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
                
                # Yanıt
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                    "excel_data_used": excel_info.get('success', False)
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
                "help": "Excel verisi veya API bağlantı hatası"
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
