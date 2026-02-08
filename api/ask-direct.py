#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /api/ask-direct.py
# BorsaAnaliz AI - Doğrudan Excel Analiz Sistemi
# Versiyon: 4.1 (ÇALIŞAN - Her Türlü Soru)

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
from datetime import datetime
import re
import ssl
import sys
import traceback

# Excel processor import - ESKİ SİSTEM
try:
    from excel_processor import excel_processor
except ImportError:
    import sys
    sys.path.append('..')
    from excel_processor import excel_processor

# SSL doğrulamasını devre dışı bırak
ssl._create_default_https_context = ssl._create_unverified_context

# ==================== SORU TİPİ ANALİZİ ====================
def analyze_question_type(question):
    """Sorunun tipini BASİTÇE analiz et"""
    question_lower = question.lower().strip()
    
    # 1. TEŞEKKÜR/BEĞENİ
    if any(k in question_lower for k in ['teşekkür', 'sağ ol', 'sağol', 'güzel', 'harika']):
        return "teşekkür"
    
    # 2. SİSTEM SORULARI
    if any(k in question_lower for k in ['kim yaptı', 'kim geliştirdi', 'sistem hakkında', 'hangi ai']):
        return "sistem"
    
    # 3. TEKNİK ANALİZ
    if any(k in question_lower for k in ['vma', 'ema', 'pivot', 'teknik analiz']):
        return "teknik"
    
    # 4. GENEL BORSA
    if any(k in question_lower for k in ['öne çıkan', 'borsa durumu', 'genel durum', 'hangi hisseler']):
        return "genel_borsa"
    
    # 5. NASIL ÇALIŞIR
    if 'nasıl çalışır' in question_lower or 'nasıl analiz' in question_lower:
        return "nasil"
    
    # 6. HİSSE ANALİZİ (varsayılan)
    return "analiz"

# ==================== ÖZEL CEVAPLAR ====================
def get_teşekkür_cevabı():
    return """🌟 **Teşekkür ederim!**

Ben BorsaAnaliz AI asistanıyım. Size yardımcı olabildiğim için mutluyum! 

Daha fazla hisse analizi veya borsa ile ilgili sorularınız için buradayım. 📊

Başka hangi hisseyi analiz etmemi istersiniz?"""

def get_sistem_cevabı():
    return """🤖 **BorsaAnaliz AI Sistemi**

**Geliştirici:** BorsaAnaliz Ekibi
**Kuruluş:** 2024
**Versiyon:** 4.1

📊 **Sistem Özellikleri:**
• **637+ hisse** gerçek zamanlı analizi
• **Günlük güncellenen** Excel verileri
• **VMA Trend Algoritması** ile hacim analizi
• **EMA, Pivot, Bollinger Bant** teknik göstergeleri
• **AI destekli** yorumlama

🔧 **Nasıl Çalışır?**
1. Her akşam güncel Excel raporu indirilir
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

**VMA Algo Nedir?**
VMA Algo, "Hacim Ağırlıklı Algoritma" anlamına gelir. Fiyat hareketlerinin hacimle desteklenip desteklenmediğini gösteren bir algoritmadır.

**Nasıl Yorumlanır?**
• **POZİTİF (00):** Trendin başladığını gösterir (parantez içindeki rakam gün sayısıdır)
• **POZİTİF (--):** Algoritma trendin günlük periyotta devam ettiğini söyler
• **NEGATİF (00):** Trendin bittiğini gösterir (parantez içindeki rakam gün sayısıdır)
• **NEGATİF (--):** Algoritma trendin günlük periyotta bittiğini söyler

**Neden Önemli?**
VMA Algo, sadece fiyat değil, işlem hacmini de analiz ederek daha güvenilir sinyaller verir.

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
1. **VMA (Volume Moving Average Algo):** Hacim trendi
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
• Her akşam güncel Excel raporunu indiririm
• 630+ hissenin teknik verilerini okurım
• VMA, EMA, Pivot, Bollinger Bant verilerini alırım

**Adım 2: Hisse Bulma**
• Sorunuzdaki hisse kodunu çıkarırım (örnek: "FROTO")
• Excel'de bu hisseyi ararım
• Tüm teknik verilerini hazırlarım

**Adım 3: Analiz Oluşturma**
1. **Fiyat Analizi:** Mevcut fiyat ve günlük hareket
2. **VMA Analizi:** Hacim trendinin gücü
3. **EMA Analizi:** Kısa-orta-uzun vade trendleri
4. **Denge Analizi:** Pivot, destek (S1), direnç (R1)
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
**⏰ Güncelleme:** Her akşam otomatik

Başka sorunuz var mı?"""

