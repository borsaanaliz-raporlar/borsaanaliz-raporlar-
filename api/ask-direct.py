# /api/ask-direct.py (GÜNCELLENMİŞ - GitHub Excel entegrasyonlu)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from io import BytesIO
import requests
from datetime import datetime

def get_excel_data(question):
    """GitHub'dan Excel indir ve ilgili hisse verilerini çek"""
    try:
        # GitHub'dan son Excel dosyasını al
        excel_url = "https://github.com/borsaanaliz-raporlar/borsaanaliz-raporlar-/raw/main/excel-files/BORSAANALIZ_V11_TAM_06022026.xlsm"
        
        print(f"📥 Excel indiriliyor: {excel_url}")
        response = requests.get(excel_url, timeout=30)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Excel indirilemedi: {response.status_code}"}
        
        # Memory'den Excel'i aç
        from openpyxl import load_workbook
        wb = load_workbook(filename=BytesIO(response.content), data_only=True, read_only=True)
        
        print(f"📊 Excel açıldı, sayfalar: {wb.sheetnames}")
        
        # Hangi hisse aranıyor?
        hisse_adi = None
        hisseler = ["FROTO", "THYAO", "TUPRS", "GARAN", "ASELS", "EREGL", "SASA", "KCHOL", "TOASO", "AKBNK"]
        
        for hisse in hisseler:
            if hisse.upper() in question.upper():
                hisse_adi = hisse
                break
        
        if not hisse_adi:
            return {"success": False, "error": "Soru hisse belirtmiyor"}
        
        print(f"🔍 Aranan hisse: {hisse_adi}")
        
        # Sinyaller sayfasında hisseyi ara
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            
            # Başlıkları bul (1. satır)
            headers = []
            for col in range(1, 50):  # İlk 50 kolonu kontrol et
                cell_value = ws.cell(row=1, column=col).value
                if cell_value:
                    headers.append(str(cell_value).strip())
                else:
                    break
            
            print(f"📋 Excel başlıkları ({len(headers)}): {headers[:10]}...")
            
            # Hisseyi ara (2. satırdan itibaren)
            hisse_data = {}
            for row in range(2, 300):  # İlk 300 satır
                hücre_değeri = ws.cell(row=row, column=1).value
                if hücre_değeri and hisse_adi in str(hücre_değeri):
                    print(f"✅ Hisse bulundu: satır {row}")
                    
                    # Tüm sütunları oku
                    for col_idx, header in enumerate(headers, start=1):
                        cell_value = ws.cell(row=row, column=col_idx).value
                        if cell_value is not None:
                            # Tarih objesini string'e çevir
                            if isinstance(cell_value, datetime):
                                hisse_data[header] = cell_value.strftime("%d.%m.%Y %H:%M")
                            else:
                                hisse_data[header] = str(cell_value)
                    
                    break
            
            wb.close()
            
            if hisse_data:
                return {
                    "success": True,
                    "hisse": hisse_adi,
                    "data": hisse_data,
                    "excel_file": "BORSAANALIZ_V11_TAM_06022026.xlsm",
                    "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
            else:
                return {"success": False, "error": f"{hisse_adi} bulunamadı"}
        else:
            return {"success": False, "error": "Sinyaller sayfası yok"}
            
    except Exception as e:
        return {"success": False, "error": f"Excel işleme hatası: {str(e)}"}

class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"API: {format%args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = json.dumps({
            "status": "online",
            "ai": "DeepSeek + Excel Entegrasyon",
            "features": "GitHub'dan Excel verisi okuyor",
            "hisseler": "FROTO, THYAO, TUPRS, GARAN, ASELS, EREGL, SASA, KCHOL, TOASO, AKBNK"
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
            
            # 2. Excel verilerini çek
            excel_result = get_excel_data(question)
            print(f"📊 Excel sonucu: {excel_result.get('success', False)}")
            
            # 3. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 4. Prompt hazırla
            prompt = f"""🎯 **BORSA ANALİZ UZMANI - EXCEL VERİLERİ İLE**
            
KULLANICI SORUSU: {question}

"""
            
            # Excel verileri varsa ekle
            if excel_result.get('success'):
                excel_data = excel_result['data']
                prompt += f"""📈 **EXCEL VERİLERİ ({excel_result['hisse']}):**

"""
                
                # Önemli alanları listele
                important_fields = [
                    'Hisse', 'Close', 'Open', 'High', 'Low', 'Hacim', 'VMA',
                    'EMA_8', 'EMA_21', 'EMA_55', 'Pivot', 'S1', 'R1',
                    'BB_UPPER', 'BB_LOWER', 'Trend', 'Pearson55'
                ]
                
                for field in important_fields:
                    if field in excel_data:
                        prompt += f"- {field}: {excel_data[field]}\n"
                
                prompt += f"""
📁 Kaynak: {excel_result['excel_file']} ({excel_result['timestamp']})
"""
            else:
                prompt += "⚠️ **NOT:** Excel verisi bulunamadı. Genel analiz yapılacak.\n"
            
            prompt += """
🎯 **TALİMATLAR:**
1. Yukarıdaki Excel verilerini KULLANARAK analiz yap
2. Sayısal değerleri BELİRT (Örnek: Close: 115.70 TL)
3. VMA = Volume Moving Algorithm (VMA değerini yorumla)
4. RSI/MACD YOK, onlardan bahsetme
5. Yatırım tavsiyesi VERME
6. Kısa ve net olsun (max 200 kelime)

📊 **ANALİZ FORMATI:**
• Excel Verileri Özeti
• VMA Bazlı Teknik Yorum
• Kritik Seviyeler
• Öneriler (bilgi amaçlı)

CEVAP:"""
            
            print(f"📝 Prompt hazır ({len(prompt)} karakter)")
            
            # 5. DeepSeek API
            url = "https://api.deepseek.com/chat/completions"
            
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 500,
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
            
            # 6. API'yi çağır
            print("🔄 DeepSeek API çağrılıyor...")
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            print("✅ DeepSeek yanıt aldı")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # Uyarı ekle
                if "yatırım tavsiyesi" not in answer.lower():
                    answer += "\n\n⚠️ **UYARI:** Bu analiz bilgi amaçlıdır, yatırım tavsiyesi değildir."
                
                # 7. Yanıt ver
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                    "excel_data_used": excel_result.get('success', False),
                    "hisse": excel_result.get('hisse', None)
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Yanıt gönderildi ({len(answer)} karakter)")
                
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
