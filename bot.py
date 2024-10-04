import os
import sys
import requests
import json
import time
import random
import shelve
from setproctitle import setproctitle
from getimage import get
from colorama import Fore, Style, init
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

url = "https://notpx.app/api/v1"

# WAKTU TUNGGU
WAIT = 180 * 3
DELAY = random.uniform(1, 3)  # Delay acak lebih luas untuk anti-bot

# DIMENSI GAMBAR
WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

setproctitle("notpixel")

# Clear terminal saat bot dimulai
os.system('clear')

# Ambil konfigurasi gambar
image = get("")

# Definisikan warna untuk representasi pixel
c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

# Fungsi untuk mencatat pesan dengan timestamp dan meng-update satu baris secara dinamis
def log_message(message, color=Style.RESET_ALL, newline=True):
    if newline:
        sys.stdout.write(f"{color}{message}{Style.RESET_ALL}\n")
    else:
        sys.stdout.write(f"\r{color}{message}{Style.RESET_ALL}")  # Tidak ada spasi di sini
    sys.stdout.flush()

# Fungsi untuk menampilkan timer tanpa bertumpuk dengan log dan membersihkan karakter setelah timer selesai
def countdown_timer(duration):
    while duration > 0:
        mins, secs = divmod(duration, 60)
        timer = f'{int(mins):02}:{int(secs):02}'
        sys.stdout.write(f"\rWaktu Tunggu Sebelum Mengelang Eksekusi: {timer}")  # Tidak ada spasi ekstra
        sys.stdout.flush()
        time.sleep(1)
        duration -= 1
    sys.stdout.write("\rCountdown selesai. Melanjutkan proses...\n")  # Kursor pindah ke bawah setelah selesai
    sys.stdout.flush()

# Fungsi untuk menginisialisasi session requests dengan logika retry
def get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False  # Jangan langsung raise error jika status 500
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Buat session dengan logika retry
session = get_session_with_retries()

# Fungsi untuk menyimpan token ke session
def save_session(token):
    with shelve.open("session.db") as session:
        session['token'] = token

# Fungsi untuk mengambil token dari session
def load_session():
    with shelve.open("session.db") as session:
        return session.get('token', None)

# Tambahkan headers untuk menyerupai request dari browser sungguhan
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://example.com',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0'
    }

# Fungsi untuk mendapatkan warna pixel dari server
def get_color(pixel, header):
    try:
        response = session.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except KeyError:
        return "#000000"
    except requests.exceptions.Timeout:
        return "#000000"
    except requests.exceptions.ConnectionError as e:
        log_message(f"Kesalahan koneksi: {e}", Fore.RED)
        return "#000000"
    except requests.exceptions.RequestException as e:
        log_message(f"Permintaan gagal: {e}", Fore.RED)
        return "#000000"

# Fungsi untuk mengklaim sumber daya dari server
def claim(header):
    log_message("Auto claiming started.", Fore.WHITE)
    try:
        response = session.get(f"{url}/mining/claim", headers=header, timeout=10)
        if response.status_code == 500:
            log_message(f"Server error saat klaim, coba lagi nanti.", Fore.RED)
            time.sleep(WAIT)  # Tunggu lebih lama sebelum mencoba lagi
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal mengklaim sumber daya: {e}", Fore.RED)

# Fungsi untuk menghitung indeks pixel berdasarkan posisi x, y
def get_pixel(x, y):
    return y * 1000 + x + 1

# Fungsi untuk mendapatkan posisi x, y dari indeks pixel
def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

# Fungsi untuk mendapatkan indeks pixel berdasarkan posisi canvas
def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

# Koordinat awal
start_x = 920
start_y = 386

# Fungsi untuk melakukan aksi melukis
def paint(canvas_pos, color, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }

    try:
        response = session.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        if response.status_code == 400:
            log_message("Painter: No charge available. Sleeping for 60 minutes.", Fore.BLUE)
            countdown_timer(60 * 60)
            log_message("Timer selesai. Melanjutkan eksekusi.", Fore.YELLOW)
            return False
        if response.status_code == 401:
            return -1

        log_message(f"Painter: 1 Pixel painted successfully.", Fore.LIGHTGREEN_EX)
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal melukis: {e}", Fore.RED)
        return False