def get_genel_borsa_cevabı(excel_data):
    """Genel borsa sorularına cevap"""
    try:
        if "Sinyaller" not in excel_data.get("sheets", {}):
            return "📊 Borsa genel durumu için Excel verileri yüklenemedi."
        
        hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
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

# ==================== BASİT HİSSE ARAMA ====================
def find_hisse_basit(question, excel_data):
    """BASİT hisse arama - 637 hisse için"""
    try:
        # Sorudaki tüm büyük harf kelimeleri al
        words = re.findall(r'[A-Z]{2,6}', question.upper())
        
        if not words:
            return {"found": False, "error": "Hisse kodu bulunamadı"}
        
        print(f"🔍 Aranan kelimeler: {words}")
        
        # ÖNCE Sinyaller sayfasında ara
        if "Sinyaller" in excel_data.get("sheets", {}):
            hisseler = excel_data["sheets"]["Sinyaller"].get("hisseler", {})
            
            print(f"📊 {len(hisseler)} hisse aranıyor...")
            
            # İlk 10 hisseyi göster (debug)
            hisse_list = list(hisseler.keys())[:10]
            print(f"📋 Örnek hisseler: {hisse_list}")
            
            # Her kelime için ara
            for word in words:
                print(f"  → '{word}' aranıyor...")
                
                # 1. Tam eşleşme
                if word in hisseler:
                    print(f"  ✅ Tam eşleşme bulundu: {word}")
                    return {
                        "found": True,
                        "type": "hisse",
                        "data": hisseler[word],
                        "sayfa": "Sinyaller",
                        "name": word
                    }
                
                # 2. Kısmi eşleşme (A1CAP in A1CAPITAL)
                for hisse_adi, hisse_veriler in hisseler.items():
                    hisse_clean = re.sub(r'[^A-Z]', '', hisse_adi.upper())
                    
                    if word in hisse_clean:
                        print(f"  ✅ Kısmi eşleşme: '{word}' -> '{hisse_adi}'")
                        return {
                            "found": True,
                            "type": "hisse",
                            "data": hisse_veriler,
                            "sayfa": "Sinyaller",
                            "name": hisse_adi
                        }
        
        print(f"❌ Hiçbir hisse bulunamadı")
        return {"found": False, "error": "Hisse bulunamadı"}
        
    except Exception as e:
        print(f"❌ Basit arama hatası: {e}")
        traceback.print_exc()
        return {"found": False, "error": str(e)}

