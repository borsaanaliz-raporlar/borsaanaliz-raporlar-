# /api/query.py - SORGULAMA MOTORU (GÜNCELLENMİŞ)
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import re

# Import modules
from excel_processor import excel_processor
from query_parser import query_parser
from filter_engine import filter_engine

class QueryEngine:
    """Ana sorgulama motoru - GÜNCEL EXCEL"""
    
    def __init__(self):
        self.excel_data = None
        self.last_load_time = None
    
    def load_excel_data(self) -> Dict:
        """GÜNCEL Excel verilerini yükle (cache'li)"""
        current_time = datetime.now()
        
        # 5 dakikadan eskiyse yenile
        if self.excel_data is None or self.last_load_time is None or \
           (current_time - self.last_load_time).total_seconds() > 300:  # 5 dakika
            
            print("🔄 Güncel Excel yükleniyor...")
            start_time = datetime.now()
            self.excel_data = excel_processor.read_excel_data()  # Otomatik güncel bulur
            self.last_load_time = current_time
            
            load_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Excel yüklendi: {self.excel_data.get('total_symbols', 0)} sembol, {load_time:.2f}s")
            print(f"📅 Excel tarihi: {self.excel_data.get('excel_date', 'bilinmiyor')}")
        
        return self.excel_data
    
    def execute_query(self, query: str, query_type: str = "natural") -> Dict:
        """Sorguyu çalıştır"""
        start_time = datetime.now()
        
        try:
            # 1. Sorguyu parse et
            if query_type == "natural":
                parsed = query_parser.parse_natural_language(query)
            else:  # advanced
                try:
                    query_json = json.loads(query) if isinstance(query, str) else query
                    parsed = query_parser.parse_advanced_query(query_json)
                except:
                    parsed = query_parser.parse_natural_language(query)
            
            if not parsed.get("parsed_successfully"):
                return {
                    "success": False,
                    "error": "Sorgu anlaşılamadı",
                    "parsed_query": parsed,
                    "suggestions": [
                        "Pearson55 > 0.85",
                        "VMA pozitif",
                        "Durum GÜÇLÜ POZİTİF",
                        "BB alt bandına yakın hisseler"
                    ]
                }
            
            # 2. GÜNCEL Excel verilerini yükle
            excel_data = self.load_excel_data()
            excel_date = excel_data.get("excel_date", "bilinmiyor")
            
            # 3. Tüm sembolleri birleştir (3 sayfa)
            all_symbols = self.combine_all_symbols(excel_data)
            
            # 4. Filtrele ve sırala
            results = filter_engine.filter_and_sort(
                all_hisseler=all_symbols,
                filters=parsed["filters"],
                sort_config=parsed["sorting"],
                limit=parsed["pagination"]["limit"]
            )
            
            # 5. Sayfa bilgisi ekle
            for result in results:
                if "source_sheet" in result:
                    result["sayfa"] = result["source_sheet"]
            
            # 6. İstatistikleri hesapla
            stats = self.calculate_stats(results, parsed["filters"])
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "query": query,
                "parsed_query": parsed,
                "results": results,
                "stats": stats,
                "excel_info": {
                    "excel_date": excel_date,
                    "total_symbols": excel_data.get("total_symbols", 0),
                    "sheets_loaded": list(excel_data.get("sheets", {}).keys()),
                    "load_time": excel_data.get("load_time", 0)
                },
                "execution_time": execution_time
            }
            
        except Exception as e:
            print(f"❌ Sorgu çalıştırma hatası: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def combine_all_symbols(self, excel_data: Dict) -> Dict:
        """3 sayfanın tüm sembollerini birleştir"""
        all_symbols = {}
        
        # 1. Sinyaller sayfası
        if "Sinyaller" in excel_data.get("sheets", {}):
            sinyaller = excel_data["sheets"]["Sinyaller"]["hisseler"]
            for hisse_adi, hisse_veriler in sinyaller.items():
                all_symbols[hisse_adi] = {
                    **hisse_veriler,
                    "source_sheet": "Sinyaller",
                    "symbol_type": "hisse"
                }
        
        # 2. ENDEKSLER sayfası
        if "ENDEKSLER" in excel_data.get("sheets", {}):
            endeksler = excel_data["sheets"]["ENDEKSLER"]["semboller"]
            for sembol_adi, sembol_veriler in endeksler.items():
                all_symbols[sembol_adi] = {
                    **sembol_veriler,
                    "source_sheet": "ENDEKSLER",
                    "symbol_type": "endeks"
                }
        
        # 3. FON_EMTIA_COIN_DOVIZ sayfası
        if "FON_EMTIA_COIN_DOVIZ" in excel_data.get("sheets", {}):
            fonlar = excel_data["sheets"]["FON_EMTIA_COIN_DOVIZ"]["semboller"]
            for sembol_adi, sembol_veriler in fonlar.items():
                all_symbols[sembol_adi] = {
                    **sembol_veriler,
                    "source_sheet": "FON_EMTIA_COIN_DOVIZ",
                    "symbol_type": "fon_emtia"
                }
        
        print(f"📊 3 sayfa birleştirildi: {len(all_symbols)} sembol")
        return all_symbols
    
    def calculate_stats(self, results: List[Dict], filters: List[Dict]) -> Dict:
        """İstatistikleri hesapla"""
        if not results:
            return {
                "count": 0,
                "message": "Filtrelere uygun sembol bulunamadı"
            }
        
        stats = {
            "count": len(results),
            "by_sheet": {},
            "by_type": {},
            "field_stats": {}
        }
        
        # Sayfa ve tip dağılımı
        for result in results:
            sheet = result.get("source_sheet", "bilinmiyor")
            sym_type = result.get("symbol_type", "bilinmiyor")
            
            stats["by_sheet"][sheet] = stats["by_sheet"].get(sheet, 0) + 1
            stats["by_type"][sym_type] = stats["by_type"].get(sym_type, 0) + 1
        
        # Alan istatistikleri (sadece Sinyaller için)
        sinyaller_results = [r for r in results if r.get("source_sheet") == "Sinyaller"]
        if sinyaller_results:
            # Pearson ortalaması
            pearson_values = []
            close_values = []
            
            for result in sinyaller_results:
                if "Pearson55" in result:
                    try:
                        pearson_values.append(float(result["Pearson55"]))
                    except:
                        pass
                
                if "Close" in result:
                    try:
                        close_values.append(float(result["Close"]))
                    except:
                        pass
            
            if pearson_values:
                stats["field_stats"]["avg_pearson55"] = round(sum(pearson_values) / len(pearson_values), 3)
                stats["field_stats"]["min_pearson55"] = round(min(pearson_values), 3)
                stats["field_stats"]["max_pearson55"] = round(max(pearson_values), 3)
            
            if close_values:
                stats["field_stats"]["avg_close"] = round(sum(close_values) / len(close_values), 2)
                stats["field_stats"]["min_close"] = round(min(close_values), 2)
                stats["field_stats"]["max_close"] = round(max(close_values), 2)
        
        return stats
    
    def format_results(self, result: Dict) -> str:
        """Sonuçları formatla"""
        if not result.get("success"):
            error = result.get("error", "Bilinmeyen hata")
            return f"❌ **Sorgu Hatası:** {error}"
        
        results = result.get("results", [])
        stats = result.get("stats", {})
        excel_info = result.get("excel_info", {})
        parsed = result.get("parsed_query", {})
        
        if not results:
            return "🔍 **Sonuç bulunamadı.**\n\nFiltrelerinizi gözden geçirin veya daha geniş kriterler deneyin."
        
        response_lines = []
        
        # Başlık
        response_lines.append(f"📊 **SORGULAMA SONUÇLARI**")
        response_lines.append("=" * 60)
        
        # Excel bilgisi
        response_lines.append(f"📅 **Excel Tarihi:** {excel_info.get('excel_date', 'bilinmiyor')}")
        response_lines.append(f"📈 **Toplam Sembol:** {excel_info.get('total_symbols', 0)} (3 sayfa)")
        response_lines.append(f"⏱️ **Çalışma Süresi:** {result.get('execution_time', 0):.2f}s")
        response_lines.append("")
        
        # İstatistikler
        response_lines.append(f"✅ **Bulunan Sembol:** {stats.get('count', 0)}")
        
        if "by_sheet" in stats:
            response_lines.append("📋 **Sayfa Dağılımı:**")
            for sheet, count in stats["by_sheet"].items():
                response_lines.append(f"   • {sheet}: {count}")
        
        if "field_stats" in stats and stats["field_stats"]:
            response_lines.append("📊 **İstatistikler (Sinyaller):**")
            for field, value in stats["field_stats"].items():
                response_lines.append(f"   • {field}: {value}")
        
        response_lines.append("")
        
        # Hisse listesi (ilk 10)
        response_lines.append("🏆 **EN İYİ 10 SONUÇ:**")
        response_lines.append("")
        
        for i, sembol in enumerate(results[:10], 1):
            sembol_adi = sembol.get("hisse", sembol.get("sembol", "N/A"))
            sembol_type = sembol.get("symbol_type", "N/A")
            sayfa = sembol.get("sayfa", sembol.get("source_sheet", "N/A"))
            
            # Emoji
            if sembol_type == "hisse":
                emoji = "📈"
            elif sembol_type == "endeks":
                emoji = "📊"
            elif sembol_type == "fon_emtia":
                emoji = "💰"
            else:
                emoji = "📌"
            
            response_lines.append(f"{i}. **{sembol_adi}** {emoji} ({sayfa})")
            
            # Temel bilgiler
            if "Close" in sembol:
                response_lines.append(f"   • Fiyat: **{sembol['Close']} TL**")
            
            if "Pearson55" in sembol:
                pearson = sembol["Pearson55"]
                if isinstance(pearson, (int, float)):
                    if pearson >= 0.85:
                        pe_emoji = "🟢"
                    elif pearson >= 0.70:
                        pe_emoji = "🟡"
                    else:
                        pe_emoji = "🔴"
                    response_lines.append(f"   • Pearson55: {pe_emoji} **{pearson}**")
                else:
                    response_lines.append(f"   • Pearson55: {pearson}")
            
            if "VMA trend algo" in sembol:
                vma = str(sembol["VMA trend algo"])
                if "POZİTİF" in vma.upper():
                    vma_emoji = "📈"
                elif "NEGATİF" in vma.upper():
                    vma_emoji = "📉"
                else:
                    vma_emoji = "↔️"
                response_lines.append(f"   • VMA: {vma_emoji} {vma}")
            
            if "DURUM" in sembol:
                durum = str(sembol["DURUM"])
                if "GÜÇLÜ POZİTİF" in durum.upper():
                    durum_emoji = "🟢"
                elif "POZİTİF" in durum.upper():
                    durum_emoji = "🟢"
                elif "GÜÇLÜ NEGATİF" in durum.upper():
                    durum_emoji = "🔴"
                elif "NEGATİF" in durum.upper():
                    durum_emoji = "🔴"
                elif "NÖTR" in durum.upper():
                    durum_emoji = "🟡"
                else:
                    durum_emoji = "⚪"
                response_lines.append(f"   • Durum: {durum_emoji} {durum}")
            
            # Bollinger Bandı uzaklığı
            if "Close" in sembol and "BB_LOWER" in sembol:
                try:
                    close = float(sembol["Close"])
                    bb_lower = float(sembol["BB_LOWER"])
                    if bb_lower > 0:
                        distance = ((close - bb_lower) / bb_lower) * 100
                        response_lines.append(f"   • BB Alt Bandı: %{distance:.1f} uzak")
                except:
                    pass
            
            response_lines.append("")
        
        if len(results) > 10:
            response_lines.append(f"⏩ **... ve {len(results) - 10} sembol daha**")
            response_lines.append("")
        
        # Filtre bilgisi
        response_lines.append("🔍 **Uygulanan Filtreler:**")
        filters = parsed.get("filters", [])
        if filters:
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "")
                value = f.get("value", "")
                response_lines.append(f"• {field} {operator} {value}")
        else:
            response_lines.append("• Tüm semboller")
        
        # Sıralama bilgisi
        sorting = parsed.get("sorting", {})
        if sorting:
            field = sorting.get("field", "")
            order = "azalan" if sorting.get("order") == "DESC" else "artan"
            response_lines.append(f"• Sıralama: {field} ({order})")
        
        response_lines.append("")
        response_lines.append("💡 **Örnek sorgular:**")
        response_lines.append("• `Pearson55 >= 0.85`")
        response_lines.append("• `VMA POZİTİF ve Durum GÜÇLÜ POZİTİF`")
        response_lines.append("• `BB alt bandına en yakın 10 hisse`")
        response_lines.append("• `FROTO, THYAO, GARAN analizi`")
        
        return "\n".join(response_lines)

