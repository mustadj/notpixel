import requests
import json
import time
import random
from setproctitle import setproctitle
from convert import get
from colorama import Fore, Style, init
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

url = "https://notpx.app/api/v1"

# WAKTU TUNGGU
WAIT = 180 * 3
DELAY = 1

# DIMENSI GAMBAR
WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

setproctitle("notpixel")

# Ambil konfigurasi gambar
image = get("")

# Definisikan warna untuk representasi pixel
c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

# Fungsi untuk mencatat pesan dengan timestamp
def log_message(message, color=Style.RESET_ALL):
    print(f"{color}{message}{Style.RESET_ALL}")

# Fungsi untuk menginisialisasi session requests dengan logika retry
def get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=0.3,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Buat session dengan logika retry
session = get_session_with_retries()

# Fungsi untuk memuat akun dari data.txt
def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [line.strip() for line in file if line.strip()]
    return accounts

# Fungsi untuk mendapatkan token baru (sesuai format yang diharapkan oleh API)
def request_new_token(account):
    log_message(f"Meminta token baru untuk akun {account}...", Fore.YELLOW)
    try:
        # Ganti dengan endpoint yang sesuai untuk mendapatkan token baru
        # Misalnya, pastikan ini adalah endpoint login yang benar
        response = session.post(f"{url}/login", data=json.dumps({"userid": account}), headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code == 200:
            new_token = response.json().get('token')
            if new_token:
                log_message(f"Berhasil login, token diterima untuk akun {account}.", Fore.GREEN)
                return new_token
            else:
                log_message(f"Tidak ada token dalam respons login akun {account}.", Fore.RED)
                return None
        elif response.status_code == 404:
            log_message(f"Kesalahan 404: Endpoint tidak ditemukan untuk akun {account}.", Fore.RED)
            return None
        else:
            log_message(f"Gagal mendapatkan token baru: {response.status_code} untuk akun {account}.", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat meminta token baru untuk akun {account}: {e}", Fore.RED)
        return None

# Fungsi utama untuk login dan melanjutkan aksi
def main():
    # Muat akun dari data.txt
    akun_list = load_accounts_from_file("data.txt")
    
    token_map = {}

    # Loop melalui akun dari data.txt untuk login
    for account in akun_list:
        if account not in token_map:
            log_message(f"--- Memulai sesi login untuk akun {account} ---", Fore.WHITE)
            new_token = request_new_token(account)  # Mendapatkan token baru
            if new_token:
                token_map[account] = new_token
            else:
                log_message(f"Gagal login dengan akun {account}, lanjutkan ke akun berikutnya.", Fore.RED)
                continue

        # Gunakan token yang telah didapat
        headers = {'authorization': token_map[account]}

        # Mulai proses klaim dan painting (Anda dapat melanjutkan dengan fungsi `paint`, `claim`, dll.)
        log_message(f"Token berhasil digunakan untuk akun {account}, memulai aksi painting...", Fore.GREEN)
        # Panggil fungsi paint atau klaim di sini dengan menggunakan token yang didapat

# Panggil fungsi utama
main()
