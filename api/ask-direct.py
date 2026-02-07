# /api/ask-direct.py (SON HAL - ÇOK KISA ANALİZ)
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import tempfile
import re
from io import BytesIO
import ssl

# SSL doğrulamasını devre dışı bırak (Vercel için)
ssl._create_default_https_context = ssl._create_unverified_context

def find_latest_excel():
    """Sitedeki EN GÜNCEL Excel dosyasını bul"""
    try:
        base_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/"
        
        today = datetime.now()
        excel_files_to_try = []
        
        # Son 7 günü kontrol et
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%d%m%Y")
            filename = f"BORSAANALIZ_V11_TAM_{date_str}.xlsm"
            excel_files_to_try.append(filename)
        
        print(f"🔍 En güncel Excel aranıyor...")
        
        for filename in excel_files_to_try:
            file_url = f"{base_url}{filename}"
            try:
                req = urllib.request.Request(file_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ EN GÜNCEL EXCEL BULUNDU: {filename}")
                        
                        date_match = re.search(r'(\d{2})(\d{2})(\d{4})\.xlsm$', filename)
                        if date_match:
                            day, month, year = date_match.groups()
                            file_date = datetime(int(year), int(month), int(day))
                            return file_url, file_date.strftime("%d.%m.%Y")
                        else:
                            return file_url, "güncel"
            except:
                continue
        
        print("⚠️ Güncel dosya bulunamadı, fallback kullanılıyor...")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"
        
    except Exception as e:
        print(f"❌ Excel bulma hatası: {e}")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"

def clean_header(header):
    """Başlığı temizle: 'Hisse (06-02-2026)' -> 'Hisse'"""
    if not header:
        return ""
    header = str(header).split('(')[0].strip()
    header = re.sub(r'\s+', ' ', header)
    return header

def read_all_excel_data(excel_path):
    """Excel'den verileri oku"""
    try:
        from openpyxl import load_workbook
        
        print(f"📖 Excel açılıyor: {excel_path}")
        
        req = urllib.request.Request(excel_path, 
                                    headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=60) as response:
            excel_content = response.read()
        
        print(f"✅ Excel indirildi ({len(excel_content):,} bytes)")
        
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
            tmp.write(excel_content)
            tmp_path = tmp.name
        
        wb = load_workbook(tmp_path, data_only=True, read_only=True)
        os.unlink(tmp_path)
        
        print(f"✅ Excel açıldı. Sayfalar: {wb.sheetnames}")
        
        data = {
            "excel_file": os.path.basename(excel_path),
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "sheets": {}
        }
        
        # 1. SİNYALLER SAYFASI
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            print(f"📊 Sinyaller okunuyor...")
            
            headers_clean = []
            for col in range(1, 150):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers_clean.append(clean_header(str(cell_val)))
                else:
                    break
            
            sinyaller_data = {}
            max_rows = min(1001, ws.max_row)
            
            for row in ws.iter_rows(min_row=2, max_row=max_rows, values_only=True):
                if row and row[0]:
                    hisse_adi = str(row[0]).strip()
                    if hisse_adi:
                        hisse_dict = {}
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                if isinstance(cell_val, datetime):
                                    hisse_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, (int, float)):
                                    hisse_dict[header_name] = cell_val
                                else:
                                    hisse_dict[header_name] = str(cell_val).strip()
                        sinyaller_data[hisse_adi] = hisse_dict
            
            data["sheets"]["Sinyaller"] = {
                "headers": headers_clean,
                "hisseler": sinyaller_data,
                "toplam_hisse": len(sinyaller_data)
            }
            print(f"✅ Sinyaller okundu: {len(sinyaller_data)} hisse")
        
        # 2. ENDEKSLER SAYFASI
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            print(f"📈 ENDEKSLER okunuyor...")
            
            headers_clean = []
            for col in range(1, 150):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers_clean.append(clean_header(str(cell_val)))
                else:
                    break
            
            endeks_dict = {}
            max_rows = min(201, ws.max_row)
            
            for row in ws.iter_rows(min_row=2, max_row=max_rows, values_only=True):
                if row and row[0]:
                    sembol_adi = str(row[0]).strip()
                    if sembol_adi:
                        sembol_dict = {}
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                if isinstance(cell_val, datetime):
                                    sembol_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, (int, float)):
                                    sembol_dict[header_name] = cell_val
                                else:
                                    sembol_dict[header_name] = str(cell_val).strip()
                        endeks_dict[sembol_adi] = sembol_dict
            
            data["sheets"]["ENDEKSLER"] = {
                "headers": headers_clean,
                "semboller": endeks_dict,
                "toplam_sembol": len(endeks_dict)
            }
            print(f"✅ ENDEKSLER okundu: {len(endeks_dict)} sembol")
        
        # 3. FON_EMTIA_COIN_DOVIZ SAYFASI
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            print(f"💰 FON_EMTIA okunuyor...")
            
            headers_clean = []
            for col in range(1, 150):
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers_clean.append(clean_header(str(cell_val)))
                else:
                    break
            
            fon_dict = {}
            max_rows = min(151, ws.max_row)
            
            for row in ws.iter_rows(min_row=2, max_row=max_rows, values_only=True):
                if row and row[0]:
                    sembol_adi = str(row[0]).strip()
                    if sembol_adi:
                        sembol_dict = {}
                        for col_idx in range(min(len(headers_clean), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers_clean[col_idx]
                                if isinstance(cell_val, datetime):
                                    sembol_dict[header_name] = cell_val.strftime("%d.%m.%Y")
                                elif isinstance(cell_val, float):
                                    sembol_dict[header_name] = round(cell_val, 2)
                                elif isinstance(cell_val, (int, float)):
                                    sembol_dict[header_name] = cell_val
                                else:
                                    sembol_dict[header_name] = str(cell_val).strip()
                        fon_dict[sembol_adi] = sembol_dict
            
            data["sheets"]["FON_EMTIA_COIN_DOVIZ"] = {
                "headers": headers_clean,
                "semboller": fon_dict,
                "toplam_sembol": len(fon_dict)
            }
            print(f"✅ FON_EMTIA okundu: {len(fon_dict)} sembol")
        
        wb.close()
        
        toplam_sembol = 0
        for sheet_name, sheet_data in data["sheets"].items():
            if "hisseler" in sheet_data:
                toplam_sembol += sheet_data.get("toplam_hisse", 0)
            elif "semboller" in sheet_data:
                toplam_sembol += sheet_data.get("toplam_sembol", 0)
        
        print(f"🎉 EXCEL OKUNDU! Toplam: {toplam_sembol} sembol")
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        return {"success": False, "error": f"Excel okuma hatası: {str(e)}"}

def find_in_excel_data(question, excel_data):
    """Excel verilerinde arama yap"""
    try:
        question_upper = question.upper()
        
        search_terms = []
        for word in re.findall(r'[A-Z0-9]+', question_upper):
            if len(word) >= 2:
                search_terms.append(word)
        
        print(f"🔍 Aranan: {search_terms}")
        
        # 1. SİNYALLER'DE ARA
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            for term in search_terms:
                for hisse_adi, hisse_veriler in hisseler.items():
                    hisse_clean = re.sub(r'[^A-Z0-9]', '', hisse_adi.upper())
                    if term in hisse_clean or hisse_clean in term:
                        print(f"✅ {hisse_adi} Sinyaller'de bulundu")
                        return {
                            "found": True,
                            "type": "hisse",
                            "data": hisse_veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        # 2. ENDEKSLER'DE ARA
        if "ENDEKSLER" in excel_data["sheets"]:
            endeksler = excel_data["sheets"]["ENDEKSLER"]["semboller"]
            
            for term in search_terms:
                for sembol_adi, sembol_veriler in endeksler.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} ENDEKSLER'de bulundu")
                        return {
                            "found": True,
                            "type": "endeks",
                            "data": sembol_veriler,
                            "sayfa": "ENDEKSLER",
                            "name": sembol_adi
                        }
        
        # 3. FON_EMTIA'DA ARA
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            fonlar = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
            
            for term in search_terms:
                for sembol_adi, sembol_veriler in fonlar.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} FON_EMTIA'da bulundu")
                        return {
                            "found": True,
                            "type": "fon_emtia",
                            "data": sembol_veriler,
                            "sayfa": "FON_EMTIA_COIN_DOVIZ",
                            "name": sembol_adi
                        }
        
        print(f"⚠️ Bulunamadı: {search_terms}")
        return {
            "found": False,
            "type": None,
            "data": None,
            "sayfa": None,
            "name": None
        }
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {"found": False, "error": str(e)}

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        excel_url, excel_date = find_latest_excel()
        
        response = json.dumps({
            "status": "online",
            "ai": "BORSAANALIZ AI - KISA ANALİZ",
            "excel": {
                "dosya": os.path.basename(excel_url),
                "tarih": excel_date,
                "format": "5 satır kısa analiz"
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
            
            if not question:
                self.send_error(400, "Soru gerekli")
                return
            
            print(f"\n=== YENİ SORU: {question} ===")
            
            # 2. Excel'i bul
            print("🔍 Excel bulunuyor...")
            excel_start = datetime.now()
            excel_url, excel_date = find_latest_excel()
            print(f"✅ Excel: {os.path.basename(excel_url)} ({excel_date})")
            
            # 3. Excel'i oku
            print("📥 Excel okunuyor...")
            excel_result = read_all_excel_data(excel_url)
            
            if not excel_result.get("success"):
                print("❌ Excel okunamadı")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
            
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Excel okunamadı. Lütfen daha sonra tekrar deneyin.",
                    "excel_data_used": False
                }, ensure_ascii=False)
            
                self.wfile.write(result.encode('utf-8'))
                return
            
            excel_time = (datetime.now() - excel_start).total_seconds()
            print(f"⏱️ Excel: {excel_time:.1f} sn")
            
            # 4. Sembolü bul
            print("🔍 Sembol aranıyor...")
            analysis = find_in_excel_data(question, excel_result["data"])
            
            # 5. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 6. PROMPT HAZIRLA (ÇOK KISA!)
            prompt = f"""KULLANICI SORUSU: {question}

"""
            
            if analysis.get("found"):
                sembol_data = analysis["data"]
                sembol_name = analysis["name"]
                
                prompt += f"""SEMBOL: {sembol_name}
EXCEL VERİLERİ:
"""
                
                # SADECE 5 ÖNEMLİ ALAN
                fields_to_show = [
                    ('Close', 'Fiyat'),
                    ('VMA trend algo', 'VMA'),
                    ('EMA_8', 'EMA8'),
                    ('EMA_21', 'EMA21'), 
                    ('EMA_55', 'EMA55'),
                    ('Pivot', 'Pivot'),
                    ('S1', 'S1'),
                    ('R1', 'R1'),
                    ('DURUM', 'Durum'),
                    ('AI_YORUM', 'Yorum')
                ]
                
                for field, label in fields_to_show:
                    if field in sembol_data:
                        value = sembol_data[field]
                        prompt += f"{label}: {value}\n"
                
                prompt += f"\nExcel'de bulundu ({analysis['sayfa']}).\n"
            
            else:
                prompt += """SEMBOL Excel'de bulunamadı.
Örnek semboller: FROTO, THYAO, GMSTR, XU100, ALTIN
"""
            
            # ÇOK SIKI TALİMATLAR!
            prompt += """
🎯 TALİMATLAR (KESİN KURALLAR):
1. EN FAZLA 5 SATIR yaz
2. HER SATIR MAX 10 KELİME
3. SADECE bu formatı kullan:
   SATIR 1: 📈 Fiyat: [Close] TL
   SATIR 2: 📊 VMA: [VMA trend algo] - [1 kelime yorum]
   SATIR 3: 📉 EMA: EMA8[EMA_8] EMA21[EMA_21] EMA55[EMA_55]
   SATIR 4: ⚖️ Seviye: P[Pivot] S1[S1] R1[R1]
   SATIR 5: 🎯 Durum: [DURUM]

4. ASLA başlık, tarih, "Analiz Raporu" yazma
5. ASLA hisse açılımı yazma
6. ASLA yatırım tavsiyesi verme
7. RSI/MACD'den bahsetme
8. Excel verileri dışında bilgi verme

⚠️ UYARI: 5 satırı geçersen veya 50 kelimeden fazla yazarsan SİSTEM HATASI olur!

CEVAP (SADECE 5 SATIR):
"""
            
            print(f"📝 Prompt: {len(prompt)} karakter")
            
            # 7. DEEPSEEK API
            ai_start = datetime.now()
            url = "https://api.deepseek.com/chat/completions"
            
            # ÇOK KISA YANIT İÇİN!
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 200,  # ÇOK KISA!
                "temperature": 0.1,
                "stop": ["\n\n"]  # İki satır boşlukta dur
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
            
            print("🔄 DeepSeek çağrılıyor (200 token)...")
            response = urllib.request.urlopen(req, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            ai_time = (datetime.now() - ai_start).total_seconds()
            
            print(f"✅ Yanıt alındı ({ai_time:.1f} sn)")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # Yanıtı kontrol et (çok uzunsa kes)
                if len(answer.split()) > 60:  # 60 kelimeden fazlaysa
                    lines = answer.split('\n')
                    answer = '\n'.join(lines[:5])  # İlk 5 satırı al
                
                # 8. YANIT VER
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                total_time = excel_time + ai_time
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": analysis.get("found", False),
                    "symbol": analysis.get("name"),
                    "sheet": analysis.get("sayfa"),
                    "time_sec": round(total_time, 1)
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Yanıt gönderildi ({total_time:.1f} sn)")
                print("=== TAMAMLANDI ===\n")
                
            else:
                raise Exception("API yanıtı yok")
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "success": False,
                "answer": f"❌ Hata: {str(e)[:100]}",
                "excel_data_used": False
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
