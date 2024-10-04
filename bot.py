import requests
import json
import time
import random
import shelve
from setproctitle import setproctitle
from getimage import get
from colorama import Fore, Style, init
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

url = "https://notpx.app/api/v1"

# WAKTU TUNGGU
WAIT = 180 * 3
DELAY = random.uniform(1, 3)

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

# Buat session dengan logika retry
session = get_session_with_retries()

# Fungsi untuk menyimpan token ke session
def save_session(token, expiry):
    with shelve.open("session.db") as session_store:
        session_store['token'] = token
        session_store['expiry'] = expiry

# Fungsi untuk mengambil token dari session
def load_session():
    with shelve.open("session.db") as session_store:
        token = session_store.get('token', None)
        expiry = session_store.get('expiry', None)
        return token, expiry

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
        session.get(f"{url}/mining/claim", headers=header, timeout=10)
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
            log_message("Painter: No charge available. Sleeping for 10 minutes.", Fore.RED)
            countdown_timer(10 * 60)
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
        time.sleep(1)
    return False

# Fungsi untuk mendapatkan token baru
def request_new_token(account):
    log_message("Meminta token baru...", Fore.YELLOW)
    try:
        response = session.post(f"{url}/login", data={"account": account}, timeout=10)
        if response.status_code == 200:
            new_token = response.json().get('token')
            expiry = datetime.now() + timedelta(hours=1)  # Token valid for 1 hour
            return new_token, expiry
        else:
            log_message(f"Gagal mendapatkan token baru: {response.status_code}", Fore.RED)
            return None, None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat meminta token baru: {e}", Fore.RED)
        return None, None

# Fungsi untuk memperbarui token jika sudah mendekati kadaluwarsa
def ensure_token_is_valid(account, headers):
    token, expiry = load_session()
    if token and expiry and expiry > datetime.now():
        log_message("Token valid, tidak perlu diperbarui.", Fore.GREEN)
        headers['authorization'] = token
    else:
        log_message("Token kadaluwarsa atau tidak ada, meminta token baru.", Fore.YELLOW)
        new_token, new_expiry = request_new_token(account)
        if new_token:
            headers['authorization'] = new_token
            save_session(new_token, new_expiry)
        else:
            log_message("Gagal memperbarui token.", Fore.RED)

# Fungsi utama untuk melakukan proses melukis
def main(account):
    headers = get_headers()

    while True:
        ensure_token_is_valid(account, headers)

        try:
            if not fetch_mining_data(headers):
                log_message("Token expired.", Fore.RED)
                return

            # Klaim sumber daya
            claim(headers)

            size = len(image) * len(image[0])
            order = [i for i in range(size)]
            random.shuffle(order)

            for pos_image in order:
                x, y = get_pos(pos_image, len(image[0]))
                time.sleep(random.uniform(1, 3))

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

                    time.sleep(random.uniform(0.1, 0.3))

                except IndexError:
                    log_message(f"IndexError pada pos_image: {pos_image}, y: {y}, x: {x}", Fore.RED)

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

# Muat satu akun dari data.txt
akun_list = load_accounts_from_file("data.txt")

# Panggil main hanya dengan satu akun
if akun_list:
    main(akun_list[0])
else:
    log_message("Tidak ada akun yang ditemukan di data.txt", Fore.RED)
