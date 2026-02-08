# /api/excel_processor.py - HIZLI EXCEL OKUYUCU
import urllib.request
import tempfile
import re
from datetime import datetime
from openpyxl import load_workbook
import json
import os
from typing import Dict, List, Any
import hashlib
import pickle

class ExcelProcessor:
    """Hızlı Excel okuyucu ve cache sistemi"""
    
    def __init__(self):
        self.cache_dir = "/tmp/borsa_cache"
        self.cache_duration = 3600  # 1 saat cache
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, excel_url: str) -> str:
        """Cache key oluştur"""
        url_hash = hashlib.md5(excel_url.encode()).hexdigest()
        return f"{self.cache_dir}/excel_data_{url_hash}.pkl"
    
    def is_cache_valid(self, cache_file: str) -> bool:
        """Cache geçerli mi?"""
        if not os.path.exists(cache_file):
            return False
        
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
        return file_age < self.cache_duration
    
    def load_from_cache(self, cache_file: str) -> Dict:
        """Cache'den yükle"""
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    
    def save_to_cache(self, cache_file: str, data: Dict):
        """Cache'e kaydet"""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except:
            pass
    
    def download_excel(self, excel_url: str) -> bytes:
        """Excel'i indir"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(excel_url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    
    def extract_headers(self, ws, max_cols=100) -> List[str]:
        """Başlıkları temizle"""
        headers = []
        for col in range(1, max_cols + 1):
            cell_val = ws.cell(row=1, column=col).value
            if not cell_val:
                break
            
            # Temizle: "Hisse (06-02-2026)" -> "Hisse"
            header = str(cell_val).split('(')[0].strip()
            header = re.sub(r'\s+', ' ', header)
            headers.append(header)
        
        return headers
    
    def parse_cell_value(self, value):
        """Hücre değerini parse et"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")
        elif isinstance(value, (int, float)):
            return float(value) if '.' in str(value) else int(value)
        else:
            return str(value).strip()
    
    def read_excel_data(self, excel_url: str) -> Dict:
        """Excel'i oku ve işle - ANA FONKSİYON"""
        print(f"📊 Excel işleniyor: {excel_url}")
        
        # 1. Cache kontrolü
        cache_file = self.get_cache_key(excel_url)
        if self.is_cache_valid(cache_file):
            print("✅ Cache'den yükleniyor...")
            cached_data = self.load_from_cache(cache_file)
            if cached_data:
                return cached_data
        
        start_time = datetime.now()
        
        try:
            # 2. Excel'i indir
            print("⬇️  Excel indiriliyor...")
            excel_content = self.download_excel(excel_url)
            
            # 3. Geçici dosyaya yaz
            with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp:
                tmp.write(excel_content)
                tmp_path = tmp.name
            
            # 4. openpyxl ile aç (read_only modunda)
            print("📖 Excel açılıyor...")
            wb = load_workbook(tmp_path, data_only=True, read_only=True)
            
            # 5. Sadece Sinyaller sayfasını oku
            if "Sinyaller" not in wb.sheetnames:
                raise Exception("Sinyaller sayfası bulunamadı")
            
            ws = wb["Sinyaller"]
            
            # 6. Başlıkları oku
            print("🔠 Başlıklar okunuyor...")
            headers = self.extract_headers(ws)
            print(f"✅ {len(headers)} başlık bulundu")
            
            # 7. TÜM hisseleri oku (630+)
            hisse_data = {}
            row_count = 0
            
            print("📈 Hisse verileri okunuyor...")
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                
                hisse_adi = str(row[0]).strip()
                if not hisse_adi:
                    continue
                
                # Hisse verilerini dict'e çevir
                hisse_dict = {}
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        cell_value = self.parse_cell_value(row[col_idx])
                        if cell_value is not None:
                            hisse_dict[header] = cell_value
                
                hisse_data[hisse_adi] = hisse_dict
                row_count += 1
                
                # Progress göstergesi
                if row_count % 100 == 0:
                    print(f"   ...{row_count} hisse okundu")
            
            # 8. Temizlik
            wb.close()
            os.unlink(tmp_path)
            
            # 9. Metadata ekle
            result = {
                "excel_url": excel_url,
                "headers": headers,
                "hisseler": hisse_data,
                "total_hisses": len(hisse_data),
                "load_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Excel işlendi: {len(hisse_data)} hisse, {result['load_time']:.2f}s")
            
            # 10. Cache'e kaydet
            self.save_to_cache(cache_file, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Excel okuma hatası: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_available_fields(self, excel_data: Dict) -> List[str]:
        """Mevcut teknik alanları listele"""
        if not excel_data.get("hisseler"):
            return []
        
        # İlk hisseden alanları al
        first_hisse = next(iter(excel_data["hisseler"].values()), {})
        return list(first_hisse.keys())
    
    def get_field_stats(self, excel_data: Dict, field: str) -> Dict:
        """Alan istatistiklerini hesapla"""
        values = []
        
        for hisse_adi, hisse_dict in excel_data["hisseler"].items():
            value = hisse_dict.get(field)
            if value is not None:
                try:
                    if isinstance(value, (int, float)):
                        values.append(float(value))
                except:
                    pass
        
        if not values:
            return {"available": False}
        
        return {
            "available": True,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }

# Global instance
excel_processor = ExcelProcessor()
