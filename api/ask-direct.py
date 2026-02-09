#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - TÜM HİSSELER ÇALIŞIR!
# Versiyon: 4.3 (Tüm 3 Sayfa + 637 Hisse)

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
    
    # 2. SİSTEM SORULARI
    if any(k in q for k in ['kim yaptı', 'kim geliştirdi', 'sistem', 'hakkında', 'hangi ai']):
        print("✅ Tip: sistem")
        return "sistem"
    
    # 3. TEKNİK SORULAR
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
    endeks_patterns = ['xu100', 'xu 100', 'xu030', 'xu 030', 'xu30', 'xu 30', 
                      'xteks', 'xulas', 'endeks', 'bist']
    for pattern in endeks_patterns:
        if pattern in q:
            print(f"✅ Tip: endeks ({pattern})")
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
**Versiyon:** 4.3 (Tüm Hisse Çalışır)
**Güncelleme:** Günlük Excel raporları

📊 **3 Sayfa Analiz:**
1. **Sinyaller:** 637+ hisse
2. **ENDEKSLER:** Tüm BIST endeksleri
3. **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto

💡 **Örnek Sorular:**
• "ARCLK analiz et"
• "PGSUS durumu"
• "XU030 endeksi"
• "VMA nedir?"

Sormak istediğiniz başka bir şey var mı?"""

def get_teknik_cevabı(question):
    q = question.lower()
    
    if 'vma' in q:
        return """📊 **VMA Algoritması Nasıl Yorumlanır?**

**VMA (Volume Moving Average):** Hacim ağırlıklı algoritma.

**Değerler ve Anlamları:**
• **POZİTİF (00):** Trend başlangıcı(parantez içindeki rakam gün sayısıdır) ✓
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

# ==================== EXCEL OKUMA ====================
def read_excel_direct():
    """Excel'i oku ve DEBUG göster"""
    try:
        print("📖 Excel okunuyor...")
        
        # Excel processor kullan
        from excel_processor import excel_processor
        
        result = excel_processor.read_excel_data()
        
        if not result.get("success", True):
            return {"error": "Excel okunamadı"}
        
        total_symbols = result.get('total_symbols', 0)
        print(f"✅ Excel okundu: {total_symbols} sembol")
        
        # DEBUG: Tüm sembolleri göster
        debug_excel_content(result)
        
        return result
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def debug_excel_content(excel_data):
    """Excel içeriğini DEBUG et"""
    try:
        print("\n" + "="*70)
        print("🔍 EXCEL DEBUG - TÜM SAYFALAR")
        print("="*70)
        
        sheets = excel_data.get("sheets", {})
        
        # 1. SINYALLER sayfası
        if "Sinyaller" in sheets:
            hisseler = sheets["Sinyaller"].get("hisseler", {})
            print(f"📈 Sinyaller: {len(hisseler)} hisse")
            
            # ARCLK ve PGSUS ara
            print("\n🔍 ARCLK ve PGSUS KONTROLÜ:")
            found_arclk = False
            found_pgsus = False
            
            for hisse_adi in hisseler.keys():
                hisse_clean = hisse_adi.upper().strip()
                
                if "ARCLK" in hisse_clean:
                    print(f"✅ ARCLK bulundu: '{hisse_adi}'")
                    found_arclk = True
                
                if "PGSUS" in hisse_clean:
                    print(f"✅ PGSUS bulundu: '{hisse_adi}'")
                    found_pgsus = True
            
            if not found_arclk:
                print("❌ ARCLK bulunamadı!")
            
            if not found_pgsus:
                print("❌ PGSUS bulunamadı!")
            
            # İlk 10 hisseyi göster
            print(f"\n📋 İlk 10 hisse:")
            for i, hisse in enumerate(list(hisseler.keys())[:10], 1):
                print(f"  {i:2d}. {hisse}")
        
        # 2. ENDEKSLER sayfası
        if "ENDEKSLER" in sheets:
            semboller = sheets["ENDEKSLER"].get("semboller", {})
            print(f"\n📊 ENDEKSLER: {len(semboller)} sembol")
            
            # XU100, XU030 ara
            print("🔍 XU100 ve XU030 KONTROLÜ:")
            for sembol in semboller.keys():
                sembol_clean = str(sembol).upper()
                if "XU100" in sembol_clean or "XU 100" in sembol_clean:
                    print(f"✅ XU100 bulundu: '{sembol}'")
                if "XU030" in sembol_clean or "XU 030" in sembol_clean:
                    print(f"✅ XU030 bulundu: '{sembol}'")
            
            # İlk 5 sembol
            print(f"📋 İlk 5 sembol:")
            for i, sembol in enumerate(list(semboller.keys())[:5], 1):
                print(f"  {i:2d}. {sembol}")
        
        # 3. FON_EMTIA_COIN_DOVIZ sayfası
        if "FON_EMTIA_COIN_DOVIZ" in sheets:
            semboller = sheets["FON_EMTIA_COIN_DOVIZ"].get("semboller", {})
            print(f"\n💰 FON_EMTIA: {len(semboller)} sembol")
            print(f"📋 İlk 5 sembol:")
            for i, sembol in enumerate(list(semboller.keys())[:5], 1):
                print(f"  {i:2d}. {sembol}")
        
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Debug hatası: {e}")