# Fungsi untuk memuat akun dari data.txt
def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [f"initData {line.strip()}" for line in file if line.strip()]
    return accounts

# Fungsi untuk mengambil data mining (saldo dan statistik lainnya) dengan logika retry
def fetch_mining_data(header, retries=3):
    for attempt in range(retries):
        try:
            response = session.get(f"{url}/mining/status", headers=header, timeout=10)
            if response.status_code == 200:
                data = response.json()
                user_balance = data.get('userBalance', 'Unknown')
                log_message(f"Jumlah Pixel: {user_balance}", Fore.WHITE)
                return True
            elif response.status_code == 401:
                log_message(f"Userid dari data.txt : 401 Unauthorized", Fore.RED)
                return False
            else:
                log_message(f"Gagal mengambil data mining: {response.status_code}", Fore.RED)
        except requests.exceptions.RequestException as e:
            log_message(f"Kesalahan saat mengambil data mining: {e}", Fore.RED)
        time.sleep(1)  # Tunggu sebentar sebelum mencoba lagi
    return False

# Fungsi untuk mendapatkan token baru
def request_new_token(account):
    log_message("Meminta token baru...", Fore.YELLOW)
    try:
        response = session.post(f"{url}/login", data={"account": account}, timeout=10)
        if response.status_code == 200:
            new_token = response.json().get('token')
            return new_token
        else:
            log_message(f"Gagal mendapatkan token baru: {response.status_code}", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat meminta token baru: {e}", Fore.RED)
        return None

# Fungsi utama untuk melakukan proses melukis
def main(auth, account):
    headers = get_headers()

    # Periksa apakah ada token di session
    session_token = load_session()
    if session_token:
        headers['authorization'] = session_token
        log_message("Token loaded from session.", Fore.GREEN)
    else:
        headers['authorization'] = auth

    log_message("Auto painting started.", Fore.WHITE)

    while True:
        try:
            if not fetch_mining_data(headers):
                log_message("Token Dari session atau data.txt Expired :(", Fore.RED)
                new_auth = request_new_token(account)
                if new_auth:
                    headers['authorization'] = new_auth
                    save_session(new_auth)  # Simpan token baru ke session
                    log_message("Token diperbarui dan disimpan ke session.", Fore.GREEN)
                else:
                    log_message("Gagal mendapatkan token baru.", Fore.RED)
                    return

            # Klaim sumber daya
            claim(headers)

            size = len(image) * len(image[0])
            order = [i for i in range(size)]
            random.shuffle(order)

            for pos_image in order:
                x, y = get_pos(pos_image, len(image[0]))
                time.sleep(random.uniform(1, 3))  # Jeda acak yang lebih besar

                try:
                    color = get_color(get_canvas_pos(x, y), headers)
                    if color == -1:
                        log_message("Expired Bang", Fore.RED)
                        break

                    if image[y][x] == ' ' or color == c[image[y][x]]:
                        continue

                    result = paint(get_canvas_pos(x, y), c[image[y][x]], headers)
                    if result == -1:
                        log_message("Token Expired :(", Fore.RED)
                        break
                    elif not result:
                        break

                    time.sleep(random.uniform(0.1, 0.3))  # Jeda tambahan

                except IndexError:
                    log_message(f"IndexError pada pos_image: {pos_image}, y: {y}, x: {x}", Fore.RED)

        except requests.exceptions.RequestException as e:
            log_message(f"Kesalahan jaringan di akun: {e}", Fore.RED)

# Muat satu akun dari data.txt
akun_list = load_accounts_from_file("data.txt")

# Panggil main hanya dengan satu akun
if akun_list:
    main(akun_list[0], akun_list[0])
else:
    log_message("Tidak ada akun yang ditemukan di data.txt", Fore.RED)
