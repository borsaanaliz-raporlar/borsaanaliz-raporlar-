#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - API KEY GEREKMEZ
# Versiyon: 6.1 (No API Key)

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import re
import traceback
from datetime import datetime
import random

# ==================== ÖNCE SORU ANALİZİ ====================
def analyze_question_type(question):
    """Soruyu BASİT analiz et"""
    q = question.lower().strip()
    
    print(f"🔍 Soru: '{q}'", file=sys.stderr)
    
    # Özel sorular (HIZLI MOD - API key gerekmez)
    if any(k in q for k in ['teşekkür', 'sağ ol', 'sağol', 'mükemmel', 'harika']):
        return "teşekkür"
    
    if any(k in q for k in ['vma', 'ema', 'teknik analiz', 'nasıl yorumlanır', 'ne demek']):
        return "teknik"
    
    if any(k in q for k in ['excel', 'macro', 'makro', 'dosya', 'açılır']):
        return "excel_macro"
    
    if any(k in q for k in ['kim yaptı', 'sistem', 'hakkında', 'sen ai', 'kimsin']):
        return "sistem"
    
    if any(k in q for k in ['öne çıkan', 'en iyi', 'borsa durumu', 'popüler', 'hangi hisseler']):
        return "genel_borsa"
    
    if any(k in q for k in ['nasıl çalışır', 'yöntem', 'süreç']):
        return "nasil"
    
    if any(k in q for k in ['endeks', 'xu100', 'xu030', 'xulas', 'xteks']):
        return "endeks"
    
    # Hisse/endeks kodu varsa analiz
    if re.search(r'\b([A-Z]{2,6})\b', question.upper()):
        return "analiz"
    
    return "bilinmeyen"

# ==================== ÖZEL CEVAPLAR (HIZLI MOD) ====================
def get_teşekkür_cevabı():
    return "🌟 **Teşekkür ederim!**\n\nBaşka hisse analizi istiyor musunuz?"

def get_teknik_cevabı(question):
    q = question.lower()
    
    if 'vma' in q:
        return """📊 **VMA (Volume Moving Average) - Hacim Algoritması**

**Değerler ve Anlamları:**
• **POZİTİF (00):** Trend başlangıcı (parantez içindeki rakam gün sayısıdır)
• **POZİTİF (--):** Trendin devam ettiğini gösterir
• **NEGATİF (00):** Trendin bitişi
• **NEGATİF (--):** Düşüş trendinin devam ettiğini gösterir

**Örnek:** "POZİTİF (75)" = Trend 75 gündür pozitif yönde devam ediyor."""
    
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

Detaylı bilgi için: "VMA nasıl yorumlanır?" veya "EMA nedir?" """

def get_excel_macro_cevabı():
    return """📊 **Excel ve MACRO Hakkında**

**Excel Dosyası:**
• Format: .xlsm (macro içeren)
• İçerik: 3 sayfa, 600+ hisse, endeksler, GMSTR/ALTIN

**MACRO Açmak İçin:**
1. Microsoft Excel 2010+
2. "Güvenlik Uyarısı" görürseniz → "Makroları Etkinleştir"
3. Veya: Dosya → Seçenekler → Güven Merkezi → Makro Ayarları

**Hisse Analizi İçin:** "GMSTR analiz et", "XU100 durumu" """

def get_sistem_cevabı():
    return """🤖 **BorsaAnaliz AI Sistemi**

**Versiyon:** 6.1 (No API Key)
**Özellik:** Hızlı Mod - Özel cevaplar anında

📊 **3 Sayfa Analiz:**
1. **Sinyaller:** 600+ hisse (ENKAI, TUPRS, LOGO)
2. **ENDEKSLER:** XU100, XULAS, XTEKS
3. **FON_EMTIA_COIN_DOVIZ:** GMSTR, ALTIN, döviz, emtia

💡 **Örnek Sorular:**
• "GMSTR analiz et" (FON sayfasında)
• "XU100 analiz et" (ENDEKSLER sayfasında)
• "ENKAI analiz et" (Sinyaller sayfasında)
• "VMA nasıl yorumlanır?"
• "Excel macro nasıl açılır?" """

def get_nasil_cevabı():
    return """🔧 **Nasıl Çalışıyorum?**

1. **Veri Al:** Güncel Excel'i okurum (3 sayfa)
2. **Sembol Bul:** Sorudaki kodu 3 sayfada da ararım
3. **Analiz:** Excel'deki verileri gösteririm
4. **Özel Sorular:** Hızlı modda anında cevap

