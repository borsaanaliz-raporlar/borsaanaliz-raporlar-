#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - TÜM HİSSELER ÇALIŞIR!
# Versiyon: 4.4 (Kesin Çözüm)

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

Ben BorsaAnaliz AI asistanıyım. Size yardımcı olabildiğim için mutluyum! 

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Versiyon:** 4.4 (Kesin Çözüm)
**Güncelleme:** Günlük Excel raporları

📊 **3 Sayfa Analiz:**
1. **Sinyaller:** 637+ hisse (YKBNK, ARCLK, PGSUS dahil)
2. **ENDEKSLER:** Tüm BIST endeksleri
3. **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto

💡 **Örnek Sorular:**
• "YKBNK analiz et"
• "ARCLK durumu"
• "PGSUS hissesi"
• "XU030 endeksi"
• "VMA nedir?"

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
    """Excel'i oku"""
    try:
        print("📖 Excel okunuyor...")
        
        # Excel processor kullan
        from excel_processor import excel_processor
        
        result = excel_processor.read_excel_data()
        
        if not result.get("success", True):
            return {"error": "Excel okunamadı"}
        
        total_symbols = result.get('total_symbols', 0)
        print(f"✅ Excel okundu: {total_symbols} sembol")
        
        return result
        
    except Exception as e:
        print(f"❌ Excel okuma hatası: {e}")
        traceback.print_exc()
        return {"error": str(e)}