# Global engine instance
query_engine = QueryEngine()

class QueryHandler(BaseHTTPRequestHandler):
    """HTTP Handler for query engine"""
    
    def do_GET(self):
        """Sistem durumu"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            "status": "online",
            "service": "BorsaAnaliz Query Engine",
            "version": "2.0",
            "guncel_ozellikler": {
                "excel_okuma": "Güncel Excel otomatik bulma",
                "sayfalar": "3 sayfa tam okuma (Sinyaller, ENDEKSLER, FON_EMTIA)",
                "filtreler": "Pearson, VMA, Durum, BB, EMA filtreleri",
                "siralama": "Çoklu sıralama seçenekleri",
                "cache": "5 dakika cache, 1 saat Excel cache"
            },
            "endpoints": {
                "GET /api/query": "Sistem durumu (bu sayfa)",
                "POST /api/query": "Doğal dil sorgulama",
                "POST /api/query?type=advanced": "Advanced JSON sorgulama"
            },
            "ornek_sorgular": [
                {"query": "Pearson55 > 0.85", "aciklama": "Yüksek korelasyonlu hisseler"},
                {"query": "VMA POZİTİF ve Durum GÜÇLÜ POZİTİF", "aciklama": "Güçlü trend"},
                {"query": "BB alt bandına en yakın 5 hisse", "aciklama": "Destek seviyesi"},
                {"query": "EMA_8 > EMA_21 > EMA_55", "aciklama": "Güçlü yükseliş trendi"}
            ]
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def do_POST(self):
        """Sorgu işleme"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            query = data.get('query', '')
            query_type = data.get('type', 'natural')
            
            if not query:
                self.send_error(400, "Query is required")
                return
            
            print(f"\n{'='*60}")
            print(f"🚀 YENİ SORGULA: {query[:100]}...")
            print('='*60)
            
            # Sorguyu çalıştır
            result = query_engine.execute_query(query, query_type)
            
            # Formatlı yanıt oluştur
            formatted_response = query_engine.format_results(result)
            
            # JSON yanıtı hazırla
            response_data = {
                "success": result.get("success", False),
                "query": query,
                "response": formatted_response,
                "stats": result.get("stats", {}),
                "excel_info": result.get("excel_info", {}),
                "execution_time": result.get("execution_time", 0),
                "result_count": len(result.get("results", [])),
                "engine_version": "2.0",
                "timestamp": datetime.now().isoformat()
            }
            
            # Raw results için (debug)
            if data.get("debug", False):
                response_data["raw_results"] = result.get("results", [])[:5]  # İlk 5
                response_data["parsed_query"] = result.get("parsed_query", {})
            
            # Yanıtı gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
            
            print(f"✅ Sorgu tamamlandı: {response_data['result_count']} sonuç, {response_data['execution_time']:.2f}s")
            print('='*60 + '\n')
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"❌ Handler hatası: {e}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            error_response = {
                "success": False,
                "error": str(e),
                "query": query if 'query' in locals() else ""
            }
            
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

# Vercel için handler
handler = QueryHandler