**Örnek Akış:**
"GMSTR analiz et" → FON sayfasında bul → Verileri göster

**Hızlı Mod:** VMA, Excel, Sistem soruları anında cevaplanır."""

def get_endeks_cevabı():
    return """📈 **BIST Endeksleri**

**Ana Endeksler:**
• **XU100:** BIST 100 - 100 büyük şirket
• **XU30:** BIST 30 - En büyük 30 şirket
• **XULAS:** Tüm şirketler
• **XTEKS:** Teknoloji endeksi
• **XUHIZ:** Hizmet endeksi

**Analiz için:** "XU100 analiz et", "XULAS durumu" """

# ==================== AKILLI ÖNE ÇIKAN HİSSELER ====================
def get_genel_borsa_cevabı():
    """Excel'den canlı hisse listesi - API key gerekmez"""
    try:
        # Excel'i oku
        excel_result = read_excel_direct()
        
        if "error" not in excel_result and "Sinyaller" in excel_result.get("sheets", {}):
            hisseler = list(excel_result["sheets"]["Sinyaller"]["hisseler"].keys())
            
            if hisseler:
                # Rastgele 6 hisse seç
                if len(hisseler) > 6:
                    random_hisseler = random.sample(hisseler, 6)
                else:
                    random_hisseler = hisseler[:6]
                
                answer = "📈 **Bugün Öne Çıkan Hisseler (Rastgele Seçim):**\n\n"
                for hisse in random_hisseler:
                    answer += f"• {hisse}\n"
                
                answer += f"\n**Toplam:** {len(hisseler)} hisse analiz ediliyor.\n"
                answer += "**Detay için:** \"[HİSSE ADI] analiz et\"\n\n"
                answer += "**Örnek:** \"ENKAI analiz et\", \"GMSTR durumu\""
                return answer
    except:
        pass
    
    # Fallback (API key gerekmez)
    return """📊 **Borsa Genel Durumu**

**3 Sayfadan Örnekler:**
• **FON Sayfası:** GMSTR, ALTIN
• **ENDEKSLER:** XU100, XULAS, XTEKS
• **SİNYALLER:** ENKAI, TUPRS, LOGO, GARAN, AKBNK

**Analiz İçin:**
"GMSTR analiz et", "XU100 durumu", "ENKAI hissesi"

**Toplam:** 600+ hisse, endeks ve sembol analiz ediliyor."""

# ==================== EXCEL OKUMA ====================
def read_excel_direct():
    """Excel'i oku - API key gerekmez"""
    try:
        print("📖 Excel okunuyor...", file=sys.stderr)
        
        from excel_processor import excel_processor
        result = excel_processor.read_excel_data()
        
        if not result.get("success", True):
            return {"error": "Excel okunamadı"}
        
        print(f"✅ Excel okundu: {result.get('total_symbols', 0)} sembol", file=sys.stderr)
        return result
        
    except Exception as e:
        print(f"❌ Excel hatası: {e}", file=sys.stderr)
        return {"error": str(e)}

# ==================== BASİT ARAMA ====================
def find_symbol_simple(question, excel_data):
    """BASİT ARAMA - 3 sayfanın TÜMÜNÜ kontrol et"""
    try:
        # Hisse kodunu çıkar
        match = re.search(r'\b([A-Z]{2,6})\b', question.upper())
        if not match:
            return {"found": False, "error": "Kod bulunamadı"}
        
        target = match.group(1)
        print(f"🔍 Aranan: '{target}'", file=sys.stderr)
        
        # 1. ÖNCE SİNYALLER SAYFASI
        if "Sinyaller" in excel_data.get("sheets", {}):
            hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
            for hisse_adi, veriler in hisseler.items():
                if target in hisse_adi.upper():
                    print(f"✅ Sinyaller: '{hisse_adi}'", file=sys.stderr)
                    return {
                        "found": True,
                        "name": hisse_adi,
                        "data": veriler,
                        "sayfa": "Sinyaller"
                    }
        
        # 2. SONRA ENDEKSLER SAYFASI
        if "ENDEKSLER" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["ENDEKSLER"].get("semboller", {})
            for sembol_adi, veriler in semboller.items():
                if target in sembol_adi.upper():
                    print(f"✅ ENDEKSLER: '{sembol_adi}'", file=sys.stderr)
                    return {
                        "found": True,
                        "name": sembol_adi,
                        "data": veriler,
                        "sayfa": "ENDEKSLER"
                    }
        
        # 3. SONRA FON_EMTIA_COIN_DOVIZ SAYFASI
        if "FON_EMTIA_COIN_DOVIZ" in excel_data.get("sheets", {}):
            semboller = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"].get("semboller", {})
            for sembol_adi, veriler in semboller.items():
                if target in sembol_adi.upper():
                    print(f"✅ FON: '{sembol_adi}'", file=sys.stderr)
                    return {
                        "found": True,
                        "name": sembol_adi,
                        "data": veriler,
                        "sayfa": "FON_EMTIA_COIN_DOVIZ"
                    }
        
        print(f"❌ '{target}' bulunamadı", file=sys.stderr)
        return {"found": False, "error": f"'{target}' Excel'de yok"}
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}", file=sys.stderr)
        return {"found": False, "error": str(e)}

