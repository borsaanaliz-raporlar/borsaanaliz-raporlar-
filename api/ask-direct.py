# /api/ask-direct.py (AKILLI SİSTEM - SORU TİPLERİNE GÖRE YANIT)
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
        
        # Sadece Sinyaller sayfasını oku (performans için)
        if "Sinyaller" in wb.sheetnames:
            ws = wb["Sinyaller"]
            print(f"📊 Sinyaller okunuyor...")
            
            headers_clean = []
            for col in range(1, 100):  # 100 sütun yeterli
                cell_val = ws.cell(row=1, column=col).value
                if cell_val:
                    headers_clean.append(clean_header(str(cell_val)))
                else:
                    break
            
            sinyaller_data = {}
            max_rows = min(1001, ws.max_row)  # 1000 hisse yeterli
            
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
        
        wb.close()
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {str(e)}")
        return {"success": False, "error": str(e)}

def find_in_excel_data(question, excel_data):
    """Excel verilerinde arama yap"""
    try:
        question_upper = question.upper()
        
        # Önce hisse kısaltmalarını ara
        search_terms = []
        for word in re.findall(r'[A-Z0-9]+', question_upper):
            if len(word) >= 2:  # En az 2 karakter
                search_terms.append(word)
        
        print(f"🔍 Aranan: {search_terms}")
        
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            for term in search_terms:
                for hisse_adi, hisse_veriler in hisseler.items():
                    hisse_clean = re.sub(r'[^A-Z0-9]', '', hisse_adi.upper())
                    if term == hisse_clean:  # Tam eşleşme
                        print(f"✅ {hisse_adi} bulundu")
                        return {
                            "found": True,
                            "data": hisse_veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        return {
            "found": False,
            "data": None,
            "sayfa": None,
            "name": None
        }
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {"found": False, "error": str(e)}

def analyze_question_type(question):
    """Sorunun tipini analiz et"""
    question_lower = question.lower()
    
    # Teşekkür/beğeni soruları
    teşekkür_kelimeleri = ['teşekkür', 'sağ ol', 'güzel', 'harika', 'süper', 'müthiş', 'bravo']
    for kelime in teşekkür_kelimeleri:
        if kelime in question_lower:
            return "teşekkür"
    
    # Sistem hakkında sorular
    sistem_kelimeleri = ['kim yaptı', 'kim hazırladı', 'nasıl çalışır', 'nedir', 'sistem', 'ai', 'yapay zeka']
    for kelime in sistem_kelimeleri:
        if kelime in question_lower:
            return "sistem"
    
    # Hisse analizi isteği (varsayılan)
    hisse_kelimeleri = ['analiz', 'durum', 'ne oldu', 'kaç', 'fiyat', 'hisse', 'endeks', 'fon']
    for kelime in hisse_kelimeleri:
        if kelime in question_lower:
            return "analiz"
    
    return "analiz"  # Varsayılan olarak analiz

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        excel_url, excel_date = find_latest_excel()
        
        response = json.dumps({
            "status": "online",
            "ai": "BORSAANALIZ AI",
            "excel": {
                "dosya": os.path.basename(excel_url),
                "tarih": excel_date,
                "not": "Güncel hisse analizleri için POST isteği gönderin"
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
            
            # 2. Soru tipini analiz et
            question_type = analyze_question_type(question)
            print(f"🔍 Soru tipi: {question_type}")
            
            # 3. TEŞEKKÜR veya SİSTEM SORUSU ise direkt yanıtla
            if question_type in ["teşekkür", "sistem"]:
                if question_type == "teşekkür":
                    answer = "🌟 **Teşekkür ederim!**\n\nBorsaAnaliz AI olarak size yardımcı olmaktan mutluluk duyuyorum. Başka hangi hisseyi analiz etmemi istersiniz?"
                else:  # sistem
                    answer = "🤖 **BorsaAnaliz AI Hakkında**\n\nBu sistem, BorsaAnaliz ekibi tarafından geliştirilmiş bir yapay zeka asistanıdır. Günlük olarak güncellenen Excel raporlarından gerçek verilerle teknik analiz yapar.\n\n📊 **Özellikler:**\n• 630+ hisse analizi\n• Gerçek zamanlı veriler\n• VMA, EMA, Pivot seviyeleri\n• Teknik durum değerlendirmesi\n\nSormak istediğiniz başka bir hisse var mı?"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": False,
                    "question_type": question_type
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Yanıt gönderildi (direkt)")
                return
            
            # 4. ANALİZ SORUSU ise Excel'den veri al
            print("🔍 Excel bulunuyor...")
            excel_start = datetime.now()
            excel_url, excel_date = find_latest_excel()
            print(f"✅ Excel: {os.path.basename(excel_url)} ({excel_date})")
            
            # 5. Excel'i oku
            print("📥 Excel okunuyor...")
            excel_result = read_all_excel_data(excel_url)
            
            if not excel_result.get("success"):
                print("❌ Excel okunamadı")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
            
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Excel dosyası okunamadı. Lütfen daha sonra tekrar deneyin.",
                    "excel_data_used": False
                }, ensure_ascii=False)
            
                self.wfile.write(result.encode('utf-8'))
                return
            
            excel_time = (datetime.now() - excel_start).total_seconds()
            print(f"⏱️ Excel: {excel_time:.1f} sn")
            
            # 6. Sembolü bul
            print("🔍 Sembol aranıyor...")
            analysis = find_in_excel_data(question, excel_result["data"])
            
            # 7. Eğer sembol bulunamadıysa
            if not analysis.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Hisse bulunamadı. Lütfen hisse kodunu kontrol edin.\n\n📋 **Örnek hisseler:** FROTO, THYAO, TUPRS, SASA, EREGL, KCHOL, ASELS, GARAN\n\n💡 **İpucu:** Sadece hisse kodunu yazın (örnek: 'FROTO')",
                    "excel_data_used": False,
                    "question_type": "analiz"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Yanıt gönderildi (hisse bulunamadı)")
                return
            
            # 8. Bulunan sembol için kısa analiz oluştur
            sembol_data = analysis["data"]
            sembol_name = analysis["name"]
            
            # Gerekli alanları kontrol et
            required_fields = ['Close', 'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55', 'Pivot', 'S1', 'R1', 'DURUM']
            
            # Varsayılan değerler
            values = {}
            for field in required_fields:
                values[field] = sembol_data.get(field, "Bilinmiyor")
            
            # Analiz oluştur
            answer_lines = []
            
            # 1. Fiyat satırı
            if values['Close'] != "Bilinmiyor":
                answer_lines.append(f"📈 **Fiyat:** {values['Close']} TL")
            
            # 2. VMA satırı
            if values['VMA trend algo'] != "Bilinmiyor":
                vma_text = str(values['VMA trend algo'])
                if "POZİTİF" in vma_text.upper():
                    vma_yorum = "↑ Hacim trendi güçlü"
                elif "NEGATİF" in vma_text.upper():
                    vma_yorum = "↓ Hacim trendi zayıf"
                else:
                    vma_yorum = "↔ Hacim trendi nötr"
                answer_lines.append(f"📊 **VMA:** {vma_text} - {vma_yorum}")
            
            # 3. EMA satırı
            if all(v != "Bilinmiyor" for v in [values['EMA_8'], values['EMA_21'], values['EMA_55']]):
                ema8 = float(values['EMA_8']) if isinstance(values['EMA_8'], (int, float)) else 0
                ema21 = float(values['EMA_21']) if isinstance(values['EMA_21'], (int, float)) else 0
                ema55 = float(values['EMA_55']) if isinstance(values['EMA_55'], (int, float)) else 0
                
                if ema8 > ema21 > ema55:
                    ema_yorum = "✓ Güçlü yükseliş"
                elif ema8 < ema21 < ema55:
                    ema_yorum = "✗ Güçlü düşüş"
                else:
                    ema_yorum = "↔ Karışık trend"
                
                answer_lines.append(f"📉 **EMA:** {ema_yorum} (8:{ema8:.2f} 21:{ema21:.2f} 55:{ema55:.2f})")
            
            # 4. Seviyeler satırı
            if all(v != "Bilinmiyor" for v in [values['Pivot'], values['S1'], values['R1']]):
                answer_lines.append(f"⚖️ **Seviyeler:** P:{values['Pivot']} S1:{values['S1']} R1:{values['R1']}")
            
            # 5. Durum satırı
            if values['DURUM'] != "Bilinmiyor":
                durum = str(values['DURUM'])
                if "POZİTİF" in durum.upper():
                    durum_emoji = "🟢"
                elif "NEGATİF" in durum.upper():
                    durum_emoji = "🔴"
                else:
                    durum_emoji = "🟡"
                answer_lines.append(f"🎯 **Durum:** {durum_emoji} {durum}")
            
            # 6. Tarih bilgisi
            answer_lines.append(f"\n📅 **Veri Tarihi:** {excel_date}")
            
            answer = "\n".join(answer_lines)
            
            # 9. Yanıtı gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            result = json.dumps({
                "success": True,
                "answer": answer,
                "excel_data_used": True,
                "symbol": sembol_name,
                "sheet": analysis["sayfa"],
                "question_type": "analiz",
                "time_sec": round(excel_time, 1)
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))
            print(f"📤 Yanıt gönderildi ({sembol_name})")
            print("=== TAMAMLANDI ===\n")
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası: {str(e)[:100]}",
                "excel_data_used": False
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
