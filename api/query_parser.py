# /api/query_parser.py - TÜRKÇE SORGU ÇÖZÜCÜ
import re
from typing import Dict, List, Any, Tuple
import json

class TurkishQueryParser:
    """Türkçe doğal dil sorgu parser"""
    
    def __init__(self):
        self.field_mappings = {
            # Pearson
            'pearson': 'Pearson55',
            'pearson55': 'Pearson55',
            'pearson 55': 'Pearson55',
            'pearson144': 'Pearson144',
            'pearson233': 'Pearson233',
            
            # VMA
            'vma': 'VMA trend algo',
            'vma trend': 'VMA trend algo',
            'volume moving average': 'VMA trend algo',
            
            # Regression
            'regression': 'Regression_55',
            'regression55': 'Regression_55',
            'regression 55': 'Regression_55',
            'regresyon': 'Regression_55',
            
            # EMA
            'ema8': 'EMA_8',
            'ema21': 'EMA_21',
            'ema55': 'EMA_55',
            'ema144': 'EMA_144',
            'ema233': 'EMA_233',
            
            # Bollinger
            'bb': 'BB_LOWER',
            'bollinger': 'BB_LOWER',
            'bollinger band': 'BB_LOWER',
            
            # Fiyat
            'fiyat': 'Close',
            'close': 'Close',
            'açılış': 'Open',
            'yüksek': 'High',
            'düşük': 'Low',
            'hacim': 'Hacim',
            
            # Durum
            'durum': 'DURUM',
            'status': 'DURUM',
        }
        
        self.operator_mappings = {
            'büyük': '>',
            'küçük': '<',
            'büyük eşit': '>=',
            'küçük eşit': '<=',
            'eşit': '==',
            'denk': '==',
            'pozitif': 'contains',
            'negatif': 'contains',
            'içerir': 'contains',
            'içermez': 'not_contains',
        }
        
        self.logical_operators = {
            've': 'AND',
            'ile': 'AND',
            'veya': 'OR',
            'ya da': 'OR',
            'değil': 'NOT',
        }
    
    def normalize_query(self, query: str) -> str:
        """Sorguyu normalize et"""
        query = query.lower().strip()
        
        # Yazım düzeltmeleri
        corrections = {
            'nassıl': 'nasıl',
            'nasil': 'nasıl',
            'pearsın': 'pearson',
            'regresyon': 'regression',
            'bollinger bandı': 'bollinger band',
            'bollinger bant': 'bollinger band',
        }
        
        for wrong, correct in corrections.items():
            query = query.replace(wrong, correct)
        
        return query
    
    def extract_comparison(self, text: str) -> Tuple[str, str, Any]:
        """Karşılaştırma ifadesini çıkar"""
        patterns = [
            # "pearson >= 0.85"
            (r'(\w+)\s*(>=|>|<=|<|==)\s*([\d\.]+)', 1, 2, 3),
            # "pearson 0.85'den büyük"
            (r'(\w+)\s+([\d\.]+)\s*(den|dan)\s+(büyük|küçük)', 1, 4, 2),
            # "pearson büyük 0.85"
            (r'(\w+)\s+(büyük|küçük)\s+([\d\.]+)', 1, 2, 3),
        ]
        
        for pattern, field_idx, op_idx, value_idx in patterns:
            match = re.search(pattern, text)
            if match:
                field = match.group(field_idx)
                operator = match.group(op_idx)
                value = match.group(value_idx)
                
                # Operator mapping
                if operator in self.operator_mappings:
                    operator = self.operator_mappings[operator]
                
                # Value conversion
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass
                
                return field, operator, value
        
        return None, None, None
    
    def parse_natural_language(self, query: str) -> Dict:
        """Doğal dil sorgusunu parse et"""
        query = self.normalize_query(query)
        print(f"🔍 Sorgu parse ediliyor: {query}")
        
        filters = []
        sorting = {}
        limit = 20
        
        # 1. PEARSON FİLTRELERİ
        if 'pearson' in query:
            if '>=' in query or '≥' in query:
                match = re.search(r'pearson\s*(?:>=|≥)\s*([\d\.]+)', query)
                if match:
                    filters.append({
                        "field": "Pearson55",
                        "operator": ">=",
                        "value": float(match.group(1)),
                        "type": "numeric"
                    })
            elif '>' in query:
                match = re.search(r'pearson\s*>\s*([\d\.]+)', query)
                if match:
                    filters.append({
                        "field": "Pearson55",
                        "operator": ">",
                        "value": float(match.group(1)),
                        "type": "numeric"
                    })
            elif 'pearson' in query and 'yüksek' in query:
                sorting = {"field": "Pearson55", "order": "DESC"}
        
        # 2. VMA FİLTRELERİ
        if 'vma' in query:
            if 'pozitif' in query:
                filters.append({
                    "field": "VMA trend algo",
                    "operator": "contains",
                    "value": "POZİTİF",
                    "type": "string"
                })
            elif 'negatif' in query:
                filters.append({
                    "field": "VMA trend algo",
                    "operator": "contains",
                    "value": "NEGATİF",
                    "type": "string"
                })
        
        # 3. REGRESSION KANALI FİLTRELERİ
        if 'regression' in query or 'regresyon' in query:
            periods = []
            for period in ['55', '144', '233']:
                if period in query:
                    periods.append(period)
            
            if not periods:  # Period belirtilmemişse, tümü
                periods = ['55', '144', '233']
            
            for period in periods:
                if 'pozitif' in query:
                    filters.append({
                        "field": f"Regression_{period}",
                        "operator": "==",
                        "value": "POZİTİF",
                        "type": "string"
                    })
        
        # 4. BOLLINGER BANDI YAKINLIĞI
        if 'bb' in query or 'bollinger' in query:
            if 'alt' in query or 'lower' in query:
                if 'yakın' in query or 'en yakın' in query:
                    sorting = {"field": "distance_to_bb_lower", "order": "ASC"}
        
        # 5. DURUM FİLTRELERİ
        durum_terms = {
            'güçlü pozitif': 'GÜÇLÜ POZİTİF',
            'pozitif': 'POZİTİF',
            'nötr': 'NÖTR',
            'negatif': 'NEGATİF',
            'güçlü negatif': 'GÜÇLÜ NEGATİF'
        }
        
        for term, durum_value in durum_terms.items():
            if term in query:
                filters.append({
                    "field": "DURUM",
                    "operator": "==",
                    "value": durum_value,
                    "type": "string"
                })
        
        # 6. LİMİT BELİRLEME
        if 'ilk' in query:
            match = re.search(r'ilk\s+(\d+)', query)
            if match:
                limit = int(match.group(1))
        
        return {
            "original_query": query,
            "filters": filters,
            "sorting": sorting if sorting else {"field": "Pearson55", "order": "DESC"},
            "pagination": {"limit": limit, "offset": 0},
            "parsed_successfully": len(filters) > 0
        }
    
    def parse_advanced_query(self, query_json: Dict) -> Dict:
        """Advanced JSON sorgusunu parse et"""
        return {
            "original_query": query_json,
            "filters": query_json.get("filters", []),
            "sorting": query_json.get("sorting", {}),
            "pagination": query_json.get("pagination", {"limit": 20, "offset": 0}),
            "parsed_successfully": True
        }

# Global instance
query_parser = TurkishQueryParser()