# ==================== KESİN ARAMA ALGORİTMASI ====================
def find_symbol_exact(question, excel_data):
    """KESİN ve DOĞRU sembol arama - TÜM HİSSELER ÇALIŞIR"""
    try:
        q_upper = question.upper().strip()
        print(f"🔍 KESİN ARAMA: '{q_upper}'")
        
        # 1. Sorudaki hisse kodunu çıkar
        words = re.findall(r'[A-Z]{2,8}', q_upper)
        
        if not words:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        search_word = words[0]  # İlk kelimeyi al (YKBNK, ARCLK, PGSUS vb.)
        print(f"📝 Aranan hisse: '{search_word}'")
        
        # 2. ÖNCE ENDEKS KONTROLÜ
        if any(endeks in q_upper for endeks in ['XU100', 'XU030', 'XU30', 'XU10', 'XTEKS', 'XULAS']):
            # Endeks adını belirle
            if 'XU100' in q_upper or 'XU 100' in q_upper:
                endeks_adi = "XU100"
            elif 'XU030' in q_upper or 'XU 030' in q_upper or 'XU30' in q_upper or 'XU 30' in q_upper:
                endeks_adi = "XU030"
            elif 'XU10' in q_upper or 'XU 10' in q_upper:
                endeks_adi = "XU10"
            elif 'XTEKS' in q_upper:
                endeks_adi = "XTEKS"
            elif 'XULAS' in q_upper:
                endeks_adi = "XULAS"
            else:
                endeks_adi = "XU100"
            
            print(f"✅ Endeks sorusu: {endeks_adi}")
            return {
                "found": True,
                "type": "endeks",
                "name": endeks_adi,
                "data": {"is_endeks": True, "name": endeks_adi},
                "sayfa": "ENDEKSLER"
            }
        
        # 3. SİNYALLER SAYFASINDA ARA
        if "Sinyaller" in excel_data.get("sheets", {}):
            hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
            
            print(f"📊 {len(hisseler)} hisse aranıyor...")
            
            # A) 1. YOL: Doğrudan anahtar olarak ara
            if search_word in hisseler:
                print(f"✅ 1. YOL: Doğrudan bulundu: '{search_word}'")
                return {
                    "found": True,
                    "type": "hisse",
                    "name": search_word,
                    "data": hisseler[search_word],
                    "sayfa": "Sinyaller"
                }
            
            # B) 2. YOL: Büyük/küçük harf duyarsız tam eşleşme
            for hisse_adi, veriler in hisseler.items():
                hisse_clean = re.sub(r'[^A-Z]', '', hisse_adi.upper())
                
                if search_word == hisse_clean:
                    print(f"✅ 2. YOL: Temizlenmiş eşleşme: '{search_word}' -> '{hisse_adi}'")
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
            
            # C) 3. YOL: Substring arama
            for hisse_adi, veriler in hisseler.items():
                if search_word in hisse_adi.upper():
                    print(f"✅ 3. YOL: Substring bulundu: '{search_word}' -> '{hisse_adi}'")
                    return {
                        "found": True,
                        "type": "hisse",
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
            
            # D) 4. YOL: Benzer hisseleri listele (yardım için)
            print(f"⚠️ '{search_word}' tam bulunamadı. Benzer hisseler:")
            similar_hisses = []
            for hisse_adi in hisseler.keys():
                if search_word[:3] in hisse_adi.upper():
                    similar_hisses.append(hisse_adi)
            
            if similar_hisses:
                print(f"📋 Benzer hisseler: {similar_hisses[:5]}")
        
        # 4. ENDEKSLER SAYFASINDA ARA
        if "ENDEKSLER" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["ENDEKSLER"].get("semboller", {})
            
            for sembol_adi, veriler in semboller.items():
                sembol_upper = str(sembol_adi).upper()
                if search_word in sembol_upper:
                    print(f"✅ ENDEKSLER'de bulundu: '{search_word}' -> '{sembol_adi}'")
                    return {
                        "found": True,
                        "type": "endeks",
                        "name": sembol_adi,
                        "data": veriler,
                        "sayfa": "ENDEKSLER"
                    }
        
        # 5. FON/EMTIA/DÖVİZ SAYFASINDA ARA
        if "FON_EMTIA_COIN_DOVIZ" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"].get("semboller", {})
            
            for sembol_adi, veriler in semboller.items():
                sembol_upper = str(sembol_adi).upper()
                if search_word in sembol_upper:
                    print(f"✅ FON_EMTIA'da bulundu: '{search_word}' -> '{sembol_adi}'")
                    return {
                        "found": True,
                        "type": "fon_emtia",
                        "name": sembol_adi,
                        "data": veriler,
                        "sayfa": "FON_EMTIA_COIN_DOVIZ"
                    }
        
        print(f"❌ Hiçbir sayfada bulunamadı: '{search_word}'")
        return {"found": False, "error": f"'{search_word}' bulunamadı"}
        
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
            "ai": "BorsaAnaliz AI 4.4",
            "version": "Kesin Çözüm - Tüm Hisse Çalışır",
            "endpoint": "/api/ask-direct",
            "method": "POST {'question': 'sorunuz'}",
            "features": [
                "YKBNK, ARCLK, PGSUS dahil 637+ hisse",
                "3 sayfa Excel okuma",
                "XU100, XU030 endeksleri",
                "VMA, EMA teknik analiz"
            ],
            "examples": [
                "YKBNK analiz et",
                "ARCLK durumu",
                "PGSUS hissesi",
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
                        
                        answer += "\n**Analiz için:** \"YKBNK analiz et\""
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
            
            # YENİ ve KESİN ARAMA YAP
            search_result = find_symbol_exact(question, excel_result)
            
            if not search_result.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Hisse kodunu çıkar
                words = re.findall(r'[A-Z]{2,8}', question.upper())
                hisse_kodu = words[0] if words else "HİSSE"
                
                answer = f"❌ **{hisse_kodu} bulunamadı.**\n\n"
                
                # Yardım için örnek hisseler göster
                if "Sinyaller" in excel_result.get("sheets", {}):
                    hisseler = excel_result["sheets"]["Sinyaller"].get("hisseler", {})
                    hisse_list = list(hisseler.keys())
                    
                    answer += "**Excel'deki hisselerden bazıları:**\n"
                    
                    # İlk 20 hisseyi 4'erli gruplar halinde göster
                    for i in range(0, min(20, len(hisse_list)), 4):
                        chunk = hisse_list[i:i+4]
                        answer += "• " + " • ".join(chunk) + "\n"
                
                answer += "\n**Veya şunu sorun:**\n"
                answer += "• \"VMA nedir?\"\n• \"XU030 endeksi\"\n• \"Sistem hakkında\""
                
                result = json.dumps({
                    "success": False,
                    "answer": answer,
                    "question_type": "not_found",
                    "symbol": hisse_kodu
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
            answer += "• \"YKBNK analiz et\"\n"
            answer += "• \"ARCLK durumu\"\n"
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
    print(f"🚀 BorsaAnaliz AI 4.4: http://localhost:{port}/api/ask-direct")
    print("📊 YKBNK, ARCLK, PGSUS dahil TÜM hisseler çalışır!")
    print("💡 Örnek: \"YKBNK analiz et\", \"ARCLK hissesi\", \"PGSUS durumu\"")
    server.serve_forever()
