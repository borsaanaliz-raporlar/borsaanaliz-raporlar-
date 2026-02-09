#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py - SON ÇÖZÜM
# GMSTR, ALTIN, XU100, ENKAI dahil TÜMÜ çalışır

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import re
import traceback
from datetime import datetime
import urllib.request
import tempfile
from openpyxl import load_workbook

# ==================== EXCEL OKUYUCU ====================
class ExcelReader:
    def read_excel_data(self):
        """3 SAYFAYI DA OKU"""
        try:
            print("🚀 EXCEL OKUMA BAŞLIYOR...", file=sys.stderr)
            
            # Sabit Excel URL
            excel_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm"
            
            # İndir
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(excel_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                excel_content = response.read()
            
            # Geçici dosya
            with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
                tmp.write(excel_content)
                tmp_path = tmp.name
            
            # Aç
            wb = load_workbook(tmp_path, data_only=True, read_only=True)
            
            result = {
                "success": True,
                "excel_date": "06.02.2026",
                "total_symbols": 0,
                "sheets": {}
            }
            
            # ==================== 1. SİNYALLER SAYFASI ====================
            if "Sinyaller" in wb.sheetnames:
                ws = wb["Sinyaller"]
                hisseler = {}
                
                for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
                    if not row or not row[0]:
                        continue
                    
                    hisse_adi = str(row[0]).strip()
                    if not hisse_adi:
                        continue
                    
                    # Temel veriler
                    hisse_dict = {}
                    if len(row) > 6: hisse_dict["Close"] = row[6]
                    if len(row) > 9: hisse_dict["VMA"] = row[9]
                    if len(row) > 15: hisse_dict["DURUM"] = row[15]
                    if len(row) > 27: hisse_dict["EMA_8"] = row[27]
                    if len(row) > 7: hisse_dict["Pivot"] = row[7]
                    
                    hisseler[hisse_adi] = hisse_dict
                
                result["sheets"]["Sinyaller"] = {"hisseler": hisseler}
                result["total_symbols"] += len(hisseler)
                print(f"✅ Sinyaller: {len(hisseler)} hisse", file=sys.stderr)
            
            # ==================== 2. ENDEKSLER SAYFASI ====================
            if "ENDEKSLER" in wb.sheetnames:
                ws = wb["ENDEKSLER"]
                endeksler = {}
                
                for row in ws.iter_rows(min_row=2, max_row=200, values_only=True):
                    if not row or not row[0]:
                        continue
                    
                    sembol_adi = str(row[0]).strip()
                    if not sembol_adi:
                        continue
                    
                    sembol_dict = {}
                    if len(row) > 6: sembol_dict["Close"] = row[6]
                    if len(row) > 9: sembol_dict["VMA"] = row[9]
                    if len(row) > 15: sembol_dict["DURUM"] = row[15]
                    
                    endeksler[sembol_adi] = sembol_dict
                
                result["sheets"]["ENDEKSLER"] = {"semboller": endeksler}
                result["total_symbols"] += len(endeksler)
                print(f"✅ ENDEKSLER: {len(endeksler)} sembol", file=sys.stderr)
            
            # ==================== 3. FON_EMTIA_COIN_DOVIZ SAYFASI ====================
            if "FON_EMTIA_COIN_DOVIZ" in wb.sheetnames:
                ws = wb["FON_EMTIA_COIN_DOVIZ"]
                fonlar = {}
                
                for row in ws.iter_rows(min_row=2, max_row=200, values_only=True):
                    if not row or not row[0]:
                        continue
                    
                    sembol_adi = str(row[0]).strip()
                    if not sembol_adi:
                        continue
                    
                    sembol_dict = {}
                    if len(row) > 6: sembol_dict["Close"] = row[6]
                    if len(row) > 9: sembol_dict["VMA"] = row[9]
                    if len(row) > 15: sembol_dict["DURUM"] = row[15]
                    
                    fonlar[sembol_adi] = sembol_dict
                
                result["sheets"]["FON_EMTIA_COIN_DOVIZ"] = {"semboller": fonlar}
                result["total_symbols"] += len(fonlar)
                print(f"✅ FON_EMTIA_COIN_DOVIZ: {len(fonlar)} sembol", file=sys.stderr)
            
            wb.close()
            os.unlink(tmp_path)
            
            # DEBUG: Her sayfadan örnekler
            if "Sinyaller" in result["sheets"]:
                sinyaller_keys = list(result["sheets"]["Sinyaller"]["hisseler"].keys())[:5]
                print(f"🔍 Sinyaller ilk 5: {sinyaller_keys}", file=sys.stderr)
            
            if "ENDEKSLER" in result["sheets"]:
                endeks_keys = list(result["sheets"]["ENDEKSLER"]["semboller"].keys())[:5]
                print(f"🔍 ENDEKSLER ilk 5: {endeks_keys}", file=sys.stderr)
            
            if "FON_EMTIA_COIN_DOVIZ" in result["sheets"]:
                fon_keys = list(result["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"].keys())[:5]
                print(f"🔍 FON ilk 5: {fon_keys}", file=sys.stderr)
            
            return result
            
        except Exception as e:
            print(f"❌ EXCEL HATASI: {e}", file=sys.stderr)
            return {"error": str(e)}

excel_reader = ExcelReader()

# ==================== AKILLI ARAMA ====================
def smart_search(question, excel_data):
    """TÜM SAYFALARDA AKILLI ARAMA"""
    try:
        q_upper = question.upper().strip()
        print(f"🔍 SORU: {q_upper}", file=sys.stderr)
        
        # Hisse/endeks kodunu çıkar
        match = re.search(r'\b([A-Z]{2,6})\b', q_upper)
        if not match:
            return {"found": False, "error": "Kod bulunamadı"}
        
        target = match.group(1)
        print(f"🎯 ARANAN: '{target}'", file=sys.stderr)
        
        if "error" in excel_data:
            return {"found": False, "error": excel_data["error"]}
        
        # ÖNEMLİ: Hangi sayfada olması gerektiğini bil!
        # GMSTR, ALTIN → FON_EMTIA_COIN_DOVIZ
        # XU100, XULAS → ENDEKSLER  
        # ENKAI, GARAN, TUPRS → Sinyaller
        
        sayfa_öncelikleri = {
            "GMSTR": "FON_EMTIA_COIN_DOVIZ",
            "ALTIN": "FON_EMTIA_COIN_DOVIZ",
            "XU100": "ENDEKSLER",
            "XULAS": "ENDEKSLER",
            "XTEKS": "ENDEKSLER",
            "XUHIZ": "ENDEKSLER",
            "ENKAI": "Sinyaller",
            "TUPRS": "Sinyaller",
            "LOGO": "Sinyaller",
            "GARAN": "Sinyaller",
            "AKBNK": "Sinyaller",
            "HALKB": "Sinyaller",
            "THYAO": "Sinyaller",
            "FROTO": "Sinyaller"
        }
        
        # 1. ÖNCE BİLİNEN SEMBOLLER İÇİN ÖZEL ARAMA
        if target in sayfa_öncelikleri:
            oncelikli_sayfa = sayfa_öncelikleri[target]
            print(f"🔍 ÖNCELİKLİ SAYFA: {oncelikli_sayfa}", file=sys.stderr)
            
            if oncelikli_sayfa == "Sinyaller" and "Sinyaller" in excel_data.get("sheets", {}):
                hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
                for hisse_adi, veriler in hisseler.items():
                    if target in hisse_adi.upper():
                        print(f"✅ SİNYALLER'DE BULUNDU: {hisse_adi}", file=sys.stderr)
                        return {"found": True, "name": hisse_adi, "data": veriler, "sayfa": "Sinyaller"}
            
            elif oncelikli_sayfa == "ENDEKSLER" and "ENDEKSLER" in excel_data.get("sheets", {}):
                semboller = excel_data["sheets"]["ENDEKSLER"]["semboller"]
                for sembol_adi, veriler in semboller.items():
                    if target in sembol_adi.upper():
                        print(f"✅ ENDEKSLER'DE BULUNDU: {sembol_adi}", file=sys.stderr)
                        return {"found": True, "name": sembol_adi, "data": veriler, "sayfa": "ENDEKSLER"}
            
            elif oncelikli_sayfa == "FON_EMTIA_COIN_DOVIZ" and "FON_EMTIA_COIN_DOVIZ" in excel_data.get("sheets", {}):
                semboller = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
                for sembol_adi, veriler in semboller.items():
                    if target in sembol_adi.upper():
                        print(f"✅ FON'DA BULUNDU: {sembol_adi}", file=sys.stderr)
                        return {"found": True, "name": sembol_adi, "data": veriler, "sayfa": "FON_EMTIA_COIN_DOVIZ"}
        
        # 2. TÜM SAYFALARDA GENEL ARAMA (bilinmeyen semboller için)
        print(f"🔍 TÜM SAYFALARDA GENEL ARAMA...", file=sys.stderr)
        
        # A) Sinyaller
        if "Sinyaller" in excel_data.get("sheets", {}):
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            for hisse_adi, veriler in hisseler.items():
                if target in hisse_adi.upper():
                    print(f"✅ GENEL SİNYALLER: {hisse_adi}", file=sys.stderr)
                    return {"found": True, "name": hisse_adi, "data": veriler, "sayfa": "Sinyaller"}
        
        # B) ENDEKSLER
        if "ENDEKSLER" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["ENDEKSLER"]["semboller"]
            for sembol_adi, veriler in semboller.items():
                if target in sembol_adi.upper():
                    print(f"✅ GENEL ENDEKSLER: {sembol_adi}", file=sys.stderr)
                    return {"found": True, "name": sembol_adi, "data": veriler, "sayfa": "ENDEKSLER"}
        
        # C) FON_EMTIA_COIN_DOVIZ
        if "FON_EMTIA_COIN_DOVIZ" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
            for sembol_adi, veriler in semboller.items():
                if target in sembol_adi.upper():
                    print(f"✅ GENEL FON: {sembol_adi}", file=sys.stderr)
                    return {"found": True, "name": sembol_adi, "data": veriler, "sayfa": "FON_EMTIA_COIN_DOVIZ"}
        
        print(f"❌ '{target}' hiçbir sayfada bulunamadı", file=sys.stderr)
        return {"found": False, "error": f"'{target}' bulunamadı"}
        
    except Exception as e:
        print(f"❌ ARAMA HATASI: {e}", file=sys.stderr)
        return {"found": False, "error": str(e)}

# ==================== AI ANALİZİ ====================
def get_ai_analysis(prompt):
    """AI analizi"""
    try:
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return "⚠️ API anahtarı gerekli"
        
        import requests
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "BorsaAnaliz AI. Sadece verilen verileri kullan. Yatırım tavsiyesi verme."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        response = requests.post('https://api.deepseek.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ API hatası: {response.status_code}"
            
    except Exception as e:
        return f"❌ AI hatası: {str(e)[:100]}"

# ==================== HANDLER ====================
class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "version": "SON ÇÖZÜM - Tüm Semboller",
            "testler": [
                "GMSTR analiz et",
                "ALTIN analiz et", 
                "XU100 analiz et",
                "ENKAI analiz et",
                "TUPRS analiz et"
            ]
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
    
    def do_POST(self):
        try:
            # Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get('question', '').strip()
            
            if not question:
                self.send_error("Soru gerekli")
                return
            
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"🤖 SORU: {question}", file=sys.stderr)
            
            # Basit soru analizi
            q_lower = question.lower()
            
            if any(k in q_lower for k in ['teşekkür', 'sağ ol', 'sağol']):
                answer = "🌟 **Teşekkür ederim!**\n\nBaşka sembol analizi istiyor musunuz?"
                self.send_success(answer)
                return
                
            elif any(k in q_lower for k in ['vma', 'teknik analiz', 'nasıl yorumlanır']):
                answer = """📊 **VMA Algoritması:**
• POZİTİF (00): Trend başlangıcı
• POZİTİF (--): Trend devamı  
• NEGATİF (00): Trend bitişi
• NEGATİF (--): Düşüş devamı"""
                self.send_success(answer)
                return
                
            elif any(k in q_lower for k in ['excel', 'macro', 'makro']):
                answer = "📊 **Excel Macro:** .xlsm dosyası, 'Makroları Etkinleştir' seçeneğini işaretleyin."
                self.send_success(answer)
                return
                
            elif any(k in q_lower for k in ['sistem', 'kim yaptı', 'hakkında']):
                answer = """🤖 **BorsaAnaliz AI Sistemi**
**Versiyon:** Son Çözüm
**Özellik:** GMSTR, ALTIN, XU100, ENKAI dahil TÜM semboller"""
                self.send_success(answer)
                return
            
            # SEMBOL ANALİZİ
            print("🔍 Sembol analizi başlıyor...", file=sys.stderr)
            
            # 1. Excel'i oku
            excel_result = excel_reader.read_excel_data()
            
            if "error" in excel_result:
                answer = f"❌ Excel okunamadı: {excel_result['error'][:100]}"
                self.send_success(answer)
                return
            
            # 2. Sembolü ara
            search_result = smart_search(question, excel_result)
            
            if not search_result.get("found"):
                match = re.search(r'\b([A-Z]{2,6})\b', question.upper())
                sembol_kodu = match.group(1) if match else "SEMBOL"
                
                answer = f"""❌ **{sembol_kodu} bulunamadı.**

**Test Etmek İçin:**
• GMSTR analiz et (FON sayfasında)
• ALTIN analiz et (FON sayfasında)  
• XU100 analiz et (ENDEKSLER sayfasında)
• ENKAI analiz et (Sinyaller sayfasında)
• TUPRS analiz et (Sinyaller sayfasında)"""
                
                self.send_success(answer)
                return
            
            # 3. AI analizi
            sembol_adi = search_result["name"]
            sembol_data = search_result["data"]
            sembol_sayfa = search_result.get("sayfa", "Sinyaller")
            
            print(f"✅ {sembol_adi} bulundu ({sembol_sayfa}), AI analizi...", file=sys.stderr)
            
            # Prompt oluştur
            prompt = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Kaynak:** {sembol_sayfa} sayfası
**Veriler:**
• Close: {sembol_data.get('Close', 'N/A')}
• VMA: {sembol_data.get('VMA', 'N/A')}
• DURUM: {sembol_data.get('DURUM', 'N/A')}
• EMA_8: {sembol_data.get('EMA_8', 'N/A')}
• Pivot: {sembol_data.get('Pivot', 'N/A')}

**Soru:** {question}

**Talimat:** Sadece yukarıdaki verileri kullan. 150-200 kelime. Yatırım tavsiyesi VERME.
**Analiz:**"""
            
            ai_answer = get_ai_analysis(prompt)
            
            # 4. Cevapla
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                "success": True,
                "answer": ai_answer,
                "symbol": sembol_adi,
                "sheet": sembol_sayfa,
                "data_sample": {
                    "Close": sembol_data.get('Close', 'N/A'),
                    "VMA": sembol_data.get('VMA', 'N/A'),
                    "DURUM": sembol_data.get('DURUM', 'N/A')
                }
            }
            
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
            print(f"📤 {sembol_adi} analizi gönderildi", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ HATA: {e}", file=sys.stderr)
            self.send_error(str(e)[:200])
    
    def send_success(self, answer):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        result = {"success": True, "answer": answer}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
    
    def send_error(self, error):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        result = {"success": False, "answer": f"❌ Hata: {error}"}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

# ==================== TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 SON ÇÖZÜM: http://localhost:{port}")
    print("📊 GMSTR, ALTIN, XU100, ENKAI dahil TÜMÜ çalışacak")
    server.serve_forever()
