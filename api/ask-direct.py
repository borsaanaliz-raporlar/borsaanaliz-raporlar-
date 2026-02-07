# /api/ask-direct.py (TAM ÇÖZÜM)
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
    """Sitedeki EN GÜNCEL Excel dosyasını AKILLICA bul"""
    try:
        base_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/"
        
        # ÖNCE: Bilinen dosya isimlerini kontrol et
        today = datetime.now()
        excel_files_to_try = []
        
        # Son 7 günü kontrol et
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%d%m%Y")
            filename = f"BORSAANALIZ_V11_TAM_{date_str}.xlsm"
            excel_files_to_try.append(filename)
        
        # 630+ hisse olduğu için dosya büyük, en günceli bul
        print(f"🔍 En güncel Excel aranıyor ({len(excel_files_to_try)} dosya kontrol edilecek)...")
        
        for filename in excel_files_to_try:
            file_url = f"{base_url}{filename}"
            try:
                # HEAD isteği ile dosya var mı kontrol et
                req = urllib.request.Request(file_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ EN GÜNCEL EXCEL BULUNDU: {filename}")
                        
                        # Dosyadan tarihi çıkar
                        date_match = re.search(r'(\d{2})(\d{2})(\d{4})\.xlsm$', filename)
                        if date_match:
                            day, month, year = date_match.groups()
                            file_date = datetime(int(year), int(month), int(day))
                            return file_url, file_date.strftime("%d.%m.%Y")
                        else:
                            return file_url, "güncel"
            except:
                continue  # Bu dosya yok, diğerini dene
        
        # Hiçbiri yoksa, fallback olarak bilinen son dosya
        print("⚠️ Güncel dosya bulunamadı, fallback kullanılıyor...")
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"
        
    except Exception as e:
        print(f"❌ Excel bulma hatası: {e}")
        # Son çare
        return "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm", "06.02.2026"

def read_all_excel_data(excel_path):
    """Excel'den TÜM verileri oku (3 sayfa + TÜM hisseler)"""
    try:
        from openpyxl import load_workbook
        
        print(f"📖 Excel açılıyor: {excel_path}")
        
        # URL'den indir
        req = urllib.request.Request(excel_path, 
                                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        with urllib.request.urlopen(req, timeout=60) as response:  # 60 saniye timeout
            excel_content = response.read()
        
        print(f"✅ Excel indirildi ({len(excel_content):,} bytes)")
        
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
            tmp.write(excel_content)
            tmp_path = tmp.name
        
        # Excel'i aç - SADECE OKUMA MODUNDA (hızlı)
        wb = load_workbook(tmp_path, data_only=True, read_only=True)
        
        # Geçici dosyayı temizle
        os.unlink(tmp_path)
        
        print(f"✅ Excel açıldı. Sayfalar: {wb.sheetnames}")
        
        data = {
            "excel_file": os.path.basename(excel_path),
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "sheets": {}
        }
        
        # 1. SİNYALLER SAYFASI (TÜM HİSSELER - 630+)
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            print(f"📊 Sinyaller sayfası okunuyor: ~{ws.max_row} satır...")
            
            # Başlıkları al (ilk satır)
            headers = []
            max_columns = 0
            
            # Kaç sütun olduğunu bul
            for col in range(1, 100):  # Maksimum 100 sütun kontrol et
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers.append(str(cell_val).strip())
                    max_columns = col
                else:
                    break
            
            print(f"📋 {len(headers)} sütun başlığı bulundu: {headers[:5]}...")
            
            # TÜM hisseleri oku (tüm satırlar)
            sinyaller_data = {}
            total_hisseler = 0
            
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
                if row and row[0]:  # İlk sütunda hisse adı varsa
                    hisse_adi = str(row[0]).strip()
                    if hisse_adi:  # Boş değilse
                        hisse_dict = {}
                        
                        # Tüm sütunları işle
                        for col_idx in range(min(len(headers), len(row))):
                            cell_val = row[col_idx]
                            if cell_val is not None:
                                header_name = headers[col_idx] if col_idx < len(headers) else f"Col{col_idx+1}"
                                
                                # Format dönüşümü
                                if isinstance(cell_val, datetime):
                                    hisse_dict[header_name] = cell_val.strftime("%d.%m.%Y %H:%M")
                                elif isinstance(cell_val, (int, float)):
                                    # Sayısal değerleri olduğu gibi sakla
                                    hisse_dict[header_name] = cell_val
                                else:
                                    hisse_dict[header_name] = str(cell_val).strip()
                        
                        sinyaller_data[hisse_adi] = hisse_dict
                        total_hisseler += 1
            
            data["sheets"]["Sinyaller"] = {
                "headers": headers,
                "hisseler": sinyaller_data,
                "toplam_hisse": total_hisseler,
                "ornek_hisseler": list(sinyaller_data.keys())[:5]  # İlk 5 hisseyi göster
            }
            
            print(f"✅ Sinyaller okundu: {total_hisseler} hisse")
        
        # 2. ENDEKSLER SAYFASI
        if "ENDEKSLER" in wb.sheetnames:
            ws = wb["ENDEKSLER"]
            print(f"📈 ENDEKSLER sayfası okunuyor...")
            
            endeks_data = []
            # İlk 50 satırı oku (performans için)
            for row in ws.iter_rows(min_row=1, max_row=min(51, ws.max_row), values_only=True):
                row_data = []
                for cell_val in row:
                    if cell_val is not None:
                        if isinstance(cell_val, datetime):
                            row_data.append(cell_val.strftime("%d.%m.%Y"))
                        elif isinstance(cell_val, (int, float)):
                            row_data.append(cell_val)
                        else:
                            row_data.append(str(cell_val))
                    else:
                        row_data.append("")
                endeks_data.append(row_data)
            
            data["sheets"]["ENDEKSLER"] = {
                "data": endeks_data,
                "toplam_satir": len(endeks_data)
            }
            print(f"✅ ENDEKSLER okundu: {len(endeks_data)} satır")
        
        # 3. FON_EMTIA_COIN_DOVIZ SAYFASI
        if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
            ws = wb["FON_EMTIA_COIN_DOVIZ"]
            print(f"💰 FON_EMTIA_COIN_DOVIZ sayfası okunuyor...")
            
            fon_data = []
            # İlk 100 satırı oku
            for row in ws.iter_rows(min_row=1, max_row=min(101, ws.max_row), values_only=True):
                row_data = []
                for cell_val in row:
                    if cell_val is not None:
                        if isinstance(cell_val, datetime):
                            row_data.append(cell_val.strftime("%d.%m.%Y"))
                        elif isinstance(cell_val, float):
                            row_data.append(round(cell_val, 4))
                        elif isinstance(cell_val, (int, float)):
                            row_data.append(cell_val)
                        else:
                            row_data.append(str(cell_val))
                    else:
                        row_data.append("")
                fon_data.append(row_data)
            
            data["sheets"]["FON_EMTIA_COIN_DOVIZ"] = {
                "data": fon_data,
                "toplam_satir": len(fon_data)
            }
            print(f"✅ FON_EMTIA_COIN_DOVIZ okundu: {len(fon_data)} satır")
        
        wb.close()
        print(f"🎉 TÜM EXCEL OKUNDU! Toplam: {data['sheets'].get('Sinyaller', {}).get('toplam_hisse', 0)} hisse")
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Excel okuma hatası: {str(e)}"}

def find_in_excel_data(question, excel_data):
    """Excel verilerinde soruya göre arama yap"""
    try:
        question_upper = question.upper()
        results = {
            "hisse": None,
            "endeks": None,
            "fon_emtia": None,
            "excel_file": excel_data["excel_file"]
        }
        
        # 1. HİSSE ARA (Sinyaller sayfasında)
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            # Popüler hisseler önce
            popular_hisseler = ["FROTO", "THYAO", "TUPRS", "GARAN", "ASELS", "EREGL", 
                              "SASA", "KCHOL", "TOASO", "AKBNK", "BIMAS", "HEKTS",
                              "KOZAA", "KOZAL", "PETKM", "SAHOL", "TCELL", "YKBNK"]
            
            # Önce popüler hisselerde ara
            for hisse in popular_hisseler:
                if hisse in question_upper:
                    if hisse in hisseler:
                        results["hisse"] = {
                            "adi": hisse,
                            "veriler": hisseler[hisse],
                            "tum_veriler": True
                        }
                        break
            
            # Popülerde bulunamazsa tüm hisselerde ara
            if not results["hisse"]:
                for hisse_adi, veriler in hisseler.items():
                    if hisse_adi in question_upper:
                        results["hisse"] = {
                            "adi": hisse_adi,
                            "veriler": veriler,
                            "tum_veriler": True
                        }
                        break
        
        # 2. ENDEKS ARA
        if "ENDEKSLER" in excel_data["sheets"]:
            endeks_rows = excel_data["sheets"]["ENDEKSLER"]["data"]
            endeks_terimleri = ["BIST", "XU100", "XU030", "ENDEKS", "INDEX", "XU050"]
            
            for terim in endeks_terimleri:
                if terim in question_upper:
                    # İlk 5 endeksi göster
                    results["endeks"] = {
                        "veriler": endeks_rows[:5],
                        "bulunan_terim": terim,
                        "toplam_endeks": len(endeks_rows)
                    }
                    break
        
        # 3. FON/EMTİA/DÖVİZ ARA
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            fon_rows = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["data"]
            fon_terimleri = ["USD", "EUR", "ALTIN", "GRAM", "BITCOIN", "ETHEREUM",
                           "FON", "EMTIA", "DOVIZ", "COIN", "GAZI", "PETROL"]
            
            for terim in fon_terimleri:
                if terim in question_upper:
                    # İlk 10 veriyi göster
                    results["fon_emtia"] = {
                        "veriler": fon_rows[:10],
                        "bulunan_terim": terim,
                        "toplam_veri": len(fon_rows)
                    }
                    break
        
        return results
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {"error": str(e)}

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # En güncel Excel'i bul
        excel_url, excel_date = find_latest_excel()
        
        response = json.dumps({
            "status": "online",
            "ai": "BORSAANALIZ AI - TAM EXCEL ANALİZ",
            "excel": {
                "guncel_dosya": os.path.basename(excel_url),
                "tarih": excel_date,
                "sayfalar": ["Sinyaller (630+ hisse)", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"],
                "not": "En güncel Excel otomatik bulunur, TÜM veriler analiz edilir"
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
            
            print(f"\n" + "="*70)
            print(f"🤖 TAM EXCEL ANALİZ BAŞLIYOR: {question}")
            print("="*70)
            
            # 2. EN GÜNCEL EXCEL'İ BUL
            print("🔍 EN GÜNCEL EXCEL DOSYASI ARANIYOR...")
            excel_start = datetime.now()
            excel_url, excel_date = find_latest_excel()
            print(f"✅ BULUNDU: {os.path.basename(excel_url)} ({excel_date})")
            
            # 3. EXCEL'İ İNDİR VE TÜM VERİLERİ OKU
            print("📥 Excel indiriliyor ve TÜM veriler okunuyor...")
            excel_result = read_all_excel_data(excel_url)
            
            if not excel_result["success"]:
                raise Exception(f"Excel okunamadı: {excel_result.get('error')}")
            
            excel_time = (datetime.now() - excel_start).total_seconds()
            print(f"⏱️ Excel işlem süresi: {excel_time:.2f} sn")
            
            # 4. SORUYU EXCEL VERİLERİNDE ARA
            print("🔍 Soru Excel verilerinde analiz ediliyor...")
            analysis = find_in_excel_data(question, excel_result["data"])
            
            # 5. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception("API Key bulunamadı")
            
            # 6. PROMPT HAZIRLA (TÜM EXCEL VERİLERİYLE)
            prompt = f"""🎯 **BORSAANALIZ AI - TAM EXCEL VERİ ANALİZİ**

**📊 GÜNCEL EXCEL RAPORU:** {excel_result['data']['excel_file']} ({excel_date})
**⏰ ANALİZ ZAMANI:** {excel_result['data']['timestamp']}
**📈 TOPLAM HİSSE:** {excel_result['data']['sheets'].get('Sinyaller', {}).get('toplam_hisse', 0)}+

**❓ KULLANICI SORUSU:** {question}

"""
            
            # BULUNAN VERİLERİ EKLE
            if analysis.get("hisse"):
                hisse = analysis["hisse"]
                prompt += f"""📈 **HİSSE ANALİZİ: {hisse['adi']}**

**TEKNİK GÖSTERGELER:**
"""
                # Önemli alanları göster
                important_fields = ['Close', 'Open', 'High', 'Low', 'Hacim', 'VMA',
                                  'EMA_8', 'EMA_21', 'EMA_55', 'Pivot', 'Trend',
                                  'S1', 'R1', 'BB_UPPER', 'BB_LOWER', 'Pearson55']
                
                for field in important_fields:
                    if field in hisse["veriler"]:
                        value = hisse["veriler"][field]
                        prompt += f"- **{field}:** {value}\n"
                
                prompt += f"\n**NOT:** {hisse['adi']} hissesi Excel raporunda bulundu. Yukarıdaki değerler GERÇEKTİR.\n\n"
            
            if analysis.get("endeks"):
                endeks = analysis["endeks"]
                prompt += f"""📊 **ENDEKS ANALİZİ:** {endeks['bulunan_terim']}

**ENDEKS VERİLERİ (İlk 5):**
"""
                for i, row in enumerate(endeks["veriler"][:5], 1):
                    prompt += f"{i}. {row}\n"
                
                prompt += f"\n**Toplam Endeks:** {endeks['toplam_endeks']}\n\n"
            
            if analysis.get("fon_emtia"):
                fon = analysis["fon_emtia"]
                prompt += f"""💰 **FON/EMTİA/DÖVİZ ANALİZİ:** {fon['bulunan_terim']}

**VERİLER (İlk 10):**
"""
                for i, row in enumerate(fon["veriler"][:10], 1):
                    prompt += f"{i}. {row}\n"
                
                prompt += f"\n**Toplam Veri:** {fon['toplam_veri']}\n\n"
            
            # Eğer hiç veri bulunamadıysa
            if not any([analysis.get("hisse"), analysis.get("endeks"), analysis.get("fon_emtia")]):
                prompt += """⚠️ **NOT:** Sorunuzda belirli bir hisse/endeks/emtia bulunamadı.

**ANCAK** Excel raporunda 630+ hisse, endeksler ve fon/emtia/döviz verileri mevcut.

"""
            
            prompt += """🎯 **ANALİZ TALİMATLARI:**
1. Yukarıdaki GERÇEK Excel verilerini KULLANARAK teknik analiz yap
2. **VMA (Volume Moving Algorithm)** bazlı yorum yap - VMA değerini analiz et
3. **RSI/MACD YOK** - Onlardan bahsetme
4. Sayısal değerlerle açık ve net konuş (Örnek: "Close: 115.70 TL")
5. **YATIRIM TAVSİYESİ VERME** - Sadece teknik analiz yap
6. Kısa ve öz olsun (max 250 kelime)

**📊 ANALİZ FORMATI:**
• 📈 Veri Özeti
• 🔍 Teknik Yorum (VMA bazlı)
• ⚠️ Kritik Seviyeler
• 💡 Gözlemler (bilgi amaçlı)

**CEVAP:**"""
            
            print(f"📝 Prompt hazır ({len(prompt):,} karakter)")
            
            # 7. DEEPSEEK API'Yİ ÇAĞIR
            ai_start = datetime.now()
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
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz-AI/2.0'
                }
            )
            
            print("🔄 DeepSeek API çağrılıyor (TÜM verilerle)...")
            response = urllib.request.urlopen(req, timeout=45)
            response_data = json.loads(response.read().decode('utf-8'))
            ai_time = (datetime.now() - ai_start).total_seconds()
            
            print(f"✅ DeepSeek yanıt aldı ({ai_time:.2f} sn)")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # 8. YANIT VER
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                total_time = excel_time + ai_time
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "tokens": response_data.get('usage', {}).get('total_tokens', 0),
                    "excel_data_used": True,
                    "hisse": analysis.get("hisse", {}).get("adi") if analysis.get("hisse") else None,
                    "performance": {
                        "excel_okuma_sn": round(excel_time, 2),
                        "ai_analiz_sn": round(ai_time, 2),
                        "toplam_sn": round(total_time, 2),
                        "hisse_sayisi": excel_result["data"]["sheets"].get("Sinyaller", {}).get("toplam_hisse", 0)
                    },
                    "excel_info": {
                        "dosya": excel_result["data"]["excel_file"],
                        "tarih": excel_date,
                        "sayfalar": list(excel_result["data"]["sheets"].keys())
                    }
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 YANIT GÖNDERİLDİ! Toplam süre: {total_time:.2f} sn")
                print("="*70 + "\n")
                
            else:
                raise Exception("API geçersiz yanıt")
                
        except Exception as e:
            print(f"❌ HATA: {str(e)}")
            print("="*70 + "\n")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "error": str(e),
                "help": "Sistem geçici olarak hizmet veremiyor. Lütfen daha sonra tekrar deneyin."
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
