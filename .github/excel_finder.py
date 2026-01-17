#!/usr/bin/env python3
"""
GitHub repository'sindeki EN SON EXCEL dosyasını otomatik bulan script
"""
import os
import re
import glob
from datetime import datetime

def find_latest_excel():
    print("🔍 En son Excel dosyası aranıyor...")
    
    # Tüm Excel dosyalarını bul
    excel_files = []
    
    for pattern in ['*.xlsm', '*.xlsx', 'BORSAANALIZ*.xlsm']:
        for file_path in glob.glob(pattern):
            if 'BORSAANALIZ' in file_path.upper():
                stat = os.stat(file_path)
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                
                excel_files.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'modified': mod_time,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024*1024), 2)
                })
    
    if not excel_files:
        print("❌ Hiç Excel dosyası bulunamadı!")
        return None
    
    # Tarihe göre sırala (en yeni en üstte)
    excel_files.sort(key=lambda x: x['modified'], reverse=True)
    
    latest = excel_files[0]
    print(f"✅ EN SON EXCEL: {latest['name']} ({latest['modified'].strftime('%d.%m.%Y %H:%M')})")
    
    return latest

if __name__ == "__main__":
    latest = find_latest_excel()
    if latest:
        print(f"📄 Bulunan: {latest['path']}")
