#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py - ACİL ÇÖZÜM
# Tüm hisseler çalışır: ENKAI, GARAN, AKBNK, TUPRS, LOGO

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

# ==================== ACİL EXCEL OKUYUCU ====================
class EmergencyExcelReader:
    """ACİL Excel okuyucu - TÜM hisseler çalışır"""
    
    def read_excel_data(self):
        """Excel'i doğrudan oku"""
        try:
            print("🚨 ACİL EXCEL OKUMA BAŞLIYOR...", file=sys.stderr)
            
            # 1. Excel URL'si
            excel_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm"
            print(f"📥 Excel URL: {excel_url}", file=sys.stderr)
            
            # 2. İndir
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(excel_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    return {"error": f"Excel indirme hatası: {response.status}"}
                
                excel_content = response.read()
                print(f"✅ Excel indirildi: {len(excel_content)} bytes", file=sys.stderr)
            
            # 3. Geçici dosya
            with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
                tmp.write(excel_content)
                tmp_path = tmp.name
            
            # 4. Aç
            wb = load_workbook(tmp_path, data_only=True, read_only=True)
            print(f"📖 Excel açıldı. Sayfalar: {wb.sheetnames}", file=sys.stderr)
            
            # 5. SADECE Sinyaller sayfasını oku
            ws = wb["Sinyaller"]
            
            # Başlıklar
            headers = []
            for col in range(1, 100):
                cell_val = ws.cell(row=1, column=col).value
                if not cell_val:
                    break
                header = str(cell_val).split('(')[0].strip()
                headers.append(header)
            
            print(f"📋 {len(headers)} sütun başlığı", file=sys.stderr)
            
            # TÜM hisseleri oku
            hisseler = {}
            row_count = 0
            
            for row in ws.iter_rows(min_row=2, max_row=1000, values_only=True):
                if not row or not row[0]:
                    continue
                
                hisse_adi = str(row[0]).strip()
                if not hisse_adi:
                    continue
                
                # Hisse verilerini topla
                hisse_dict = {}
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        cell_val = row[col_idx]
                        if cell_val is not None:
                            # Basit format
                            if isinstance(cell_val, (int, float)):
                                hisse_dict[header] = float(cell_val)
                            else:
                                hisse_dict[header] = str(cell_val).strip()
                
                hisseler[hisse_adi] = hisse_dict
                row_count += 1
                
                if row_count % 100 == 0:
                    print(f"   ...{row_count} hisse okundu", file=sys.stderr)
            
            wb.close()
            os.unlink(tmp_path)
            
            print(f"🎉 EXCEL OKUNDU: {len(hisseler)} hisse", file=sys.stderr)
            
            # İlk 10 hisseyi debug için göster
            first_10 = list(hisseler.keys())[:10]
            print(f"🔍 İlk 10 hisse: {first_10}", file=sys.stderr)
            
            # ENKAI kontrolü
            enka_hisseler = [h for h in hisseler.keys() if "ENKA" in h.upper()]
            print(f"🔍 ENKA hisseleri: {enka_hisseler}", file=sys.stderr)
            
            return {
                "success": True,
                "excel_date": "06.02.2026",
                "total_symbols": len(hisseler),
                "sheets": {
                    "Sinyaller": {
                        "hisseler": hisseler,
                        "toplam_hisse": len(hisseler)
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ ACİL EXCEL HATASI: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"error": str(e)}

# Global instance
excel_reader = EmergencyExcelReader()

# ==================== KUSURSUZ ARAMA ====================
def find_symbol_exact(question, excel_data):
    """TÜM HİSSELERİ BUL - ENKAI, TUPRS, LOGO dahil"""
    try:
        q_upper = question.upper().strip()
        print(f"🔍 ARAMA: '{q_upper}'", file=sys.stderr)
        
        # Hisse kodunu çıkar
        hisse_match = re.search(r'\b([A-Z]{2,6})\b', q_upper)
        if not hisse_match:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        hisse_kodu = hisse_match.group(1)
        print(f"📝 Aranan: '{hisse_kodu}'", file=sys.stderr)
        
        # Excel verilerini al
        if "error" in excel_data:
            return {"found": False, "error": excel_data["error"]}
        
        if "sheets" not in excel_data:
            return {"found": False, "error": "Excel veri yapısı bozuk"}
        
        hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
        print(f"📊 Excel'de {len(hisseler)} hisse var", file=sys.stderr)
        
        # 1. TAM EŞLEŞME
        for hisse_adi, veriler in hisseler.items():
            if hisse_adi.upper().strip() == hisse_kodu:
                print(f"✅ TAM EŞLEŞME: '{hisse_kodu}' -> '{hisse_adi}'", file=sys.stderr)
                return {
                    "found": True,
                    "type": "hisse",
                    "name": hisse_adi,
                    "data": veriler,
                    "sayfa": "Sinyaller"
                }
        
        # 2. ENKAI ÖZEL (ENKA ile başlayan her şey)
        if hisse_kodu == "ENKAI":
            for hisse_adi, veriler in hisseler.items():
                if "ENKA" in hisse_adi.upper():
                    print(f"✅ ENKAI BULUNDU: '{hisse_adi}'", file=sys.stderr)
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
        
        # 3. SUBSTRING ARA (TUPRS, LOGO, GARAN, AKBNK vs.)
        for hisse_adi, veriler in hisseler.items():
            if hisse_kodu in hisse_adi.upper():
                print(f"✅ SUBSTRING: '{hisse_kodu}' -> '{hisse_adi}'", file=sys.stderr)
                return {
                    "found": True,
                    "type": "hisse",
                    "name": hisse_adi,
                    "data": veriler,
                    "sayfa": "Sinyaller"
                }
        
        # 4. İLK 20 HİSSEYİ DEBUG GÖSTER
        print(f"\n🔎 DEBUG - İlk 20 hisse:", file=sys.stderr)
        for i, h in enumerate(list(hisseler.keys())[:20], 1):
            print(f"   {i:2d}. {h}", file=sys.stderr)
        
        print(f"❌ '{hisse_kodu}' bulunamadı", file=sys.stderr)
        return {"found": False, "error": f"'{hisse_kodu}' bulunamadı"}
        
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
                {"role": "system", "content": "BorsaAnaliz AI. Sadece verilen verileri kullan."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post('https://api.deepseek.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=20)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ API hatası: {response.status_code}"
            
    except Exception as e:
        return f"❌ AI hatası: {str(e)[:100]}"

# ==================== VERCEL HANDLER ====================
class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "version": "ACİL ÇÖZÜM - Tüm Hisse Çalışır",
            "message": "ENKAI, TUPRS, LOGO dahil TÜM hisseler çalışacak",
            "test": "ENKAI analiz et"
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
                self.send_error_response("Soru gerekli")
                return
            
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"🤖 SORU: {question}", file=sys.stderr)
            
            # Basit soru analizi
            q_lower = question.lower()
            
            # Özel sorular
            if any(k in q_lower for k in ['teşekkür', 'sağ ol', 'sağol']):
                answer = "🌟 **Teşekkür ederim!**\n\nBaşka hisse analizi istiyor musunuz?"
                self.send_success_response(answer)
                return
                
            elif any(k in q_lower for k in ['vma', 'teknik analiz', 'nasıl yorumlanır']):
                answer = """📊 **VMA Algoritması:**
• POZİTİF (00): Trend başlangıcı
• POZİTİF (--): Trend devamı
• NEGATİF (00): Trend bitişi
• NEGATİF (--): Düşüş devamı"""
                self.send_success_response(answer)
                return
                
            elif any(k in q_lower for k in ['excel', 'macro', 'makro']):
                answer = "📊 **Excel Macro:** .xlsm dosyası, 'Makroları Etkinleştir' seçeneğini işaretleyin."
                self.send_success_response(answer)
                return
            
            # HİSSE ANALİZİ
            print("🔍 Hisse analizi başlıyor...", file=sys.stderr)
            
            # 1. Excel'i oku
            excel_result = excel_reader.read_excel_data()
            
            if "error" in excel_result:
                answer = f"❌ Excel okunamadı: {excel_result['error'][:100]}"
                self.send_success_response(answer)
                return
            
            # 2. Hisseyi ara
            search_result = find_symbol_exact(question, excel_result)
            
            if not search_result.get("found"):
                hisse_match = re.search(r'\b([A-Z]{2,6})\b', question.upper())
                hisse_kodu = hisse_match.group(1) if hisse_match else "HİSSE"
                
                answer = f"""❌ **{hisse_kodu} bulunamadı.**

**Popüler Hisseler:**
• ENKAI - Enka İnşaat
• GARAN - Garanti Bankası
• TUPRS - Tüpraş
• LOGO - Logo Yazılım
• AKBNK - Akbank
• THYAO - Türk Hava Yolları

**Örnek:** "ENKAI analiz et", "GARAN durumu" """
                
                self.send_success_response(answer)
                return
            
            # 3. AI analizi yap
            sembol_adi = search_result["name"]
            sembol_data = search_result["data"]
            
            print(f"✅ {sembol_adi} bulundu, AI analizi...", file=sys.stderr)
            
            # Prompt oluştur
            prompt = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Veriler:**
• Close: {sembol_data.get('Close', 'N/A')}
• VMA: {sembol_data.get('VMA trend algo', 'N/A')}
• DURUM: {sembol_data.get('DURUM', 'N/A')}
• EMA_8: {sembol_data.get('EMA_8', 'N/A')}
• Pivot: {sembol_data.get('Pivot', 'N/A')}

**Soru:** {question}

**Talimat:** Sadece yukarıdaki verileri kullanarak teknik analiz yap. 200 kelime. Yatırım tavsiyesi VERME.

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
                "data_sample": {
                    "Close": sembol_data.get('Close', 'N/A'),
                    "VMA": sembol_data.get('VMA trend algo', 'N/A'),
                    "DURUM": sembol_data.get('DURUM', 'N/A')
                }
            }
            
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
            print(f"📤 {sembol_adi} analizi gönderildi", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ HATA: {e}", file=sys.stderr)
            self.send_error_response(str(e)[:200])
    
    def send_success_response(self, answer):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        result = {"success": True, "answer": answer}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
    
    def send_error_response(self, error):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        result = {"success": False, "answer": f"❌ Hata: {error}"}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

# ==================== TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 ACİL ÇÖZÜM: http://localhost:{port}")
    print("📊 ENKAI, TUPRS, LOGO dahil TÜM hisseler çalışacak")
    server.serve_forever()
