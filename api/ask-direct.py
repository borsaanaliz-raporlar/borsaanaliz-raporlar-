#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - TAM ÇALIŞAN VERSİYON
# Versiyon: 4.5 (Final Fix)

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import re
import traceback
from datetime import datetime

# ==================== ÖNCE SORU ANALİZİ ====================
def analyze_question_type(question):
    """Soruyu AKILLICA analiz et"""
    q = question.lower().strip()
    
    print(f"🔍 Soru analizi: '{q}'")
    
    # 1. TEŞEKKÜR/BEĞENİ
    if any(k in q for k in ['teşekkür', 'sağ ol', 'sağol', 'güzel', 'harika', 'müthiş']):
        return "teşekkür"
    
    # 2. SİSTEM SORULARI
    if any(k in q for k in ['kim yaptı', 'kim geliştirdi', 'sistem', 'hakkında', 'hangi ai', 'sen ai', 'nedir']):
        return "sistem"
    
    # 3. TEKNİK SORULAR
    if any(k in q for k in ['vma', 'ema', 'pivot', 'teknik analiz', 'nasıl yorumlanır', 'ne demek', 'bollinger']):
        return "teknik"
    
    # 4. NASIL ÇALIŞIR
    if any(k in q for k in ['nasıl çalışır', 'nasıl analiz', 'yöntem', 'süreç']):
        return "nasil"
    
    # 5. GENEL BORSA
    if any(k in q for k in ['öne çıkan', 'en iyi', 'borsa durumu', 'genel durum', 'piyasa', 'hangi hisseler']):
        return "genel_borsa"
    
    # 6. ENDEKS SORULARI
    if any(k in q for k in ['xu100', 'xu030', 'xu30', 'endeks', 'bist', 'xteks', 'xulas']):
        return "endeks"
    
    # 7. EXCEL/MACRO SORULARI (YENİ)
    if any(k in q for k in ['excel', 'macro', 'makro', 'dosya', 'açılır', 'nasıl açılır']):
        return "excel_macro"
    
    # 8. HİSSE ANALİZİ (son çare)
    # Hisse kodunu kontrol et
    hisse_pattern = re.search(r'\b([A-Z]{2,6})\b', question.upper())
    if hisse_pattern:
        return "analiz"
    
    return "bilinmeyen"

# ==================== ÖZEL CEVAPLAR ====================
def get_teşekkür_cevabı():
    return """🌟 **Teşekkür ederim!**

Ben BorsaAnaliz AI asistanıyım. Size yardımcı olabildiğim için mutluyum! 

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Versiyon:** 4.5 (Final)
**Güncelleme:** Günlük Excel raporları

📊 **3 Sayfa Analiz:**
1. **Sinyaller:** 637+ hisse
2. **ENDEKSLER:** Tüm BIST endeksleri  
3. **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto

💡 **Örnek Sorular:**
• "GARAN analiz et"
• "ARCLK durumu"
• "HALKB hissesi"
• "XU030 endeksi"
• "VMA nasıl yorumlanır?"

Sormak istediğiniz başka bir şey var mı?"""

def get_teknik_cevabı(question):
    q = question.lower()
    
    if 'vma' in q:
        return """📊 **VMA Algoritması Nasıl Yorumlanır?**

**VMA (Volume Moving Average):** Hacim ağırlıklı algoritma.

**Değerler ve Anlamları:**
• **POZİTİF (00):** Trend başlangıcı (parantez içindeki rakam gün sayısıdır) ✓
• **POZİTİF (--):** Trendin devam ettiğini gösterir 
• **NEGATİF (00):** Trendin bitişi (parantez içindeki rakam gün sayısıdır) ✗
• **NEGATİF (--):** Düşüş trendinin devam ettiğini gösterir

**Örnek:** "POZİTİF (75)" = Trend 75 gündür pozitif yönde devam ediyor.

Teknik analizde VMA, hacim ağırlıklı trend algoritmasıdır."""

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

    else:
        return """📈 **Teknik Analiz Göstergeleri**

1. **VMA:** Hacim algoritması
2. **EMA:** Fiyat trendi  
3. **Pivot:** Destek/direnç
4. **Bollinger:** Volatilite

Hangi gösterge hakkında bilgi istiyorsunuz?"""

def get_nasil_cevabı():
    return """🔧 **Nasıl Çalışıyorum?**

1. **Veri Al:** Güncel Excel'i okurum (3 sayfa)
2. **Hisse Bul:** Sorudaki kodu ararım (637+ hisse)
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

**Önemli Endeksler:**
• **XU100:** Büyük şirketler
• **XU30:** En büyük 30 şirket
• **XTUSY:** Tüm hisseler

Detaylı hisse analizi için hisse adı yazın: "GARAN analiz et" """

