import requests
import json
import time
import random
from setproctitle import setproctitle
from convert import get
from colorama import Fore, Style, init
from urllib.parse import unquote  # Untuk decode URL
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

url = "https://notpx.app/api/v1"

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)
setproctitle("notpixel")

# Fungsi untuk mencatat pesan dengan timestamp
def log_message(message, color=Style.RESET_ALL):
    print(f"{color}{message}{Style.RESET_ALL}")

# Fungsi untuk memuat akun dari data.txt dan melakukan decode URL
def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [unquote(line.strip()) for line in file if line.strip()]  # Decode URL-encoded data
    return accounts

# Fungsi untuk ekstrak user_id dari data yang sudah ter-decode
def extract_user_id(account_data):
    # Misalkan data setelah decode memiliki bentuk seperti "user={...}&chat_instance=..."
    # Kita hanya ingin mengambil bagian setelah "user=" dan sebelum "&"
    try:
        user_id = account_data.split('user=')[1].split('&')[0]  # Ambil user_id dari URL
        return json.loads(user_id).get('id')  # Ambil ID dari struktur JSON
    except (IndexError, json.JSONDecodeError):
        log_message(f"Format data akun tidak sesuai: {account_data}", Fore.RED)
        return None

# Fungsi untuk membuat session dengan retry
def get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Inisialisasi session
session = get_session_with_retries()

# Fungsi untuk mendapatkan token baru (sesuai format yang diharapkan oleh API)
def request_new_token(account):
    log_message(f"Meminta token baru untuk akun {account}...", Fore.YELLOW)
    
    # Ekstrak user_id
    user_id = extract_user_id(account)
    if not user_id:
        log_message(f"Gagal mengekstrak user_id dari akun: {account}", Fore.RED)
        return None

    try:
        # Ganti dengan endpoint yang sesuai untuk mendapatkan token baru
        response = session.post(f"{url}/login", data=json.dumps({"userid": user_id}), headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code == 200:
            new_token = response.json().get('token')
            if new_token:
                log_message(f"Berhasil login, token diterima untuk akun {user_id}.", Fore.GREEN)
                return new_token
            else:
                log_message(f"Tidak ada token dalam respons login akun {user_id}.", Fore.RED)
                return None
        elif response.status_code == 404:
            log_message(f"Kesalahan 404: Endpoint tidak ditemukan untuk akun {user_id}.", Fore.RED)
            return None
        else:
            log_message(f"Gagal mendapatkan token baru: {response.status_code} untuk akun {user_id}.", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat meminta token baru untuk akun {user_id}: {e}", Fore.RED)
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
