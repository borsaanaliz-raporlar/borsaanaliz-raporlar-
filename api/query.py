# /api/query.py - ANA SORGULAMA MOTORU
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Import modules
from excel_processor import excel_processor
from query_parser import query_parser
from filter_engine import filter_engine

class QueryEngine:
    """Ana sorgulama motoru"""
    
    def __init__(self):
        self.excel_data = None
        self.excel_url = "https://borsaanaliz-raporlar.vercel.app/raporlar/BORSAANALIZ_V11_TAM_06022026.xlsm"
    
    def load_excel_data(self) -> Dict:
        """Excel verilerini yükle (cache'li)"""
        if self.excel_data is None:
            print("📥 Excel verileri yükleniyor...")
            self.excel_data = excel_processor.read_excel_data(self.excel_url)
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
                    "parsed_query": parsed
                }
            
            # 2. Excel verilerini yükle
            excel_data = self.load_excel_data()
            all_hisseler = excel_data.get("hisseler", {})
            
            # 3. Filtrele ve sırala
            results = filter_engine.filter_and_sort(
                all_hisseler=all_hisseler,
                filters=parsed["filters"],
                sort_config=parsed["sorting"],
                limit=parsed["pagination"]["limit"]
            )
            
            # 4. İstatistikleri hesapla
            stats = self.calculate_stats(results, parsed["filters"])
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "query": query,
                "parsed_query": parsed,
                "results": results,
                "stats": stats,
                "execution_time": execution_time,
                "excel_info": {
                    "total_hisses": len(all_hisseler),
                    "excel_url": self.excel_url,
                    "load_time": excel_data.get("load_time", 0)
                }
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
    
    def calculate_stats(self, results: List[Dict], filters: List[Dict]) -> Dict:
        """İstatistikleri hesapla"""
        if not results:
            return {}
        
        stats = {
            "count": len(results),
            "avg_pearson55": 0,
            "avg_close": 0,
            "strong_positive": 0,
            "neutral": 0,
            "strong_negative": 0,
        }
        
        total_pearson = 0
        total_close = 0
        
        for result in results:
            # Pearson ortalaması
            pearson = result.get("Pearson55", 0)
            if isinstance(pearson, (int, float)):
                total_pearson += float(pearson)
            
            # Close ortalaması
            close = result.get("Close", 0)
            if isinstance(close, (int, float)):
                total_close += float(close)
            
            # Durum sayıları
            durum = str(result.get("DURUM", "")).upper()
            if "GÜÇLÜ POZİTİF" in durum:
                stats["strong_positive"] += 1
            elif "NÖTR" in durum:
                stats["neutral"] += 1
            elif "GÜÇLÜ NEGATİF" in durum:
                stats["strong_negative"] += 1
        
        if stats["count"] > 0:
            stats["avg_pearson55"] = round(total_pearson / stats["count"], 3)
            stats["avg_close"] = round(total_close / stats["count"], 2)
        
        return stats
    
    def format_results(self, result: Dict) -> str:
        """Sonuçları formatla"""
        if not result.get("success"):
            error = result.get("error", "Bilinmeyen hata")
            return f"❌ **Sorgu Hatası:** {error}"
        
        results = result.get("results", [])
        stats = result.get("stats", {})
        parsed = result.get("parsed_query", {})
        
        if not results:
            return "🔍 **Sonuç bulunamadı.**\n\nFiltrelerinizi gözden geçirin veya daha geniş kriterler deneyin."
        
        response_lines = []
        
        # Başlık
        response_lines.append(f"📊 **SORGULAMA SONUÇLARI**")
        response_lines.append("=" * 50)
        
        # İstatistikler
        response_lines.append(f"• **Bulunan Hisse:** {stats.get('count', 0)}")
        response_lines.append(f"• **Ortalama Pearson55:** {stats.get('avg_pearson55', 0)}")
        response_lines.append(f"• **Ortalama Fiyat:** {stats.get('avg_close', 0)} TL")
        response_lines.append(f"• **Güçlü Pozitif:** {stats.get('strong_positive', 0)}")
        response_lines.append(f"• **Nötr:** {stats.get('neutral', 0)}")
        response_lines.append(f"• **Güçlü Negatif:** {stats.get('strong_negative', 0)}")
        response_lines.append(f"• **Çalışma Süresi:** {result.get('execution_time', 0):.2f}s")
        response_lines.append("")
        
        # Hisse listesi (ilk 10)
        response_lines.append("🏆 **EN İYİ 10 HİSSE:**")
        response_lines.append("")
        
        for i, hisse in enumerate(results[:10], 1):
            hisse_adi = hisse.get("hisse", "N/A")
            close = hisse.get("Close", "N/A")
            pearson = hisse.get("Pearson55", "N/A")
            vma = hisse.get("VMA trend algo", "N/A")
            durum = hisse.get("DURUM", "N/A")
            
            # Durum emojisi
            durum_upper = str(durum).upper()
            if "GÜÇLÜ POZİTİF" in durum_upper:
                emoji = "🟢"
            elif "POZİTİF" in durum_upper:
                emoji = "🟢"
            elif "GÜÇLÜ NEGATİF" in durum_upper:
                emoji = "🔴"
            elif "NEGATİF" in durum_upper:
                emoji = "🔴"
            elif "NÖTR" in durum_upper:
                emoji = "🟡"
            else:
                emoji = "⚪"
            
            response_lines.append(f"{i}. **{hisse_adi}** {emoji}")
            response_lines.append(f"   • Fiyat: **{close} TL**")
            response_lines.append(f"   • Pearson55: **{pearson}**")
            response_lines.append(f"   • VMA: {vma}")
            response_lines.append(f"   • Durum: {durum}")
            
            # Bollinger alt bandına uzaklık
            if "BB_LOWER" in hisse:
                bb_lower = hisse.get("BB_LOWER", 0)
                if isinstance(close, (int, float)) and isinstance(bb_lower, (int, float)) and bb_lower > 0:
                    distance = ((close - bb_lower) / bb_lower) * 100
                    response_lines.append(f"   • BB Alt Bandı: %{distance:.1f} uzak")
            
            response_lines.append("")
        
        if len(results) > 10:
            response_lines.append(f"⏩ **... ve {len(results) - 10} hisse daha**")
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
            response_lines.append("• Tüm hisseler")
        
        # Sıralama bilgisi
        sorting = parsed.get("sorting", {})
        if sorting:
            field = sorting.get("field", "")
            order = "azalan" if sorting.get("order") == "DESC" else "artan"
            response_lines.append(f"• Sıralama: {field} ({order})")
        
        response_lines.append("")
        response_lines.append("💡 **Örnek sorgular:**")
        response_lines.append("• `Pearson55 >= 0.85 ve VMA POZİTİF`")
        response_lines.append("• `Regression kanalı pozitif olanlar`")
        response_lines.append("• `BB alt bandına en yakın 10 hisse`")
        
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
            "version": "1.0-alpha",
            "endpoints": {
                "POST /api/query": "Doğal dil sorgulama",
                "POST /api/query/advanced": "Advanced JSON sorgulama"
            },
            "capabilities": [
                "Pearson55/144/233 filtreleme",
                "VMA trend analizi",
                "Regression kanalı filtreleme",
                "Bollinger Bandı analizi",
                "EMA trend analizi",
                "Doğal Türkçe sorgu"
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
                "execution_time": result.get("execution_time", 0),
                "result_count": len(result.get("results", [])),
                "engine_version": "1.0-alpha",
                "timestamp": datetime.now().isoformat()
            }
            
            # Raw results için (debug)
            if data.get("debug", False):
                response_data["raw_results"] = result.get("results", [])
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