def get_excel_macro_cevabı():
    return """📊 **Excel ve MACRO Hakkında**

**Excel Dosyası:**
• Format: .xlsm (macro içeren)
• Boyut: ~5-10 MB
• İçerik: 3 sayfa, 637+ hisse

**MACRO (Makro):**
Excel'de otomatik işlemler için kullanılır. Analiz sistemimizde:

1. **Excel'i Açmak İçin:**
   • Microsoft Excel 2010+
   • "Güvenlik Uyarısı" görürseniz → "Makroları Etkinleştir"
   • Veya: İndirdiğiniz dosya üzerinde sağ tık → Özellikler → Endellemeyi kaldır → Tamam

2. **Sistemimizde:**
   • Excel'den otomatik veri okuma
   • AI analizi için veri hazırlama
   • Günlük güncellemeler

**Hisse Analizi İçin:**
Sadece hisse adı yazın: "GARAN analiz et", "ARCLK durumu" """

def get_genel_borsa_cevabı():
    return """📊 **Borsa Genel Durumu**

**Analiz İçin:**
Lütfen hisse adı yazın:

**Popüler Hisseler:**
• GARAN - Garanti Bankası
• ARCLK - Arçelik
• HALKB - Halkbank
• THYAO - Türk Hava Yolları
• FROTO - Ford Otosan
• EREGL - Eregli Demir Çelik

**Örnek:** "GARAN analiz et", "ARCLK durumu"

Veya teknik sorular:
• "VMA nasıl yorumlanır?"
• "EMA nedir?"
• "XU100 endeksi" """

# ==================== EXCEL OKUMA ====================
def read_excel_direct():
    """Excel'i oku"""
    try:
        print("📖 Excel okunuyor...")
        
        from excel_processor import excel_processor
        result = excel_processor.read_excel_data()
        
        if not result.get("success", True):
            return {"error": "Excel okunamadı"}
        
        total_symbols = result.get('total_symbols', 0)
        print(f"✅ Excel okundu: {total_symbols} sembol")
        
        return result
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {e}")
        return {"error": str(e)}

# ==================== KESİN ARAMA ====================
def find_symbol_simple(question, excel_data):
    """BASİT ve ETKİLİ arama"""
    try:
        q_upper = question.upper().strip()
        print(f"🔍 ARAMA: '{q_upper}'")
        
        # Hisse kodunu çıkar
        hisse_match = re.search(r'\b([A-Z]{2,6})\b', q_upper)
        if not hisse_match:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        hisse_kodu = hisse_match.group(1)
        print(f"📝 Aranan hisse: '{hisse_kodu}'")
        
        # Sinyaller sayfasında ara
        if "Sinyaller" in excel_data.get("sheets", {}):
            hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
            
            # 1. Doğrudan arama
            if hisse_kodu in hisseler:
                print(f"✅ Doğrudan bulundu: '{hisse_kodu}'")
                return {
                    "found": True,
                    "type": "hisse",
                    "name": hisse_kodu,
                    "data": hisseler[hisse_kodu],
                    "sayfa": "Sinyaller"
                }
            
            # 2. Tüm hisselerde ara
            for hisse_adi, veriler in hisseler.items():
                hisse_clean = re.sub(r'[^A-Z]', '', hisse_adi.upper())
                
                if hisse_kodu == hisse_clean:
                    print(f"✅ Temizlenmiş bulundu: '{hisse_kodu}' -> '{hisse_adi}'")
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
            
            # 3. Substring arama
            for hisse_adi, veriler in hisseler.items():
                if hisse_kodu in hisse_adi.upper():
                    print(f"✅ Substring bulundu: '{hisse_kodu}' -> '{hisse_adi}'")
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
        
        print(f"❌ Bulunamadı: '{hisse_kodu}'")
        return {"found": False, "error": f"'{hisse_kodu}' bulunamadı"}
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {"found": False, "error": str(e)}

