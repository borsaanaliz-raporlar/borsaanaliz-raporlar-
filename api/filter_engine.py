# /api/filter_engine.py - HIZLI FİLTRELEME MOTORU
from typing import Dict, List, Any, Callable
import re

class FilterEngine:
    """Hızlı filtreleme motoru"""
    
    def __init__(self):
        self.operators = {
            # Numeric operators
            ">": lambda x, y: self.to_float(x) > y,
            "<": lambda x, y: self.to_float(x) < y,
            ">=": lambda x, y: self.to_float(x) >= y,
            "<=": lambda x, y: self.to_float(x) <= y,
            "==": lambda x, y: self.to_float(x) == y,
            "!=": lambda x, y: self.to_float(x) != y,
            
            # String operators
            "contains": lambda x, y: y in str(x).upper(),
            "not_contains": lambda x, y: y not in str(x).upper(),
            "equals": lambda x, y: str(x).upper() == str(y).upper(),
            "startswith": lambda x, y: str(x).upper().startswith(str(y).upper()),
            "endswith": lambda x, y: str(x).upper().endswith(str(y).upper()),
        }
    
    def to_float(self, value) -> float:
        """Değeri float'a çevir"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # "115,7" -> 115.7
            clean = str(value).replace(',', '.').replace(' ', '')
            return float(clean)
        except:
            return 0.0
    
    def apply_filter(self, hisse_data: Dict, filter_def: Dict) -> bool:
        """Tek filtre uygula"""
        field = filter_def.get("field")
        operator = filter_def.get("operator", "==")
        value = filter_def.get("value")
        
        if field not in hisse_data:
            return False
        
        field_value = hisse_data[field]
        
        # Operator'ü bul
        if operator not in self.operators:
            print(f"⚠️ Bilinmeyen operator: {operator}")
            return False
        
        try:
            return self.operators[operator](field_value, value)
        except Exception as e:
            print(f"❌ Filtre hatası: {e}")
            return False
    
    def apply_filters(self, hisse_data: Dict, filters: List[Dict]) -> bool:
        """Tüm filtreleri uygula (AND mantığı)"""
        if not filters:
            return True
        
        for filter_def in filters:
            if not self.apply_filter(hisse_data, filter_def):
                return False
        
        return True
    
    def calculate_distance_to_bb_lower(self, hisse_data: Dict) -> float:
        """BB alt bandına uzaklık hesapla"""
        close = self.to_float(hisse_data.get("Close", 0))
        bb_lower = self.to_float(hisse_data.get("BB_LOWER", 0))
        
        if bb_lower == 0:
            return 999.0
        
        # Yüzde olarak uzaklık
        return ((close - bb_lower) / bb_lower) * 100
    
    def sort_hisseler(self, hisseler: List[Dict], sort_config: Dict) -> List[Dict]:
        """Hisseleri sırala"""
        field = sort_config.get("field", "Pearson55")
        order = sort_config.get("order", "DESC")
        
        def get_sort_value(item):
            if field == "distance_to_bb_lower":
                return self.calculate_distance_to_bb_lower(item)
            
            value = item.get(field)
            return self.to_float(value)
        
        return sorted(hisseler, 
                     key=get_sort_value, 
                     reverse=(order == "DESC"))
    
    def filter_and_sort(self, all_hisseler: Dict, 
                       filters: List[Dict], 
                       sort_config: Dict,
                       limit: int = 20) -> List[Dict]:
        """Filtrele ve sırala - ANA FONKSİYON"""
        print(f"🔍 {len(all_hisseler)} hisse filtreleniyor...")
        
        filtered = []
        
        for hisse_adi, hisse_data in all_hisseler.items():
            # Filtreleri uygula
            if self.apply_filters(hisse_data, filters):
                filtered.append({
                    "hisse": hisse_adi,
                    **hisse_data
                })
        
        print(f"✅ {len(filtered)} hisse filtreden geçti")
        
        # Sırala
        if filtered and sort_config:
            filtered = self.sort_hisseler(filtered, sort_config)
        
        # Limit uygula
        return filtered[:limit]

# Global instance
filter_engine = FilterEngine()