# ==================== VERCEL HANDLER ====================
class handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Vercel logları için"""
        print(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """GET istekleri için"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "status": "online",
                "ai": "BORSAANALIZ AI - ÇALIŞAN SİSTEM",
                "version": "4.1 (Basit ve Etkili)",
                "endpoint": "/api/ask-direct",
                "method": "POST JSON: {'question': 'sorunuz'}",
                "example_queries": [
                    "FROTO analiz et",
                    "A1CAP analiz et", 
                    "XU100 endeksi analiz et",
                    "Bugün öne çıkan hisseler",
                    "VMA nedir?",
                    "Sistem hakkında bilgi"
                ],
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
            print("✅ GET isteği başarılı")
            
        except Exception as e:
            print(f"❌ GET hatası: {e}")
    
    def do_POST(self):
        """POST istekleri için - ÇALIŞAN SİSTEM"""
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
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            print(f"\n{'='*70}")
            print(f"🤖 YENİ SORU: {question}")
            print('='*70)
            
            # 2. Soru tipini analiz et
            question_type = analyze_question_type(question)
            print(f"🔍 Soru tipi: {question_type}")
            
            # 3. ÖZEL SORU TİPLERİ için direkt cevap
            if question_type in ["teşekkür", "sistem", "teknik", "nasil", "genel_borsa"]:
                print(f"✅ Özel cevap hazırlanıyor: {question_type}")
                
                if question_type == "teşekkür":
                    answer = get_teşekkür_cevabı()
                elif question_type == "sistem":
                    answer = get_sistem_cevabı()
                elif question_type == "teknik":
                    answer = get_teknik_cevabı(question)
                elif question_type == "nasil":
                    answer = get_nasil_cevabı()
                elif question_type == "genel_borsa":
                    # Excel verilerini al
                    print("🔍 Güncel Excel okunuyor...")
                    try:
                        excel_result = excel_processor.read_excel_data()
                        print(f"✅ Excel okundu: {excel_result.get('total_symbols', 0)} sembol")
                        answer = get_genel_borsa_cevabı(excel_result)
                    except Exception as e:
                        print(f"❌ Excel okuma hatası: {e}")
                        answer = "📊 Borsa genel durumu için Excel verileri yüklenemedi."
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "excel_data_used": question_type == "genel_borsa",
                    "question_type": question_type,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Özel yanıt gönderildi: {question_type}")
                print('='*70 + '\n')
                return
            
            # 4. HİSSE ANALİZİ için Excel verilerini al
            print("🔍 Hisse analizi için Excel okunuyor...")
            excel_start = datetime.now()
            
            try:
                excel_result = excel_processor.read_excel_data()
                excel_time = (datetime.now() - excel_start).total_seconds()
                excel_date = excel_result.get("excel_date", "bilinmiyor")
                
                print(f"✅ Excel okundu: {excel_result.get('total_symbols', 0)} sembol, {excel_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Excel okuma hatası: {e}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": f"❌ Excel dosyası okunamadı.\n\nLütfen daha sonra tekrar deneyin.",
                    "excel_data_used": False,
                    "error": str(e)[:100]
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                return
            
            # 5. BASİT ARAMA YAP
            print("🔍 Basit hisse araması yapılıyor...")
            analysis = find_hisse_basit(question, excel_result)
            
            if not analysis.get("found"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                answer = "❌ **Hisse bulunamadı.**\n\n"
                answer += "**Lütfen hisse kodunu doğru yazın:**\n"
                answer += "• FROTO, THYAO, TUPRS, SASA, EREGL\n"
                answer += "• KCHOL, ASELS, GARAN, BIMAS, A1CAP\n"
                answer += "• ARCLK, TCELL, HEKTS, AKBNK, YKBNK\n\n"
                answer += "**Örnek:** \"FROTO analiz et\""
                
                result = json.dumps({
                    "success": False,
                    "answer": answer,
                    "excel_data_used": False,
                    "question_type": "analiz"
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print("📤 Hisse bulunamadı uyarısı gönderildi")
                return
            
            # 6. AI ANALİZİ İÇİN PROMPT HAZIRLA (SİZİN PROMPT DEĞİŞİKLİKLERİYLE)
            sembol_data = analysis["data"]
            sembol_name = analysis["name"]
            
            prompt = f"""🎯 **BORSAANALIZ AI - GERÇEK EXCEL VERİ ANALİZİ**

**📊 GÜNCEL EXCEL RAPORU:** {excel_result.get('excel_url', 'bilinmiyor')} ({excel_date})
**⏰ ANALİZ ZAMANI:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
**📈 TOPLAM SEMBOL:** {excel_result.get('total_symbols', 0)} (3 sayfa)

**❓ KULLANICI SORUSU:** {question}

📊 **{sembol_name.upper()} ANALİZİ**

**KAYNAK:** {analysis.get('sayfa', 'Sinyaller')} sayfası (Excel'de bulundu)
**EXCEL TARİHİ:** {excel_date}
**VERİLER (Excel'den alındı - GERÇEK VERİLER):**

"""
            
            # ÖNEMLİ ALANLARI GÖSTER
            important_fields = [
                'Close', 'Open', 'High', 'Low', 'Hacim',
                'VMA trend algo', 'EMA_8', 'EMA_21', 'EMA_55',
                'Pivot', 'S1', 'R1', 'BB_UPPER', 'BB_LOWER',
                'Pearson55', 'DURUM', 'AI_YORUM'
            ]
            
            for field in important_fields:
                if field in sembol_data:
                    value = sembol_data[field]
                    prompt += f"• **{field}:** {value}\n"
            
            prompt += f"\n✅ **{sembol_name}** Excel'de bulundu. Yukarıdaki değerler GERÇEKTİR.\n\n"
            
            # ANALİZ TALİMATLARI (SİZİN DEĞİŞİKLİKLERİNİZLE)
            prompt += """🎯 **ANALİZ TALİMATLARI:**

1. **SADECE** yukarıdaki Excel verilerini kullan
2. **VMA trend algo** değerini MUTLAKA analiz et (Örnek: "POZİTİF (50)")
3. Close, EMA_8, EMA_21, EMA_55 değerlerini karşılaştır
4. WT Sinyal, LSMA KAMA değerlerini analiz et
5. Pivot, S1, R1 seviyelerini belirt
6. **DURUM** alanını yorumla (GÜÇLÜ POZİTİF/ZAYIF vb.)
7. **AI_YORUM** alanındaki özeti dikkate al
8. **RSI/MACD YOK** - onlardan bahsetme
9. Sayısal değerleri net belirt (Örnek: "Close: 712,5 TL")
10. **YATIRIM TAVSİYESİ VERME** - sadece teknik analiz
11. Kapsamlı ama öz olsun (300-400 kelime)

📊 **ANALİZ FORMATI:**
**1. TEMEL VERİLER:** Fiyat, VMA, EMA'lar, WT Sinyal, LSMA KAMA
**2. TEKNİK YORUM:** VMA analizi, trend yapısı
**3. KRİTİK SEVİYELER:** Pivot, destek (S1), direnç (R1)
**4. GENEL DEĞERLENDİRME:** Durum ve riskler

**CEVAP:**
"""
            
            print(f"📝 Prompt hazır ({len(prompt):,} karakter)")
            
            # 7. DEEPSEEK API ÇAĞRISI
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            ai_answer = ""
            
            if api_key:
                try:
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
                    
                    print("🤖 AI çağrısı yapılıyor...")
                    response = requests.post(
                        'https://api.deepseek.com/v1/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        ai_response = response.json()
                        ai_answer = ai_response['choices'][0]['message']['content']
                        print("✅ AI yanıtı alındı")
                    else:
                        ai_answer = f"❌ API hatası: {response.status_code}"
                        print(f"⚠️ API hatası: {response.status_code}")
                        
                except Exception as e:
                    ai_answer = f"❌ AI analiz hatası: {str(e)[:100]}"
                    print(f"❌ AI hatası: {e}")
            else:
                ai_answer = "❌ API anahtarı bulunamadı. Detaylı analiz yapılamıyor."
                print("⚠️ API anahtarı yok")
            
            # 8. YANITI GÖNDER
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = json.dumps({
                "success": True,
                "answer": ai_answer,
                "excel_data_used": True,
                "symbol": sembol_name,
                "sheet": analysis.get("sayfa"),
                "excel_date": excel_date,
                "total_symbols": excel_result.get("total_symbols", 0),
                "execution_time": excel_time,
                "question_type": "analiz",
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))
            print(f"📤 Yanıt gönderildi. Toplam süre: {excel_time:.2f}s")
            print('='*70 + '\n')
            
        except Exception as e:
            print(f"❌ Genel POST hatası: {e}")
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            result = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası: {str(e)[:100]}",
                "error": str(e)
            }, ensure_ascii=False)
            
            self.wfile.write(result.encode('utf-8'))

# ==================== LOCAL TEST ====================
if __name__ == "__main__":
    from http.server import HTTPServer
    
    port = 3002
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 BorsaAnaliz AI çalışıyor: http://localhost:{port}/api/ask-direct")
    server.serve_forever()
