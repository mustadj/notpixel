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
import os

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
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Fungsi untuk menyimpan token ke dalam data.txt
def save_token(token):
    with open("data.txt", "w") as file:
        file.write(token)

# Fungsi untuk membaca token dari data.txt
def get_saved_token():
    if os.path.exists("data.txt"):
        with open("data.txt", "r") as file:
            return file.read().strip()
    return None

# Fungsi untuk login, hanya dilakukan jika token tidak ditemukan
def login():
    token = get_saved_token()
    if token:
        log_message("Token ditemukan, login tidak diperlukan.")
        return token
    else:
        log_message("Token tidak ditemukan, melakukan login...")
        # Contoh proses login di sini
        # response = requests.post(f"{url}/login", data={"username": "your_username", "password": "your_password"})
        # token = response.json().get("token")
        token = "contoh_token"  # Ini hanya placeholder, sesuaikan dengan hasil login
        save_token(token)
        return token

# Main execution
def main():
    session = get_session_with_retries()
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    # Mulai proses utama dengan token yang telah tersimpan
    log_message("Proses utama dimulai dengan token yang sudah ada.")

if __name__ == "__main__":
    main()

