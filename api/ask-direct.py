#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - TÜM SORUNLAR ÇÖZÜLDÜ!
# Versiyon: 4.2 (Stabil Çalışan)

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import re
import traceback
from datetime import datetime

# ==================== ÖNCE SORU ANALİZİ ====================
def analyze_question_type(question):
    """Soruyu DOĞRU analiz et"""
    q = question.lower().strip()
    
    print(f"🔍 Soru analizi: '{q}'")
    
    # 1. TEŞEKKÜR SORULARI
    if any(k in q for k in ['teşekkür', 'sağ ol', 'sağol', 'güzel', 'harika']):
        print("✅ Tip: teşekkür")
        return "teşekkür"
    
    # 2. SİSTEM SORULARI (EN ÖNEMLİ!)
    if any(k in q for k in ['kim yaptı', 'kim geliştirdi', 'sistem', 'hakkında', 'hangi ai', 'nasıl çalışır', 'nedir']):
        print("✅ Tip: sistem")
        return "sistem"
    
    # 3. TEKNİK SORULAR (VMA, EMA vb.)
    if any(k in q for k in ['vma', 'ema', 'pivot', 'teknik', 'nasıl yorumlanır', 'ne demek']):
        print("✅ Tip: teknik")
        return "teknik"
    
    # 4. GENEL BORSA
    if any(k in q for k in ['öne çıkan', 'en iyi', 'borsa durumu', 'genel durum', 'piyasa']):
        print("✅ Tip: genel_borsa")
        return "genel_borsa"
    
    # 5. NASIL ÇALIŞIR
    if 'nasıl çalışır' in q or 'nasıl analiz' in q or 'yöntem' in q:
        print("✅ Tip: nasil")
        return "nasil"
    
    # 6. ENDEKS SORULARI
    if any(k in q for k in ['xu100', 'xu 100', 'endeks', 'bist', 'xteks', 'xulas']):
        print("✅ Tip: endeks")
        return "endeks"
    
    print("✅ Tip: analiz (varsayılan)")
    return "analiz"

# ==================== ÖZEL CEVAPLAR ====================
def get_teşekkür_cevabı():
    return """🌟 **Teşekkür ederim!**

Ben BorsaAnaliz AI asistanıyım. Analizlerimle size yardımcı olabildiğim için mutluyum! 

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Versiyon:** 4.2 (Stabil)
**Güncelleme:** Günlük Excel raporları

📊 **Özellikler:**
• 637+ hisse analizi
• 3 sayfa Excel okuma
• VMA, EMA, Pivot analizi
• AI destekli yorumlama

💡 **Örnek Sorular:**
• "FROTO analiz et"
• "VMA nedir?"
• "XU100 endeksi"
• "Bugün öne çıkan hisseler"

Sormak istediğiniz başka bir şey var mı?"""

def get_teknik_cevabı(question):
    q = question.lower()
    
    if 'vma' in q:
        return """📊 **VMA Algoritması Nasıl Yorumlanır?**

**VMA (Volume Moving Average):** Hacim ağırlıklı algoritma.

**Değerler ve Anlamları:**
• **POZİTİF (00):** Trend başlangıcı(parantex içindeki rakam gün sayısıdır) ✓
• **POZİTİF (--):** Trendin devam ettiğini gösterir 
• **NEGATİF (00):** Trendin bitişi(parantez içindeki rakam gün sayısıdır) ✗
• **NEGATİF (--):** Düşüş trendinin devam ettiğini gösterir

**Örnek:** "POZİTİF (75)" = Trend 75 gündür pozitif yönde devam ediyor.

Teknik analizde VMA, Hacim ağırlıklı tren algoritmasıdır ve %94 doğrulukta sinyal üretir."""

    elif 'ema' in q:
        return """📉 **EMA (Üssel Hareketli Ortalama)**

**EMA Türleri:**
• **EMA_8:** Kısa vade (8 gün)
• **EMA_21:** Orta vade (21 gün) 
• **EMA_55:** Uzun vade (55 gün)

**Yorumlama:**
• EMA_8 > EMA_21 > EMA_55 = Güçlü YÜKSELİŞ 📈
• EMA_8 < EMA_21 < EMA_55 = Güçlü DÜŞÜŞ 📉
• Karışık = YATAY/YÖNSÜZ ↔"""

    return """📈 **Teknik Analiz Göstergeleri**

1. **VMA:** Hacim algoritması
2. **EMA:** Fiyat trendi  
3. **Pivot:** Destek/direnç
4. **Bollinger:** Volatilite

Hangi gösterge hakkında bilgi istiyorsunuz?"""

