#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - Doğrudan Excel Analiz Sistemi
# Versiyon: 4.1 (XU100 Fix + Genel Sorular Dahil)

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from datetime import datetime
import re
import ssl

# Excel processor import
from excel_processor import excel_processor

# SSL doğrulamasını devre dışı bırak
ssl._create_default_https_context = ssl._create_unverified_context

def clean_header(header):
    """Başlığı temizle: 'Hisse (06-02-2026)' -> 'Hisse'"""
    if not header:
        return ""
    header = str(header).split('(')[0].strip()
    header = re.sub(r'\s+', ' ', header)
    return header

def find_in_excel_data(question, excel_data):
    """Excel verilerinde arama - 3 SAYFADA TAM ARA"""
    try:
        question_upper = question.upper()
        
        # Arama terimlerini al
        search_terms = []
        for word in re.findall(r'[A-Z0-9]+', question_upper):
            if len(word) >= 2:  # En az 2 karakter
                search_terms.append(word)
        
        print(f"🔍 Aranan terimler: {search_terms}")
        
        # 1. ÖNCE: HİSSE ARA (Sinyaller sayfasında)
        if "Sinyaller" in excel_data["sheets"]:
            hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
            
            for term in search_terms:
                for hisse_adi, hisse_veriler in hisseler.items():
                    hisse_clean = re.sub(r'[^A-Z0-9]', '', hisse_adi.upper())
                    if term in hisse_clean or hisse_clean in term:
                        print(f"✅ {hisse_adi} Sinyaller sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "hisse",
                            "data": hisse_veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        # 2. SONRA: ENDEKS ARA (ENDEKSLER sayfasında)
        if "ENDEKSLER" in excel_data["sheets"]:
            endeksler = excel_data["sheets"]["ENDEKSLER"]["semboller"]
            
            # ÖNCE: XU100 ÖZEL ARAMA (TAM EŞLEŞME) - FIX EDİLDİ!
            if "XU100" in question_upper:
                # Önce tam eşleşme ara
                for sembol in endeksler.keys():
                    sembol_upper = sembol.upper()
                    if "XU100" in sembol_upper:
                        print(f"✅ XU100 bulundu: {sembol}")
                        return {
                            "found": True,
                            "type": "endeks",
                            "data": endeksler[sembol],
                            "sayfa": "ENDEKSLER",
                            "name": sembol
                        }
                
                # Tam bulunamazsa benzer ara
                benzer_endeksler = []
                for sembol in endeksler.keys():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol.upper())
                    if "XU" in sembol_clean or "BIST" in sembol_clean or "100" in sembol_clean:
                        benzer_endeksler.append(sembol)
                
                if benzer_endeksler:
                    ilk_endeks = benzer_endeksler[0]
                    print(f"⚠️ XU100 tam bulunamadı, en yakın endeks: {ilk_endeks}")
                    return {
                        "found": True,
                        "type": "endeks",
                        "data": endeksler[ilk_endeks],
                        "sayfa": "ENDEKSLER",
                        "name": ilk_endeks,
                        "not": f"XU100 tam bulunamadı, en yakın endeks: {ilk_endeks}"
                    }
            
            # DİĞER ENDEKS ARAMALARI
            for term in search_terms:
                for sembol_adi, sembol_veriler in endeksler.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} ENDEKSLER sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "endeks",
                            "data": sembol_veriler,
                            "sayfa": "ENDEKSLER",
                            "name": sembol_adi
                        }
        
        # 3. SON OLARAK: FON/EMTİA/DÖVİZ ARA
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            fonlar = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
            
            for term in search_terms:
                for sembol_adi, sembol_veriler in fonlar.items():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol_adi.upper())
                    if term in sembol_clean or sembol_clean in term:
                        print(f"✅ {sembol_adi} FON_EMTIA_COIN_DOVIZ sayfasında bulundu")
                        return {
                            "found": True,
                            "type": "fon_emtia",
                            "data": sembol_veriler,
                            "sayfa": "FON_EMTIA_COIN_DOVIZ",
                            "name": sembol_adi
                        }
        
        # Hiçbir şey bulunamadı
        print(f"⚠️ Hiçbir sayfada bulunamadı: {search_terms}")
        
        # Hangi semboller mevcut? (debug için)
        available_symbols = []
        if "Sinyaller" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["Sinyaller"]["hisseler"].keys())[:5])
        if "ENDEKSLER" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["ENDEKSLER"]["semboller"].keys())[:5])
        if "FON_EMTIA_COIN_DOVIZ" in excel_data["sheets"]:
            available_symbols.extend(list(excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"].keys())[:5])
        
        print(f"📋 Mevcut semboller (örnek): {available_symbols}")
        
        return {
            "found": False,
            "type": None,
            "data": None,
            "sayfa": None,
            "name": None,
            "available_symbols": available_symbols[:10]
        }
        
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        return {
            "found": False,
            "error": str(e)
        }

def analyze_question_type(question):
    """Sorunun tipini DETAYLI analiz et"""
    question_lower = question.lower().strip()
    
    # 1. TEŞEKKÜR/BEĞENİ SORULARI
    teşekkür_kelimeleri = [
        'teşekkür', 'sağ ol', 'sağol', 'güzel', 'harika', 'süper', 
        'müthiş', 'bravo', 'iyi', 'harikasın', 'süpersin', 'eline sağlık'
    ]
    for kelime in teşekkür_kelimeleri:
        if kelime in question_lower:
            return "teşekkür"
    
    # 2. SİSTEM SORULARI
    sistem_kelimeleri = [
        'kim', 'hangi', 'nasıl çalışır', 'nedir', 'sistem', 'ai', 
        'yapay zeka', 'ekip', 'geliştiren', 'yapan', 'oluşturan',
        'hakkında', 'bilgi', 'açıkla', 'anlat'
    ]
    for kelime in sistem_kelimeleri:
        if kelime in question_lower:
            return "sistem"
    
    # 3. TEKNİK ANALİZ SORULARI (VMA, EMA vs.)
    teknik_kelimeleri = [
        'vma', 'ema', 'pivot', 'rsi', 'macd', 'algoritma', 'algoritması',
        'yorumlanır', 'nasıl yorumlanır', 'ne demek', 'anlamı', 'nedir',
        'bollinger', 'bollinger band', 'teknik analiz', 'gösterge'
    ]
    for kelime in teknik_kelimeleri:
        if kelime in question_lower:
            return "teknik"
    
    # 4. GENEL BORSA SORULARI (YENİ EKLENDİ!)
    genel_borsa_kelimeleri = [
        'bugün öne çıkan', 'öne çıkan hisseler', 'en iyi hisseler',
        'tavsiye', 'öner', 'hangi hisse', 'ne alayım', 'ne alalım',
        'gündem', 'piyasa', 'borsa durumu', 'genel durum',
        'hangi sektör', 'sektörel', 'önerilerin', 'önerin',
        'neler popüler', 'popüler hisseler', 'hangi hisseler iyi'
    ]
    for kelime in genel_borsa_kelimeleri:
        if kelime in question_lower:
            return "genel_borsa"
    
    # 5. NASIL ÇALIŞIR SORULARI
    nasil_kelimeleri = [
        'nasıl analiz', 'nasıl çalışır', 'nasıl yapıyorsun', 'yöntem',
        'metod', 'süreç', 'proses', 'mekanizma'
    ]
    for kelime in nasil_kelimeleri:
        if kelime in question_lower:
            return "nasil"
    
    # 6. HİSSE ANALİZ SORULARI (son çare)
    hisse_kelimeleri = ['analiz', 'analiz et', 'hisse', 'hissesi', 'kaç', 'fiyat', 'durum', 'endeks']
    for kelime in hisse_kelimeleri:
        if kelime in question_lower:
            return "analiz"
    
    return "analiz"  # Varsayılan

def get_teşekkür_cevabı():
    """Teşekkür sorularına özel cevap"""
    return """🌟 **Teşekkür ederim!**

Ben BorsaAnaliz AI asistanıyım. Size yardımcı olabildiğim için mutluyum! 

Daha fazla hisse analizi veya borsa ile ilgili sorularınız için buradayım. 📊

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    """Sistem sorularına özel cevap"""
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Kuruluş:** 2024
**Versiyon:** 4.1 (XU100 Fix + Genel Sorular)

📊 **Sistem Özellikleri:**
• **630+ hisse** gerçek zamanlı analizi
• **Günlük güncellenen** Excel verileri
• **VMA Trend Algoritması** ile hacim analizi
• **EMA, Pivot, Bollinger Bant** teknik göstergeleri
• **AI destekli** yorumlama

🔧 **Nasıl Çalışır?**
1. Her sabah güncel Excel raporu indirilir
2. 630+ hissenin teknik verileri okunur
3. Sorunuzdaki hisse kodu aranır
4. Bulunan verilerle kısa teknik analiz oluşturulur

💡 **Örnek Sorular:**
• "FROTO analiz et"
• "VMA nedir?"
• "Borsanın genel durumu nasıl?"
• "XU100 endeksi analizi"
• "Nasıl analiz yapıyorsun?"

Sormak istediğiniz başka bir şey var mı?"""

def get_teknik_cevabı(question):
    """Teknik sorulara özel cevap"""
    question_lower = question.lower()
    
    if 'vma' in question_lower:
        return """📊 **VMA (Volume Moving Average) Trend Algoritması**

**VMA Nedir?**
VMA, "Hacim Hareketli Ortalama" anlamına gelir. Fiyat hareketlerinin hacimle desteklenip desteklenmediğini gösteren bir göstergedir.

**Nasıl Yorumlanır?**
• **POZİTİF (50-100):** Hacim trendi güçlü, fiyat hareketi güvenilir
• **POZİTİF (0-50):** Hacim trendi orta, dikkatli olunmalı
• **NEGATİF (0-50):** Hacim trendi zayıf, fiyat hareketi şüpheli
• **NEGATİF (50-100):** Hacim trendi çok zayıf, güvenilir değil

**Örnek Yorumlar:**
• "POZİTİF (75)" → Güçlü hacim desteği, trend sağlam
• "POZİTİF (25)" → Zayıf hacim desteği, dikkat edilmeli
• "NEGATİF (30)" → Hacim trend olumsuz, satış baskısı var

**Neden Önemli?**
VMA, sadece fiyat değil, işlem hacmini de analiz ederek daha güvenilir sinyaller verir.

Başka bir teknik gösterge hakkında sorunuz var mı?"""
    
    elif 'ema' in question_lower:
        return """📉 **EMA (Exponential Moving Average) - Üssel Hareketli Ortalama**

**EMA Nedir?**
EMA, fiyatların üssel olarak ağırlıklandırılmış ortalamasıdır. Son fiyatlara daha fazla önem verir.

**EMA Türleri:**
• **EMA_8:** Kısa vade (8 günlük) - Hızlı trend
• **EMA_21:** Orta vade (21 günlük) - Ana trend
• **EMA_55:** Uzun vade (55 günlük) - Büyük resim

**Nasıl Yorumlanır?**
• **EMA_8 > EMA_21 > EMA_55:** Güçlü yükseliş trendi ✓
• **EMA_8 < EMA_21 < EMA_55:** Güçlü düşüş trendi ✗
• **EMA'lar birbirine yakın:** Yatay/karışık trend ↔

**Örnek:**
EMA8: 100, EMA21: 95, EMA55: 90 → Tüm EMA'lar artıyor = Güçlü yükseliş

Başka sorunuz var mı?"""
    
    else:
        return """📈 **Teknik Analiz Göstergeleri**

**Temel Göstergeler:**
1. **VMA (Volume Moving Average):** Hacim trendi
2. **EMA (Exponential Moving Average):** Fiyat trendi
3. **Pivot Noktaları:** Destek/direnç seviyeleri
4. **Bollinger Bantları:** Volatilite seviyeleri

**Her bir gösterge hakkında detaylı bilgi almak için sorabilirsiniz:**
• "VMA nasıl yorumlanır?"
• "EMA nedir?"
• "Pivot seviyeleri nasıl kullanılır?"
• "Bollinger Bantları ne işe yarar?"

Hangi gösterge hakkında bilgi almak istersiniz?"""

def get_nasil_cevabı():
    """Nasıl çalıştığına dair sorulara cevap"""
    return """🔧 **Nasıl Analiz Yapıyorum?**

**Adım 1: Veri Toplama**
• Her sabah güncel Excel raporunu indiririm
• 630+ hissenin teknik verilerini okurum
• VMA, EMA, Pivot, Bollinger Bant verilerini alırım

**Adım 2: Hisse Bulma**
• Sorunuzdaki hisse kodunu çıkarırım (örnek: "FROTO")
• Excel'de bu hisseyi ararım
• Tüm teknik verilerini hazırlarım

**Adım 3: Analiz Oluşturma**
1. **Fiyat Analizi:** Mevcut fiyat ve günlük hareket
2. **VMA Analizi:** Hacim trendinin gücü
3. **EMA Analizi:** Kısa-orta-uzun vade trendleri
4. **Seviye Analizi:** Pivot, destek (S1), direnç (R1)
5. **Durum Değerlendirmesi:** Genel teknik durum

**Adım 4: Formatlama**
• 5-6 satırlık özet analiz oluştururum
• Emojilerle görselleştiririm
• Anlaşılır ve net dil kullanırım

**Örnek Analiz:**
📈 Fiyat: 115.7 TL
📊 VMA: POZİTİF (54) - Hacim trendi güçlü
📉 EMA: ✓ Güçlü yükseliş (8:113.66 21:108.50 55:101.63)
⚖️ Seviyeler: P:115.72 S1:114.35 R1:117.05
🎯 Durum: 🟡 NÖTR

**📊 Veri Kaynağı:** BorsaAnaliz günlük Excel raporları
**⏰ Güncelleme:** Her sabah otomatik

Başka sorunuz var mı?"""

def get_genel_borsa_cevabı(excel_data):
    """Genel borsa sorularına cevap"""
    try:
        if "Sinyaller" not in excel_data.get("sheets", {}):
            return "📊 Borsa genel durumu için Excel verileri yüklenemedi."
        
        hisseler = excel_data["sheets"]["Sinyaller"]["hisseler"]
        excel_date = excel_data.get("excel_date", "bilinmiyor")
        
        # En iyi 5 hisseyi bul (Pearson55 yüksek olanlar)
        top_hisseler = []
        for hisse_adi, hisse_veriler in hisseler.items():
            if "Pearson55" in hisse_veriler and "Close" in hisse_veriler:
                try:
                    pearson = float(hisse_veriler["Pearson55"])
                    close = hisse_veriler["Close"]
                    durum = hisse_veriler.get("DURUM", "N/A")
                    vma = hisse_veriler.get("VMA trend algo", "N/A")
                    
                    top_hisseler.append({
                        "hisse": hisse_adi,
                        "pearson": pearson,
                        "close": close,
                        "durum": durum,
                        "vma": vma
                    })
                except:
                    continue
        
        # Pearson'a göre sırala
        top_hisseler.sort(key=lambda x: x["pearson"], reverse=True)
        top_5 = top_hisseler[:5]
        
        # En düşük 5 hisseyi bul (Pearson55 düşük olanlar)
        worst_hisseler = sorted(top_hisseler, key=lambda x: x["pearson"])[:5]
        
        response = []
        response.append(f"📊 **BUGÜN ÖNE ÇIKAN HİSSELER** ({excel_date})")
        response.append("=" * 50)
        response.append("")
        response.append("🏆 **PEARSON55 EN YÜKSEK 5 HİSSE:**")
        response.append("")
        
        for i, hisse in enumerate(top_5, 1):
            hisse_adi = hisse["hisse"]
            pearson = hisse["pearson"]
            close = hisse["close"]
            durum = hisse["durum"]
            vma = hisse["vma"]
            
            # Durum emojisi
            if "GÜÇLÜ POZİTİF" in str(durum).upper():
                durum_emoji = "🟢"
            elif "POZİTİF" in str(durum).upper():
                durum_emoji = "🟢"
            elif "GÜÇLÜ NEGATİF" in str(durum).upper():
                durum_emoji = "🔴"
            elif "NEGATİF" in str(durum).upper():
                durum_emoji = "🔴"
            elif "NÖTR" in str(durum).upper():
                durum_emoji = "🟡"
            else:
                durum_emoji = "⚪"
            
            # VMA emojisi
            if "POZİTİF" in str(vma).upper():
                vma_emoji = "📈"
            elif "NEGATİF" in str(vma).upper():
                vma_emoji = "📉"
            else:
                vma_emoji = "↔️"
            
            response.append(f"{i}. **{hisse_adi}**")
            response.append(f"   • Pearson55: **{pearson:.3f}**")
            response.append(f"   • Fiyat: {close} TL")
            response.append(f"   • Durum: {durum_emoji} {durum}")
            response.append(f"   • VMA: {vma_emoji} {vma}")
            response.append("")
        
        response.append("⚠️ **EN DÜŞÜK PEARSON55 (DİKKAT EDİLMESİ GEREKENLER):**")
        response.append("")
        
        for i, hisse in enumerate(worst_hisseler[:3], 1):
            hisse_adi = hisse["hisse"]
            pearson = hisse["pearson"]
            durum = hisse["durum"]
            
            if "NEGATİF" in str(durum).upper():
                durum_emoji = "🔴"
            else:
                durum_emoji = "🟡"
            
            response.append(f"{i}. **{hisse_adi}** - Pearson55: **{pearson:.3f}** {durum_emoji}")
        
        response.append("")
        response.append("📈 **TOPLAM HİSSE SAYISI:** {}".format(len(hisseler)))
        response.append("")
        response.append("💡 **İPUCU:** Daha detaylı analiz için hisse adını yazın.")
        response.append("Örnek: \"FROTO analiz et\", \"THYAO durumu\", \"XU100 endeksi\"")
        
        return "\n".join(response)
        
    except Exception as e:
        print(f"❌ Genel borsa cevabı hatası: {e}")
        return "📊 Borsa genel durumu analiz ediliyor... Lütfen biraz bekleyin veya spesifik bir hisse sorun."

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # Excel processor'dan güncel bilgi al
        try:
            excel_info = {
                "status": "online",
                "ai": "BORSAANALIZ AI - GÜNCEL EXCEL ANALİZ",
                "version": "4.1 (XU100 Fix + Genel Sorular)",
                "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "features": [
                    "630+ hisse analizi",
                    "3 sayfa tam okuma (Sinyaller, ENDEKSLER, FON_EMTIA)",
                    "Güncel Excel otomatik bulma",
                    "VMA, EMA, Pivot analizi",
                    "Doğal dil anlama",
                    "XU100 endeks analizi",
                    "Genel borsa durumu"
                ],
                "example_queries": [
                    "FROTO analiz et",
                    "XU100 endeksi analiz et",
                    "VMA nedir?",
                    "Bugün öne çıkan hisseler",
                    "Borsanın genel durumu"
                ],
                "fixes": [
                    "XU100 endeks arama düzeltildi",
                    "Genel borsa soruları eklendi",
                    "Büyük/küçük harf duyarlılığı düzeltildi"
                ]
            }
        except Exception as e:
            excel_info = {
                "status": "online",
                "ai": "BORSAANALIZ AI",
                "note": "Excel sistemi hazırlanıyor",
                "error": str(e)
            }
        
        response = json.dumps(excel_info, ensure_ascii=False, indent=2)
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
            print(f"🤖 GÜNCEL EXCEL ANALİZ: {question}")
            print("="*70)
            
            # 2. Soru tipini analiz et
            question_type = analyze_question_type(question)
            print(f"🔍 Soru tipi: {question_type}")
            
            # 3. ÖZEL SORU TİPLERİ için direkt cevap
            if question_type in ["teşekkür", "sistem", "teknik", "nasil"]:
                print(f"✅ Özel cevap hazırlanıyor: {question_type}")
                
                if question_type == "teşekkür":
                    answer = get_teşekkür_cevabı()
                elif question_type == "sistem":
                    answer = get_sistem_cevabı()
                elif question_type == "teknik":
                    answer = get_teknik_cevabı(question)
                elif question_type == "nasil":
                    answer = get_nasil_cevabı()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": False,
                    "question_type": question_type,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Özel yanıt gönderildi: {question_type}")
                print("="*70 + "\n")
                return
            
            # 4. EXCEL'DEN VERİ AL (GÜNCEL)
            print("🔍 Güncel Excel bulunuyor ve okunuyor...")
            excel_start = datetime.now()
            
            try:
                excel_result = excel_processor.read_excel_data()
                excel_time = (datetime.now() - excel_start).total_seconds()
                excel_date = excel_result.get("excel_date", "bilinmiyor")
                
                print(f"✅ Excel okundu: {excel_result.get('total_symbols', 0)} sembol, {excel_time:.2f}s")
                print(f"📅 Excel tarihi: {excel_date}")
                
                # Hangi sayfalar mevcut?
                sheets = list(excel_result.get("sheets", {}).keys())
                print(f"📑 Mevcut sayfalar: {sheets}")
                
            except Exception as e:
                print(f"❌ Excel okuma hatası: {str(e)}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": f"❌ Excel dosyası okunamadı.\n\nHata: {str(e)[:100]}\n\nLütfen daha sonra tekrar deneyin.",
                    "excel_data_used": False,
                    "error": str(e)[:100],
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                return
            
            # 5. GENEL BORSA SORUSU ise özel cevap
            if question_type == "genel_borsa":
                print("📊 Genel borsa sorusu işleniyor...")
                answer = get_genel_borsa_cevabı(excel_result)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": True,
                    "question_type": "genel_borsa",
                    "excel_date": excel_date,
                    "total_symbols": excel_result.get("total_symbols", 0),
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Genel borsa yanıtı gönderildi")
                print("="*70 + "\n")
                return
            
            # 6. SORUYU EXCEL VERİLERİNDE ARA (3 SAYFADA)
            print("🔍 Soru Excel verilerinde analiz ediliyor (3 sayfada TAM arama)...")
            analysis = find_in_excel_data(question, excel_result)
            
            # 7. API Key kontrolü
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                # Fallback: Basit yanıt oluştur
                if analysis.get("found"):
                    sembol_data = analysis["data"]
                    sembol_name = analysis["name"]
                    sayfa_name = analysis["sayfa"]
                    
                    # Basit analiz oluştur
                    response_parts = []
                    response_parts.append(f"📊 **{sembol_name.upper()} TEKNİK ANALİZİ**")
                    response_parts.append(f"📅 Excel Tarihi: {excel_date}")
                    response_parts.append(f"📑 Kaynak Sayfa: {sayfa_name}")
                    response_parts.append("")
                    
                    # Ana göstergeleri göster
                    important_fields = [
                        ('Close', 'Fiyat'),
                        ('VMA trend algo', 'VMA Trend'),
                        ('DURUM', 'Durum'),
                        ('EMA_8', 'EMA 8'),
                        ('EMA_21', 'EMA 21'),
                        ('EMA_55', 'EMA 55'),
                        ('Pivot', 'Pivot'),
                        ('S1', 'Destek (S1)'),
                        ('R1', 'Direnç (R1)')
                    ]
                    
                    for field, display_name in important_fields:
                        if field in sembol_data:
                            value = sembol_data[field]
                            response_parts.append(f"• **{display_name}:** {value}")
                    
                    response_parts.append("")
                    response_parts.append("💡 **Not:** Daha detaylı analiz için API anahtarı gerekli.")
                    answer = "\n".join(response_parts)
                else:
                    answer = "❌ **Sembol Excel'de bulunamadı.**\n\n"
                    answer += "Lütfen sembol adını kontrol edin:\n"
                    answer += "• Hisseler: FROTO, THYAO, TUPRS, SASA, EREGL, KCHOL\n"
                    answer += "• Endeksler: XU100, XTEKS, XULAS\n"
                    answer += "• Diğer: GMSTR, ALTIN, USD, BTC\n\n"
                    answer += "Örnek: \"FROTO analiz et\""
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": analysis.get("found", False),
                    "symbol": analysis.get("name"),
                    "sheet": analysis.get("sayfa"),
                    "excel_date": excel_date,
                    "total_symbols": excel_result.get("total_symbols", 0),
                    "execution_time": excel_time,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Basit yanıt gönderildi (API key yok)")
                print("="*70 + "\n")
                return
            
            # 8. PROMPT HAZIRLA
            prompt = f"""🎯 **BORSAANALIZ AI - GERÇEK EXCEL VERİ ANALİZİ**

**📊 GÜNCEL EXCEL RAPORU:** {os.path.basename(excel_result.get('excel_url', 'bilinmiyor'))} ({excel_date})
**⏰ ANALİZ ZAMANI:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
**📈 TOPLAM SEMBOL:** {excel_result.get('total_symbols', 0)} (3 sayfa)

**❓ KULLANICI SORUSU:** {question}

"""
            
            # BULUNAN VERİLERİ EKLE
            if analysis.get("found"):
                sembol_data = analysis["data"]
                sembol_name = analysis["name"]
                sayfa_name = analysis["sayfa"]
                
                prompt += f"""📊 **{sembol_name.upper()} ANALİZİ**

**KAYNAK:** {sayfa_name} sayfası (Excel'de bulundu)
**EXCEL TARİHİ:** {excel_date}
**VERİLER (Excel'den alındı):**

"""
                
                # ÖNEMLİ ALANLARI GÖSTER
                important_fields = [
                    'Close', 'Open', 'High', 'Low', 'Hacim',
                    'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55',
                    'Pivot', 'S1', 'R1', 'BB_UPPER', 'BB_LOWER',
                    'Pearson55', 'DURUM', 'AI_YORUM'
                ]
                
                fields_found = 0
                for field in important_fields:
                    if field in sembol_data:
                        value = sembol_data[field]
                        prompt += f"• **{field}:** {value}\n"
                        fields_found += 1
                
                if fields_found > 0:
                    prompt += f"\n✅ **{sembol_name}** Excel'de bulundu. Yukarıdaki değerler GERÇEKTİR.\n\n"
                else:
                    prompt += f"\n⚠️ **{sembol_name}** Excel'de bulundu ama teknik veriler eksik.\n\n"
                
                # Özel not
                if analysis.get("not"):
                    prompt += f"**Not:** {analysis['not']}\n\n"
            
            else:
                prompt += """⚠️ **UYARI:** Sorunuzdaki sembol Excel'de bulunamadı.

**EXCEL'DE MEVCUT OLANLAR (3 SAYFA):**
• **Sinyaller:** 630+ hisse senedi (A1CAP, FROTO, THYAO, TUPRS, SASA, EREGL, KCHOL, ASELS, GARAN, BIMAS vb.)
• **ENDEKSLER:** BIST endeksleri (XTEKS, XULAS, XU serisi vb.)
• **FON_EMTIA_COIN_DOVIZ:** Döviz, emtia, kripto para (GMSTR, ALTIN, USD, EUR, BTC, ETH vb.)

**Lütfen:**
1. Sembol adını doğru yazın
2. Büyük/küçük harf fark etmez
3. Örnek: "FROTO analiz et", "GMSTR teknik durumu", "XU100 endeksi"

"""
                if analysis.get("available_symbols"):
                    prompt += f"**Örnek semboller:** {', '.join(analysis['available_symbols'][:8])}\n\n"
            
            # ANALİZ TALİMATLARI
            prompt += """🎯 **ANALİZ TALİMATLARI:**

1. **SADECE** yukarıdaki Excel verilerini kullan
2. **VMA trend algo** değerini MUTLAKA analiz et (Örnek: "POZİTİF (50)")
3. Close, EMA_8, EMA_21, EMA_55 değerlerini karşılaştır
4. Pivot, S1, R1 seviyelerini belirt
5. **DURUM** alanını yorumla (GÜÇLÜ POZİTİF/ZAYIF vb.)
6. **AI_YORUM** alanındaki özeti dikkate al
7. **RSI/MACD YOK** - onlardan bahsetme
8. Sayısal değerleri net belirt (Örnek: "Close: 712,5 TL")
9. **YATIRIM TAVSİYESİ VERME** - sadece teknik analiz
10. Kapsamlı ama öz olsun (300-400 kelime)

📊 **ANALİZ FORMATI:**
**1. TEMEL VERİLER:** Fiyat, VMA, EMA'lar
**2. TEKNİK YORUM:** VMA analizi, trend yapısı
**3. KRİTİK SEVİYELER:** Pivot, destek (S1), direnç (R1)
**4. GENEL DEĞERLENDİRME:** Durum ve riskler

**CEVAP:**
"""
            
            print(f"📝 Prompt hazır ({len(prompt):,} karakter)")
            
            # 9. DEEPSEEK API'Yİ ÇAĞIR
            ai_start = datetime.now()
            try:
                # API çağrısı için gerekli import
                import requests
                
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "Sen BorsaAnaliz AI asistanısın. Sadece verilen Excel verilerini kullanarak teknik analiz yap."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
                
                response = requests.post(
                    'https://api.deepseek.com/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                ai_time = (datetime.now() - ai_start).total_seconds()
                
                if response.status_code == 200:
                    ai_response = response.json()
                    answer = ai_response['choices'][0]['message']['content']
                    print(f"✅ AI yanıtı alındı: {ai_time:.2f}s")
                else:
                    answer = f"❌ API hatası: {response.status_code}\n\n"
                    answer += "Basit analiz:\n"
                    if analysis.get("found"):
                        sembol_name = analysis.get("name")
                        answer += f"• **{sembol_name}** Excel'de bulundu\n"
                        answer += "• Detaylı analiz için API erişimi gerekli\n"
                    else:
                        answer += "• Sembol Excel'de bulunamadı\n"
                    
                    print(f"⚠️ API hatası: {response.status_code}")
            
            except Exception as e:
                ai_time = (datetime.now() - ai_start).total_seconds()
                answer = f"❌ AI analiz hatası: {str(e)[:100]}\n\n"
                answer += "Lütfen daha sonra tekrar deneyin."
                print(f"❌ AI hatası: {e}")
            
            # 10. YANITI GÖNDER
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            result = json.dumps({
                "success": True,
                "answer": answer,
                "excel_data_used": analysis.get("found", False),
                "symbol": analysis.get("name"),
                "sheet": analysis.get("sayfa"),
                "excel_date": excel_date,
                "total_symbols": excel_result.get("total_symbols", 0),
                "execution_time": excel_time,
                "ai_time": ai_time if 'ai_time' in locals() else None,
                "question_type": question_type,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))
            print(f"📤 Yanıt gönderildi. Toplam süre: {excel_time:.2f}s")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"❌ Genel hata: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            result = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası: {str(e)[:100]}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))