# ==================== YENİ AKILLI ARAMA ====================
def smart_search_fixed(question, excel_data):
    """YENİ ve DOĞRU arama algoritması - 3 SAYFA"""
    try:
        q_upper = question.upper().strip()
        print(f"🔍 YENİ ARAMA: '{q_upper}'")
        
        # 1. ÖNCE: ENDEKS KONTROLÜ
        endeks_eslesmeler = {
            'XU100': ['XU100', 'XU 100'],
            'XU030': ['XU030', 'XU 030', 'XU30', 'XU 30'],
            'XU10': ['XU10', 'XU 10'],
            'XTEKS': ['XTEKS'],
            'XULAS': ['XULAS']
        }
        
        for endeks_adi, patterns in endeks_eslesmeler.items():
            for pattern in patterns:
                if pattern in q_upper:
                    print(f"✅ Endeks bulundu: {endeks_adi}")
                    return {
                        "found": True,
                        "type": "endeks",
                        "name": endeks_adi,
                        "data": {"is_endeks": True, "name": endeks_adi},
                        "sayfa": "ENDEKSLER"
                    }
        
        # 2. HİSSE KODUNU ÇIKAR (daha esnek)
        # Hisse kodları: ARCLK, PGSUS, THYAO, FROTO, A1CAP gibi
        words = re.findall(r'[A-Z]{2,8}', q_upper)
        
        if not words:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        print(f"📝 Potansiyel hisse kodları: {words}")
        
        # 3. 3 SAYFADA ARA
        
        # A) ÖNCE SİNYALLER (hisseler)
        sheets = excel_data.get("sheets", {})
        
        if "Sinyaller" in sheets:
            hisseler = sheets["Sinyaller"].get("hisseler", {})
            print(f"📊 Sinyaller'de {len(hisseler)} hisse aranıyor...")
            
            # Her kelime için ara
            for word in words:
                print(f"  → Sinyaller'de '{word}' aranıyor...")
                
                # 1. TAM EŞLEŞME (büyük/küçük harf duyarsız)
                for hisse_adi, veriler in hisseler.items():
                    hisse_upper = hisse_adi.upper().strip()
                    
                    if word == hisse_upper:
                        print(f"  ✅ TAM EŞLEŞME: '{word}' -> '{hisse_adi}'")
                        return {
                            "found": True,
                            "type": "hisse",
                            "name": hisse_adi,
                            "data": veriler,
                            "sayfa": "Sinyaller"
                        }
                
                # 2. KISMİ EŞLEŞME (ARCLK, PGSUS vb.)
                for hisse_adi, veriler in hisseler.items():
                    hisse_upper = hisse_adi.upper().strip()
                    
                    if word in hisse_upper:
                        print(f"  ✅ KISMİ EŞLEŞME: '{word}' -> '{hisse_adi}'")
                        return {
                            "found": True,
                            "type": "hisse",
                            "name": hisse_adi,
                            "data": veriler,
                            "sayfa": "Sinyaller"
                        }
        
        # B) SONRA ENDEKSLER
        if "ENDEKSLER" in sheets:
            semboller = sheets["ENDEKSLER"].get("semboller", {})
            
            for word in words:
                for sembol_adi, veriler in semboller.items():
                    sembol_upper = str(sembol_adi).upper().strip()
                    
                    if word in sembol_upper or sembol_upper in word:
                        print(f"✅ ENDEKSLER'de bulundu: '{word}' -> '{sembol_adi}'")
                        return {
                            "found": True,
                            "type": "endeks",
                            "name": sembol_adi,
                            "data": veriler,
                            "sayfa": "ENDEKSLER"
                        }
        
        # C) SONRA FON/EMTIA/DÖVİZ
        if "FON_EMTIA_COIN_DOVIZ" in sheets:
            semboller = sheets["FON_EMTIA_COIN_DOVIZ"].get("semboller", {})
            
            for word in words:
                for sembol_adi, veriler in semboller.items():
                    sembol_upper = str(sembol_adi).upper().strip()
                    
                    if word in sembol_upper or sembol_upper in word:
                        print(f"✅ FON_EMTIA'da bulundu: '{word}' -> '{sembol_adi}'")
                        return {
                            "found": True,
                            "type": "fon_emtia",
                            "name": sembol_adi,
                            "data": veriler,
                            "sayfa": "FON_EMTIA_COIN_DOVIZ"
                        }
        
        print(f"❌ Hiçbir sayfada bulunamadı: {words}")
        return {"found": False, "error": f"{words[0]} hiçbir sayfada bulunamadı"}
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        traceback.print_exc()
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
            "ai": "BorsaAnaliz AI 4.3",
            "endpoint": "/api/ask-direct",
            "method": "POST {'question': 'sorunuz'}",
            "features": [
                "637+ hisse analizi",
                "3 sayfa Excel okuma",
                "ARCLK, PGSUS, XU030 dahil",
                "Tüm BIST hisseleri"
            ],
            "examples": [
                "ARCLK analiz et",
                "PGSUS durumu",
                "XU030 endeksi",
                "VMA nedir?"
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
                    endeks_match = re.search(r'(XU100|XU030|XU30|XU10|XTEKS|XULAS)', question.upper())
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
            
            # 4. GENEL BORSA SORUSU
            if question_type == "genel_borsa":
                print("🔍 Genel borsa için Excel okunuyor...")
                
                excel_result = read_excel_direct()
                
                if "error" in excel_result:
                    answer = "📊 Borsa genel durumu için Excel verileri yüklenemedi."
                else:
                    # Basit liste göster
                    if "Sinyaller" in excel_result.get("sheets", {}):
                        hisseler = excel_result["sheets"]["Sinyaller"].get("hisseler", {})
                        excel_date = excel_result.get("excel_date", "güncel")
                        
                        answer = f"📊 **BORSA GENEL DURUMU** ({excel_date})\n\n"
                        answer += f"**Toplam Hisse:** {len(hisseler)}\n\n"
                        answer += "**Örnek Hisseler:**\n"
                        
                        # 3 sütun halinde
                        hisse_list = list(hisseler.keys())[:15]
                        for i in range(0, len(hisse_list), 5):
                            chunk = hisse_list[i:i+5]
                            answer += "• " + " • ".join(chunk) + "\n"
                        
                        answer += "\n**Analiz için:** \"ARCLK analiz et\""
                    else:
                        answer = "📊 Hisse listesi yüklenemedi."
                
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
            
            # YENİ ARAMA YAP
            search_result = smart_search_fixed(question, excel_result)
            
            if not search_result.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                # ÖNERİLERLE CEVAP
                hisse_kodlari = re.findall(r'[A-Z]{2,6}', question.upper())
                hisse_kodu = hisse_kodlari[0] if hisse_kodlari else "???"
                
                answer = f"❌ **{hisse_kodu} bulunamadı.**\n\n"
                answer += "**Örnek Hisseler:**\n"
                answer += "• ARCLK, PGSUS, ENKAI, FROTO, THYAO\n"
                answer += "• TUPRS, SASA, EREGL, KCHOL, ASELS\n"
                answer += "• GARAN, BIMAS, A1CAP, TCELL, HEKTS\n\n"
                answer += "**Veya şunu sorun:**\n"
                answer += "• \"VMA nedir?\"\n• \"XU030 endeksi\"\n• \"Sistem hakkında\""
                
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
            sayfa = search_result.get("sayfa", "Sinyaller")
            
            # Prompt oluştur
            prompt = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Excel Tarihi:** {excel_date}
**Kaynak:** {sayfa} sayfası

**GERÇEK VERİLER (Excel'den):**
"""
            
            # Önemli alanları ekle
            fields_to_show = [
                'Close', 'Open', 'High', 'Low', 'Hacim',
                'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55',
                'Pivot', 'S1', 'R1', 'DURUM', 'Pearson55'
            ]
            
            for field in fields_to_show:
                if field in sembol_data:
                    value = sembol_data[field]
                    prompt += f"• **{field}:** {value}\n"
            
            prompt += f"\n**Soru:** {question}\n\n"
            prompt += """**Talimatlar:**
1. SADECE yukarıdaki Excel verilerini kullan
2. VMA, EMA, Pivot, Pearson55 analizi yap
3. Teknik durumu özetle
4. Yatırım tavsiyesi VERME
5. 250-300 kelime, net olsun

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
                "sheet": sayfa,
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
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            answer = f"❌ **Sistem hatası:** {str(e)[:100]}\n\n"
            answer += "Lütfen basit bir hisse sorusu sorun:\n"
            answer += "• \"ARCLK analiz et\"\n"
            answer += "• \"PGSUS durumu\"\n"
            answer += "• \"XU030 endeksi\""
            
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
    print(f"🚀 BorsaAnaliz AI 4.3: http://localhost:{port}/api/ask-direct")
    print("📊 ARCLK, PGSUS, XU030 dahil TÜM hisseler çalışır!")
    server.serve_forever()