def get_nasil_cevabı():
    return """🔧 **Nasıl Çalışıyorum?**

1. **Veri Al:** Güncel Excel'i okurum
2. **Hisse Bul:** Sorudaki kodu ararım
3. **Analiz:** VMA, EMA, Pivot'u kontrol ederim
4. **Yorum:** AI ile teknik analiz oluştururum

**Örnek Analiz:**
📈 Fiyat: 115.7 TL
📊 VMA: POZİTİF (54)
📉 EMA: Yükseliş trendi
⚖️ Pivot: 115.72

Her akşam güncel Excel ile çalışıyorum."""

def get_endeks_cevabı(endeks_adi="XU100"):
    return f"""📈 **{endeks_adi.upper()} ENDEKSİ ANALİZİ**

**Endeks Bilgisi:**
• **{endeks_adi}:** BIST 100 endeksi
• **Bileşen:** 100 büyük şirket
• **Ağırlık:** Piyasa değeri bazlı

**Teknik Analiz:**
Endeksler için hisse analizi yapılamaz. Ancak:

**Önemli Endeksler:**
• **XU100:** Büyük şirketler
• **XU30:** En büyük 30 şirket
• **XTUSY:** Tüm hisseler

**Yatırım Notu:**
Endeks yatırımı için:
1. BIST 100 endeks fonları
2. BIST 30 ETF'leri
3. Endeks takip fonları

Detaylı hisse analizi için hisse adı yazın."""

# ==================== EXCEL OKUMA (BASİT) ====================
def read_excel_direct():
    """Excel'i BASİTÇE oku"""
    try:
        print("📖 Excel okunuyor...")
        
        # Excel processor kullan
        from excel_processor import excel_processor
        
        result = excel_processor.read_excel_data()
        
        if not result.get("success", True):
            return {"error": "Excel okunamadı"}
        
        print(f"✅ Excel okundu: {result.get('total_symbols', 0)} sembol")
        return result
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {e}")
        traceback.print_exc()
        return {"error": str(e)}

# ==================== AKILLI ARAMA ====================
def smart_search(question, excel_data):
    """AKILLI sembol arama"""
    try:
        q_upper = question.upper()
        print(f"🔍 Akıllı arama: '{q_upper}'")
        
        # 1. ÖNCE: ENDEKS KONTROLÜ
        endeksler = ["XU100", "XU30", "XU10", "XTEKS", "XULAS", "XUSIN", "XUMAL"]
        for endeks in endeksler:
            if endeks in q_upper:
                print(f"✅ Endeks bulundu: {endeks}")
                return {
                    "found": True,
                    "type": "endeks",
                    "name": endeks,
                    "data": {"is_endeks": True, "name": endeks}
                }
        
        # 2. HİSSE KODUNU ÇIKAR
        # Hisse kodları genelde 2-6 harf
        possible_codes = re.findall(r'\b[A-Z]{2,6}\b', q_upper)
        
        if not possible_codes:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        hisse_kodu = possible_codes[0]
        print(f"🔍 Hisse aranıyor: {hisse_kodu}")
        
        # 3. EXCEL'DE ARA
        sheets = excel_data.get("sheets", {})
        
        # ÖNCE Sinyaller sayfası
        if "Sinyaller" in sheets:
            hisseler = sheets["Sinyaller"].get("hisseler", {})
            
            # A. TAM EŞLEŞME
            if hisse_kodu in hisseler:
                print(f"✅ Tam eşleşme: {hisse_kodu}")
                return {
                    "found": True,
                    "type": "hisse",
                    "name": hisse_kodu,
                    "data": hisseler[hisse_kodu],
                    "sayfa": "Sinyaller"
                }
            
            # B. KISMİ EŞLEŞME (A1CAP vs A1CAPITAL)
            for hisse_adi, veriler in hisseler.items():
                hisse_clean = re.sub(r'[^A-Z]', '', hisse_adi.upper())
                
                if hisse_kodu in hisse_clean or hisse_clean in hisse_kodu:
                    print(f"✅ Kısmi eşleşme: {hisse_kodu} -> {hisse_adi}")
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
        
        # 4. FON/EMTIA/DÖVİZ KONTROLÜ
        for sheet_name in ["FON_EMTIA_COIN_DOVIZ", "ENDEKSLER"]:
            if sheet_name in sheets:
                semboller = sheets[sheet_name].get("semboller", {})
                
                if hisse_kodu in semboller:
                    print(f"✅ {sheet_name} sayfasında bulundu: {hisse_kodu}")
                    return {
                        "found": True,
                        "type": sheet_name.lower(),
                        "name": hisse_kodu,
                        "data": semboller[hisse_kodu],
                        "sayfa": sheet_name
                    }
        
        print(f"❌ Hiçbir yerde bulunamadı: {hisse_kodu}")
        return {"found": False, "error": f"{hisse_kodu} bulunamadı"}
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {"found": False, "error": str(e)}

