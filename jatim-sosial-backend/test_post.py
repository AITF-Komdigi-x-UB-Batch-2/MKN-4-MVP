import requests
import json
import os

url = "http://localhost:8000/api/v1/import-csv"
# Menggunakan 'r' di depan kutip biar aman di Windows
file_path = r"D:\Coding\MVP-Apps-Pemetaan_Kemiskinan_dan_Bantuan\datadummy_alvin_sample.csv"

try:
    # Membuka file CSV dari local storage laptopmu
    with open(file_path, 'rb') as f:
        files = {'file': f}
        
        print("Sedang mengirim file ke Docker backend...")
        response = requests.post(url, files=files)
        
        # Mengecek respon balik dari backend di Docker
        print(f"Status Code: {response.status_code}")
        print("Respon Backend:")
        print(response.json())

except FileNotFoundError:
    print(f"Error: File tidak ditemukan di jalur {file_path}. Coba cek lagi nama atau foldernya.")
except requests.exceptions.ConnectionError:
    print("Error: Gagal konek ke backend. Pastikan Docker Container kamu udah jalan dan port 8000 udah di-forward.")