# ==================== BASİT ANALİZ (API KEY GEREKMEZ) ====================
def generate_simple_analysis(sembol_adi, sembol_data, sembol_sayfa):
    """API key GEREKMEZ - Excel verilerinden basit analiz"""
    
    # Temel verileri al
    close = sembol_data.get('Close', 'N/A')
    vma = sembol_data.get('VMA', sembol_data.get('VMA trend algo', 'N/A'))
    durum = sembol_data.get('DURUM', 'N/A')
    ema_8 = sembol_data.get('EMA_8', 'N/A')
    pivot = sembol_data.get('Pivot', 'N/A')
    open_price = sembol_data.get('Open', 'N/A')
    high = sembol_data.get('High', 'N/A')
    low = sembol_data.get('Low', 'N/A')
    
    # Durum analizi
    durum_analiz = ""
    if "POZİTİF" in str(durum).upper():
        durum_analiz = "📈 **Pozitif Trend**"
    elif "NEGATİF" in str(durum).upper():
        durum_analiz = "📉 **Negatif Trend**"
    elif "NÖTR" in str(durum).upper():
        durum_analiz = "↔ **Yatay/Nötr**"
    
    # VMA analizi
    vma_analiz = ""
    if "POZİTİF" in str(vma).upper():
        vma_analiz = "✅ **VMA Pozitif** - Hacim trendi destekliyor"
    elif "NEGATİF" in str(vma).upper():
        vma_analiz = "⚠️ **VMA Negatif** - Hacim trendi desteklemiyor"
    
    # EMA analizi
    ema_analiz = ""
    try:
        if ema_8 != 'N/A' and close != 'N/A':
            ema_8_val = float(str(ema_8).replace(',', '.'))
            close_val = float(str(close).replace(',', '.'))
            if close_val > ema_8_val:
                ema_analiz = f"🚀 **Fiyat EMA_8 üzerinde** ({close_val} > {ema_8_val})"
            else:
                ema_analiz = f"📉 **Fiyat EMA_8 altında** ({close_val} < {ema_8_val})"
    except:
        ema_analiz = ""
    
    # Pivot analizi
    pivot_analiz = ""
    try:
        if pivot != 'N/A' and close != 'N/A':
            pivot_val = float(str(pivot).replace(',', '.'))
            close_val = float(str(close).replace(',', '.'))
            if close_val > pivot_val:
                pivot_analiz = f"⚖️ **Fiyat pivot üstünde** ({close_val} > {pivot_val})"
            else:
                pivot_analiz = f"⚖️ **Fiyat pivot altında** ({close_val} < {pivot_val})"
    except:
        pivot_analiz = ""
    
    # Analizi oluştur
    analysis = f"""📊 **{sembol_adi.upper()} TEKNİK ANALİZİ**

**Kaynak:** {sembol_sayfa} sayfası

**TEMEL VERİLER:**
• **Kapanış:** {close}
• **Açılış:** {open_price}
• **Yüksek:** {high}
• **Düşük:** {low}
• **VMA:** {vma}
• **EMA_8:** {ema_8}
• **Pivot:** {pivot}
• **Durum:** {durum}

**TEKNİK YORUM:**
{durum_analiz}
{vma_analiz}
{ema_analiz}
{pivot_analiz}

**ÖNERİLER:**
1. **VMA Pozitif** ise trend güçlü
2. **Fiyat EMA_8 üzerinde** ise kısa vade olumlu
3. **Fiyat pivot üstünde** ise direnç aşılabilir
4. **Durum GÜÇLÜ POZİTİF** ise yükseliş devam edebilir

⚠️ **NOT:** Bu analiz yatırım tavsiyesi değildir. Kendi araştırmanızı yapın."""
    
    return analysis

