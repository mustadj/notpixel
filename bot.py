import requests
import json
import time
import random
import shelve
from setproctitle import setproctitle
from getimage import get
from colorama import Fore, Style, init
from datetime import datetime

# URL API
url = "https://notpx.app/api/v1"

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

# Set proctitle
setproctitle("notpixel")

# Ambil konfigurasi gambar
image = get("")

# Fungsi untuk menyimpan session (token)
def save_session(data):
    with shelve.open("session.db") as session:
        session['token'] = data.get('access_token')
        session['refresh_token'] = data.get('refresh_token')

# Fungsi untuk memuat session dari file
def load_session():
    with shelve.open("session.db") as session:
        return {
            'access_token': session.get('token', None),
            'refresh_token': session.get('refresh_token', None)
        }

# Fungsi untuk merefresh token menggunakan refresh_token
def refresh_access_token(refresh_token):
    refresh_url = f"{url}/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': 'your_client_id',  # Masukkan client_id Anda
        'client_secret': 'your_client_secret'  # Masukkan client_secret Anda
    }
    response = requests.post(refresh_url, data=data)
    if response.status_code == 200:
        new_token_data = response.json()
        save_session(new_token_data)  # Simpan token baru ke session
        return new_token_data['access_token']
    else:
        log_message("Gagal memperbarui Access Token.", Fore.RED)
        return None

# Fungsi untuk mengecek apakah token masih valid
def is_token_valid():
    session_data = load_session()
    if session_data['access_token']:
        headers = {'Authorization': f"Bearer {session_data['access_token']}"}
        response = requests.get(f"{url}/validate_token", headers=headers)
        return response.status_code == 200
    return False

# Fungsi untuk mendapatkan akses token dari sesi atau memperbarui token jika kadaluarsa
def get_access_token():
    session_data = load_session()
    if is_token_valid():
        return session_data['access_token']
    else:
        return refresh_access_token(session_data['refresh_token'])

# Tambahkan headers untuk menyerupai request dari browser sungguhan
def get_headers():
    access_token = get_access_token()
    return {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://example.com',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0'
    }

# Fungsi utama untuk melakukan proses melukis
def main():
    headers = get_headers()
    
    while True:
        try:
            # Logika melukis, klaim sumber daya, dsb.
            log_message("Proses berjalan dengan token yang valid.", Fore.GREEN)
            # Tambahkan logika tambahan sesuai keperluan
            time.sleep(5)  # Simulasi delay antar request

        except requests.exceptions.RequestException as e:
            log_message(f"Kesalahan jaringan di akun: {e}", Fore.RED)

# Fungsi untuk menampilkan timer mundur
def countdown_timer(duration):
    while duration > 0:
        mins, secs = divmod(duration, 60)
        timer = f'{int(mins):02}:{int(secs):02}'
        print(f'Timer Mundur: {timer}', end="\r")
        time.sleep(1)
        duration -= 1
    print("Countdown selesai. Melanjutkan proses...")

# Jalankan main script
main()
