#!/usr/bin/env python3
"""
EN SON EXCEL DOSYASINI BULUCU - raporlar/ klasörüne göre optimize edildi
"""
import os
import glob
from datetime import datetime

def find_latest_excel():
    print("🔍 En son Excel dosyası aranıyor...")
    
    excel_files = []
    
    # ÖNCELİKLE raporlar/ klasörüne bak
    for pattern in ['raporlar/*.xlsm', 'raporlar/*.xlsx', 'raporlar/**/*.xlsm', 'raporlar/**/*.xlsx']:
        for file_path in glob.glob(pattern, recursive=True):
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
                print(f"  📄 Bulundu: {os.path.basename(file_path)} ({mod_time.strftime('%d.%m.%Y %H:%M')})")
    
    # Eğer raporlar/ klasöründe yoksa tüm repoda ara
    if not excel_files:
        print("⚠️ raporlar/ klasöründe bulunamadı, tüm repoda aranıyor...")
        for pattern in ['*.xlsm', '*.xlsx', '**/*.xlsm', '**/*.xlsx']:
            for file_path in glob.glob(pattern, recursive=True):
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
    
    # En yeniye göre sırala
    excel_files.sort(key=lambda x: x['modified'], reverse=True)
    latest = excel_files[0]
    
    print(f"\n✅ EN SON EXCEL:")
    print(f"   📁 Dosya: {latest['name']}")
    print(f"   📂 Konum: {latest['path']}")
    print(f"   🕐 Tarih: {latest['modified'].strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"   💾 Boyut: {latest['size_mb']} MB")
    
    return latest

if __name__ == "__main__":
    latest = find_latest_excel()
    if latest:
        print(f"\n📊 Tam yol: {os.path.abspath(latest['path'])}")