# ==================== BASİT HANDLER ====================
class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "online",
            "ai": "BorsaAnaliz AI 6.1",
            "version": "No API Key - Hızlı Mod",
            "features": "Özel sorular anında, hisse analizi Excel'den"
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
            
            print(f"\n🤖 SORU: {question}", file=sys.stderr)
            
            # Soru tipi
            question_type = analyze_question_type(question)
            print(f"🔍 Tip: {question_type}", file=sys.stderr)
            
            # Özel cevaplar (HIZLI MOD - API key gerekmez)
            special_answers = {
                "teşekkür": get_teşekkür_cevabı,
                "teknik": lambda: get_teknik_cevabı(question),
                "excel_macro": get_excel_macro_cevabı,
                "sistem": get_sistem_cevabı,
                "genel_borsa": get_genel_borsa_cevabı,
                "nasil": get_nasil_cevabı,
                "endeks": get_endeks_cevabı
            }
            
            if question_type in special_answers:
                answer = special_answers[question_type]()
                self.send_success_response(answer)
                print(f"📤 Hızlı cevap: {question_type}", file=sys.stderr)
                return
            
            # HİSSE ANALİZİ
            if question_type == "analiz":
                print("🔍 Hisse analizi...", file=sys.stderr)
                
                # Excel'i oku
                excel_result = read_excel_direct()
                
                if "error" in excel_result:
                    self.send_success_response("❌ Excel okunamadı. Lütfen daha sonra tekrar deneyin.")
                    return
                
                # Hisseyi ara (3 sayfada da)
                search_result = find_symbol_simple(question, excel_result)
                
                if not search_result.get("found"):
                    match = re.search(r'\b([A-Z]{2,6})\b', question.upper())
                    sembol_kodu = match.group(1) if match else "SEMBOL"
                    
                    # 3 sayfada aradığımızı belirt
                    answer = f"""❌ **{sembol_kodu} Excel'de bulunamadı.**

**3 SAYFA TARANDI:**
1. **Sinyaller:** 600+ hisse
2. **ENDEKSLER:** Tüm BIST endeksleri
3. **FON_EMTIA_COIN_DOVIZ:** GMSTR, ALTIN, döviz, emtia

**ÖRNEKLER (Farklı Sayfalar):**
• **FON:** "GMSTR analiz et", "ALTIN analiz et"
• **ENDEKSLER:** "XU100 analiz et", "XULAS analiz et"
• **SİNYALLER:** "ENKAI analiz et", "TUPRS analiz et"

**Popüler:** GMSTR, ALTIN, XU100, ENKAI, TUPRS, LOGO"""
                    
                    self.send_success_response(answer)
                    return
                
                # BASİT ANALİZ (API key GEREKMEZ)
                sembol_adi = search_result["name"]
                sembol_data = search_result["data"]
                sembol_sayfa = search_result.get("sayfa", "Sinyaller")
                
                print(f"✅ Bulundu: {sembol_adi} ({sembol_sayfa})", file=sys.stderr)
                
                # Excel verilerinden basit analiz oluştur
                analysis = generate_simple_analysis(sembol_adi, sembol_data, sembol_sayfa)
                
                # Cevapla
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = {
                    "success": True,
                    "answer": analysis,
                    "symbol": sembol_adi,
                    "sheet": sembol_sayfa,
                    "mode": "hızlı_mod",
                    "timestamp": datetime.now().isoformat()
                }
                
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
                print(f"📤 Gönderildi: {sembol_adi} ({sembol_sayfa})", file=sys.stderr)
                return
            
            # BİLİNMEYEN SORU
            self.send_success_response("""🤔 **Anlamadım**

**HIZLI MOD Örnekleri:**
• **Analiz:** "GMSTR analiz et", "XU100 durumu", "ENKAI hissesi"
• **Teknik:** "VMA nasıl yorumlanır?", "EMA nedir?"
• **Sistem:** "Excel macro nasıl açılır?", "Sistem hakkında"
• **Genel:** "Bugün öne çıkan hisseler"

**3 Sayfa Analiz:** Sinyaller, ENDEKSLER, FON_EMTIA_COIN_DOVIZ""")
            
        except Exception as e:
            print(f"❌ HATA: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self.send_error_response(f"Sistem hatası: {str(e)[:100]}")

    def send_success_response(self, answer):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        result = {"success": True, "answer": answer, "mode": "hızlı"}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
    
    def send_error_response(self, error):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        result = {"success": False, "answer": f"❌ Hata: {error}", "mode": "hızlı"}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

# ==================== TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 BorsaAnaliz AI 6.1: http://localhost:{port}")
    print("📊 HIZLI MOD - API key GEREKMEZ")
    print("✨ Özel sorular anında, hisse analizi Excel'den")
    server.serve_forever()
