# /api/ask-direct.py (GÜNCELLENMİŞ - excel_processor ile)
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
            
            # ÖZEL: XU100 araması
            if "XU100" in question_upper:
                benzer_endeksler = []
                for sembol in endeksler.keys():
                    sembol_clean = re.sub(r'[^A-Z0-9]', '', sembol.upper())
                    if "XU" in sembol_clean or "BIST" in sembol_clean:
                        benzer_endeksler.append(sembol)
                
                if benzer_endeksler:
                    ilk_endeks = benzer_endeksler[0]
                    print(f"⚠️ XU100 bulunamadı, en yakın endeks: {ilk_endeks}")
                    return {
                        "found": True,
                        "type": "endeks",
                        "data": endeksler[ilk_endeks],
                        "sayfa": "ENDEKSLER",
                        "name": ilk_endeks,
                        "not": f"XU100 bulunamadı, en yakın endeks: {ilk_endeks}"
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
    
    return "analiz"

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # Excel processor'dan güncel bilgi al
        try:
            # Sadece cache'den kontrol et, okuma yapma
            excel_info = {
                "status": "online",
                "ai": "BORSAANALIZ AI - GÜNCEL EXCEL ANALİZ",
                "excel_system": "excel_processor aktif",
                "cache_system": "1 saat cache",
                "sheets": ["Sinyaller (630+ hisse)", "ENDEKSLER", "FON_EMTIA_COIN_DOVIZ"]
            }
        except:
            excel_info = {
                "status": "online",
                "ai": "BORSAANALIZ AI",
                "note": "Excel sistemi hazırlanıyor"
            }
        
        response = json.dumps(excel_info, ensure_ascii=False)
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
                
                print(f"✅ Excel okundu: {excel_result['total_symbols']} sembol, {excel_time:.2f}s")
                print(f"📅 Excel tarihi: {excel_date}")
                
            except Exception as e:
                print(f"❌ Excel okuma hatası: {str(e)}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                result = json.dumps({
                    "success": False,
                    "answer": "❌ Excel dosyası okunamadı. Lütfen:\n1. Excel'in sitede olduğundan emin olun\n2. Hisse adını doğru yazın\n3. Daha sonra tekrar deneyin",
                    "excel_data_used": False,
                    "error": str(e)[:100]
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                return
            
            # 5. SORUYU EXCEL VERİLERİNDE ARA (3 SAYFADA)
            print("🔍 Soru Excel verilerinde analiz ediliyor (3 sayfada TAM arama)...")
            analysis = find_in_excel_data(question, excel_result)
            
            # 6. API Key
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                # Fallback: Basit yanıt
                answer = self.create_simple_response(analysis, excel_result, excel_date)
                
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
                    "execution_time": excel_time
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 Basit yanıt gönderildi (API key yok)")
                print("="*70 + "\n")
                return
            
            # 7. PROMPT HAZIRLA
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
            
            # 8. DEEPSEEK API'Yİ ÇAĞIR
            ai_start = datetime.now()
            url = "https://api.deepseek.com/chat/completions"
            
            request_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 800,
                "temperature": 0.1
            }
            
            json_data = json.dumps(request_data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz-AI/4.0'
                }
            )
            
            print("🔄 DeepSeek API çağrılıyor...")
            response = urllib.request.urlopen(req, timeout=50)
            response_data = json.loads(response.read().decode('utf-8'))
            ai_time = (datetime.now() - ai_start).total_seconds()
            
            print(f"✅ DeepSeek yanıt aldı ({ai_time:.2f} sn)")
            
            if 'choices' in response_data and response_data['choices']:
                answer = response_data['choices'][0]['message']['content']
                
                # 9. YANIT VER
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                total_time = excel_time + ai_time
                
                result = json.dumps({
                    "success": True,
                    "answer": answer,
                    "model": "deepseek-chat",
                    "excel_data_used": analysis.get("found", False),
                    "symbol": analysis.get("name"),
                    "sheet": analysis.get("sayfa"),
                    "excel_date": excel_date,
                    "total_symbols": excel_result.get("total_symbols", 0),
                    "performance": {
                        "excel_okuma_sn": round(excel_time, 2),
                        "ai_analiz_sn": round(ai_time, 2),
                        "toplam_sn": round(total_time, 2)
                    }
                }, ensure_ascii=False)
                
                self.wfile.write(result.encode('utf-8'))
                print(f"📤 YANIT GÖNDERİLDİ! Toplam süre: {total_time:.2f} sn")
                print("="*70 + "\n")
                
            else:
                raise Exception("API geçersiz yanıt")
                
        except Exception as e:
            print(f"❌ HATA: {str(e)}")
            print("="*70 + "\n")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "success": False,
                "answer": f"❌ Sistem hatası: {str(e)[:100]}\nLütfen daha sonra tekrar deneyin.",
                "excel_data_used": False
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
    
    def create_simple_response(self, analysis, excel_result, excel_date):
        """API key yoksa basit yanıt oluştur"""
        if analysis.get("found"):
            sembol_data = analysis["data"]
            sembol_name = analysis["name"]
            
            response_lines = []
            response_lines.append(f"📊 **{sembol_name.upper()} ANALİZİ**")
            response_lines.append(f"📅 Excel Tarihi: {excel_date}")
            response_lines.append(f"📁 Sayfa: {analysis.get('sayfa')}")
            response_lines.append("")
            
            # Temel veriler
            if 'Close' in sembol_data:
                response_lines.append(f"📈 **Fiyat:** {sembol_data['Close']} TL")
            
            if 'VMA trend algo' in sembol_data:
                response_lines.append(f"📊 **VMA:** {sembol_data['VMA trend algo']}")
            
            if all(k in sembol_data for k in ['EMA_8', 'EMA_21', 'EMA_55']):
                response_lines.append(f"📉 **EMA:** 8:{sembol_data['EMA_8']} 21:{sembol_data['EMA_21']} 55:{sembol_data['EMA_55']}")
            
            if all(k in sembol_data for k in ['Pivot', 'S1', 'R1']):
                response_lines.append(f"⚖️ **Seviyeler:** P:{sembol_data['Pivot']} S1:{sembol_data['S1']} R1:{sembol_data['R1']}")
            
            if 'DURUM' in sembol_data:
                response_lines.append(f"🎯 **Durum:** {sembol_data['DURUM']}")
            
            if 'AI_YORUM' in sembol_data:
                response_lines.append(f"💡 **Yorum:** {sembol_data['AI_YORUM']}")
            
            response_lines.append("")
            response_lines.append("⚠️ *AI analizi için API key gerekli*")
            
            return "\n".join(response_lines)
        else:
            return f"❌ Sembol bulunamadı.\n\n📅 Excel Tarihi: {excel_date}\n📊 Toplam Sembol: {excel_result.get('total_symbols', 0)}\n💡 Örnek semboller: FROTO, THYAO, GMSTR, XU100"