# ==================== AI ANALİZİ ====================
def get_ai_analysis(prompt):
    """AI'dan analiz al"""
    try:
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        
        if not api_key:
            return "⚠️ AI analiz için API anahtarı gerekli."
        
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
        return f"❌ AI analiz hatası"

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
            "ai": "BorsaAnaliz AI 4.5",
            "version": "Final Fix - Tüm Hisse Çalışır",
            "endpoint": "/api/ask-direct",
            "method": "POST {'question': 'sorunuz'}",
            "examples": [
                "GARAN analiz et",
                "ARCLK durumu", 
                "HALKB hissesi",
                "XU030 endeksi",
                "VMA nedir?",
                "Excel macro nasıl açılır?"
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
            print(f"🔍 Soru tipi: {question_type}")
            
            # 3. ÖZEL SORULAR İÇİN DİREKT CEVAP
            special_answers = {
                "teşekkür": get_teşekkür_cevabı,
                "sistem": get_sistem_cevabı,
                "teknik": lambda: get_teknik_cevabı(question),
                "nasil": get_nasil_cevabı,
                "endeks": lambda: get_endeks_cevabı(),
                "excel_macro": get_excel_macro_cevabı,
                "genel_borsa": get_genel_borsa_cevabı
            }
            
            if question_type in special_answers:
                print(f"✅ Özel cevap: {question_type}")
                answer = special_answers[question_type]()
                
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
            
            # 4. HİSSE ANALİZİ İÇİN
            if question_type == "analiz":
                print("🔍 Hisse analizi başlatılıyor...")
                
                # Excel'i oku
                excel_result = read_excel_direct()
                
                if "error" in excel_result:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    
                    answer = "❌ Excel okunamadı. Lütfen daha sonra tekrar deneyin."
                    
                    result = json.dumps({
                        "success": False,
                        "answer": answer,
                        "question_type": "error"
                    }, ensure_ascii=False)
                    
                    self.wfile.write(result.encode())
                    return
                
                # Hisseyi ara
                search_result = find_symbol_simple(question, excel_result)
                
                if not search_result.get("found"):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    # Hisse kodunu çıkar
                    hisse_match = re.search(r'\b([A-Z]{2,6})\b', question.upper())
                    hisse_kodu = hisse_match.group(1) if hisse_match else "HİSSE"
                    
                    answer = f"❌ **{hisse_kodu} bulunamadı.**\n\n"
                    answer += "**Örnek Hisseler:**\n"
                    answer += "• GARAN, ARCLK, HALKB, THYAO\n"
                    answer += "• FROTO, EREGL, SASA, TUPRS\n"
                    answer += "• KCHOL, ASELS, BIMAS, A1CAP\n\n"
                    answer += "**Veya şunu sorun:**\n"
                    answer += "• \"VMA nedir?\"\n• \"XU030 endeksi\"\n• \"Excel macro\""
                    
                    result = json.dumps({
                        "success": False,
                        "answer": answer,
                        "question_type": "not_found",
                        "symbol": hisse_kodu
                    }, ensure_ascii=False)
                    
                    self.wfile.write(result.encode())
                    print(f"📤 Hisse bulunamadı: {hisse_kodu}")
                    return
                
                # AI analizi yap
                sembol_adi = search_result["name"]
                sembol_data = search_result["data"]
                excel_date = excel_result.get("excel_date", "güncel")
                
                print(f"✅ {sembol_adi} bulundu, AI analizi yapılıyor...")
                
                # Prompt oluştur
                prompt = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Excel Tarihi:** {excel_date}
**Kaynak:** Sinyaller sayfası

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
5. 250-300 kelime, net olsun

**Analiz:**"""
                
                # AI'dan analiz al
                ai_answer = get_ai_analysis(prompt)
                
                # Cevapla
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": ai_answer,
                    "symbol": sembol_adi,
                    "excel_date": excel_date,
                    "question_type": "analiz",
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode())
                print(f"📤 Analiz gönderildi: {sembol_adi}")
                print('='*60 + '\n')
                return
            
            # 5. BİLİNMEYEN SORU TİPİ
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            answer = """🤔 **Anlamadım**

Lütfen şunlardan birini sorun:

**Hisse Analizi:**
• "GARAN analiz et"
• "ARCLK durumu"
• "HALKB hissesi"

**Teknik Sorular:**
• "VMA nasıl yorumlanır?"
• "EMA nedir?"

**Diğer:**
• "XU030 endeksi"
• "Excel macro nasıl açılır?"
• "Sistem hakkında" """
            
            result = json.dumps({
                "success": False,
                "answer": answer,
                "question_type": "bilinmeyen"
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode())
            print(f"📤 Bilinmeyen soru tipi")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
            traceback.print_exc()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            answer = f"❌ **Sistem hatası:** {str(e)[:100]}\n\n"
            answer += "Lütfen basit bir soru sorun: \"GARAN analiz et\""
            
            result = json.dumps({
                "success": False,
                "answer": answer,
                "error": str(e)[:200]
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode())

# ==================== LOCAL TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 BorsaAnaliz AI 4.5: http://localhost:{port}/api/ask-direct")
    print("📊 TÜM hisseler çalışır: GARAN, ARCLK, HALKB dahil")
    server.serve_forever()
