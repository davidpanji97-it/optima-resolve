import pandas as pd
import os

file_path = 'rekap_tiket_it.csv'

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    print("🔄 Mendeteksi database lama. Memulai proses migrasi...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        baris_pertama = f.readline()
        jumlah_kolom = len(baris_pertama.split(','))
    
    if jumlah_kolom < 9:
        if jumlah_kolom == 4:
            df_lama = pd.read_csv(file_path, names=['Waktu', 'ID Tiket', 'Kendala', 'Solusi'])
            df_lama['Lampiran'] = "Tidak ada lampiran"
        elif jumlah_kolom == 5:
            df_lama = pd.read_csv(file_path, names=['Waktu', 'ID Tiket', 'Kendala', 'Solusi', 'Lampiran'])
        else:
            print("❌ Format kolom tidak dikenali.")
            exit()
        
        # Menyuntikkan data default untuk menyesuaikan 9 kolom baru
        df_lama['NIP'] = "99999"
        df_lama['Nama'] = "User Historis"
        df_lama['Divisi'] = "Lainnya"
        df_lama['Telepon'] = "-"
        
        # Menyusun urutan 9 kolom agar sesuai dengan sistem V4
        df_baru = df_lama[['Waktu', 'ID Tiket', 'NIP', 'Nama', 'Divisi', 'Telepon', 'Kendala', 'Solusi', 'Lampiran']]
        
        df_baru.to_csv(file_path, index=False, header=False, encoding='utf-8')
        print("✅ Migrasi sukses! Data lama Anda berhasil diubah ke format 9 kolom tanpa ada yang hilang.")
    else:
        print("💡 Database Anda sudah dalam format 9 kolom. Tidak perlu migrasi.")
else:
    print("❌ File rekap_tiket_it.csv tidak ditemukan atau kosong.")