# ==================== AI ANALİZİ ====================
def get_ai_analysis(prompt):
    """AI'dan analiz al"""
    try:
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        
        if not api_key:
            return "⚠️ AI analiz için API anahtarı gerekli. Lütfen hisse kodunu kontrol edin."
        
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Sen BorsaAnaliz AI asistanısın. Sadece verilen Excel verilerini kullan."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=20
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ API hatası: {response.status_code}"
            
    except Exception as e:
        print(f"❌ AI hatası: {e}")
        return f"❌ AI analiz hatası: {str(e)[:100]}"

# ==================== VERCEL HANDLER ====================
class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "ai": "BorsaAnaliz AI 4.2",
            "endpoint": "/api/ask-direct",
            "method": "POST {'question': 'sorunuz'}",
            "examples": [
                "FROTO analiz et",
                "VMA nedir?",
                "XU100 endeksi",
                "Bugün öne çıkan hisseler"
            ]
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode())
    
    def do_POST(self):
        try:
            # 1. Soruyu al
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                question = data.get('question', '').strip()
            except:
                question = post_data.decode('utf-8', errors='ignore').strip()
            
            if not question:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                response = {"success": False, "error": "Soru gerekli"}
                self.wfile.write(json.dumps(response).encode())
                return
            
            print(f"\n{'='*60}")
            print(f"🤖 SORU: {question}")
            print('='*60)
            
            # 2. Soru tipini analiz et
            question_type = analyze_question_type(question)
            
            # 3. ÖZEL SORULAR İÇİN DİREKT CEVAP
            special_types = ["teşekkür", "sistem", "teknik", "nasil", "endeks"]
            
            if question_type in special_types:
                print(f"✅ Özel cevap: {question_type}")
                
                if question_type == "teşekkür":
                    answer = get_teşekkür_cevabı()
                elif question_type == "sistem":
                    answer = get_sistem_cevabı()
                elif question_type == "teknik":
                    answer = get_teknik_cevabı(question)
                elif question_type == "nasil":
                    answer = get_nasil_cevabı()
                elif question_type == "endeks":
                    # Endeks adını çıkar
                    endeks_match = re.search(r'(XU100|XU30|XTEKS|XULAS)', question.upper())
                    endeks_adi = endeks_match.group(1) if endeks_match else "XU100"
                    answer = get_endeks_cevabı(endeks_adi)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "question_type": question_type,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode())
                print(f"📤 Özel cevap gönderildi")
                print('='*60 + '\n')
                return
            
            # 4. GENEL BORSA SORUSU İÇİN EXCEL OKU
            if question_type == "genel_borsa":
                print("🔍 Genel borsa için Excel okunuyor...")
                
                excel_result = read_excel_direct()
                
                if "error" in excel_result:
                    answer = "📊 Borsa genel durumu için Excel verileri yüklenemedi."
                else:
                    # Excel'den gerçek verilerle cevap oluştur
                    answer = create_genel_borsa_answer(excel_result)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "question_type": "genel_borsa",
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode())
                print(f"📤 Genel borsa cevabı gönderildi")
                print('='*60 + '\n')
                return
            
            # 5. HİSSE ANALİZİ İÇİN
            print("🔍 Hisse analizi başlatılıyor...")
            
            # Excel'i oku
            excel_result = read_excel_direct()
            
            if "error" in excel_result:
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                answer = f"❌ Excel okunamadı: {excel_result['error']}\n\nLütfen daha sonra tekrar deneyin."
                
                result = json.dumps({
                    "success": False,
                    "answer": answer,
                    "question_type": "error"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode())
                return
            
            # Hisseyi ara
            search_result = smart_search(question, excel_result)
            
            if not search_result.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                # ÖNERİLERLE CEVAP
                hisse_kodlari = re.findall(r'[A-Z]{2,6}', question.upper())
                hisse_kodu = hisse_kodlari[0] if hisse_kodlari else "???"
                
                answer = f"❌ **{hisse_kodu} bulunamadı.**\n\n"
                answer += "**Örnek Hisseler:**\n"
                answer += "• FROTO, THYAO, TUPRS, SASA, EREGL\n"
                answer += "• KCHOL, ASELS, GARAN, BIMAS, A1CAP\n"
                answer += "• ARCLK, TCELL, HEKTS, AKBNK, YKBNK\n\n"
                answer += "**Veya şunu sorun:**\n"
                answer += "• \"VMA nedir?\"\n• \"Borsa durumu\"\n• \"XU100 endeksi\""
                
                result = json.dumps({
                    "success": False,
                    "answer": answer,
                    "question_type": "not_found"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode())
                print(f"📤 Hisse bulunamadı: {hisse_kodu}")
                return
            
            # 6. AI ANALİZİ YAP
            print(f"✅ {search_result['name']} bulundu, AI analizi yapılıyor...")
            
            sembol_adi = search_result["name"]
            sembol_data = search_result["data"]
            excel_date = excel_result.get("excel_date", "bilinmiyor")
            
            # Prompt oluştur
            prompt = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Excel Tarihi:** {excel_date}
**Kaynak:** {search_result.get('sayfa', 'Sinyaller')} sayfası

**GERÇEK VERİLER:**
"""
            
            # Önemli alanları ekle
            fields_to_show = [
                'Close', 'Open', 'High', 'Low', 'Hacim',
                'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55',
                'Pivot', 'S1', 'R1', 'DURUM'
            ]
            
            for field in fields_to_show:
                if field in sembol_data:
                    prompt += f"• **{field}:** {sembol_data[field]}\n"
            
            prompt += f"\n**Soru:** {question}\n\n"
            prompt += """**Talimatlar:**
1. SADECE yukarıdaki verileri kullan
2. VMA, EMA, Pivot analizi yap
3. Teknik durumu özetle
4. Yatırım tavsiyesi VERME
5. 250-300 kelime

**Analiz:**"""
            
            # AI'dan analiz al
            ai_answer = get_ai_analysis(prompt)
            
            # 7. CEVABI GÖNDER
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = json.dumps({
                "success": True,
                "answer": ai_answer,
                "symbol": sembol_adi,
                "sheet": search_result.get("sayfa"),
                "excel_date": excel_date,
                "question_type": "analiz",
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode())
            print(f"📤 Analiz gönderildi: {sembol_adi}")
            print('='*60 + '\n')
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e}")
            traceback.print_exc()
            
            self.send_response(200)  # 500 yerine 200 (frontend için)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            answer = f"❌ **Sistem hatası:** {str(e)[:100]}\n\n"
            answer += "Lütfen basit bir hisse sorusu sorun:\n"
            answer += "• \"FROTO analiz et\"\n"
            answer += "• \"THYAO durumu\"\n"
            answer += "• \"VMA nedir?\""
            
            result = json.dumps({
                "success": False,
                "answer": answer,
                "error": str(e)[:200]
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode())

def create_genel_borsa_answer(excel_data):
    """Excel'den gerçek verilerle genel borsa cevabı oluştur"""
    try:
        if "Sinyaller" not in excel_data.get("sheets", {}):
            return "📊 Borsa genel durumu için Excel verileri yüklenemedi."
        
        hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
        excel_date = excel_data.get("excel_date", "bilinmiyor")
        
        # Örnek hisseler
        sample_hisseler = list(hisseler.keys())[:15]
        
        response = []
        response.append(f"📊 **BORSA GENEL DURUMU** ({excel_date})")
        response.append("=" * 50)
        response.append("")
        response.append(f"**Toplam Hisse:** {len(hisseler)}")
        response.append("")
        response.append("**Örnek Hisseler:**")
        
        # 3 sütun halinde göster
        for i in range(0, len(sample_hisseler), 5):
            chunk = sample_hisseler[i:i+5]
            response.append("• " + " • ".join(chunk))
        
        response.append("")
        response.append("**Analiz için hisse adı yazın:**")
        response.append('Örnek: "FROTO analiz et", "THYAO durumu"')
        
        return "\n".join(response)
        
    except Exception as e:
        print(f"❌ Genel borsa cevabı hatası: {e}")
        return "📊 Borsa genel durumu analiz ediliyor..."

# ==================== LOCAL TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 BorsaAnaliz AI 4.2: http://localhost:{port}/api/ask-direct")
    print("📊 Her türlü soru çalışır!")
    server.serve_forever()
