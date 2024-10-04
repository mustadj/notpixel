import requests
import json
import time
import random
from setproctitle import setproctitle
from getimage import get
from colorama import Fore, Style, init
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

# Tambahkan headers untuk menyerupai request dari browser sungguhan
def get_headers(token=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://example.com',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0'
    }
    if token:
        headers['authorization'] = f"Bearer {token}"
    return headers

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
        accounts = [line.strip() for line in file if line.strip()]
    return accounts

# Fungsi untuk login dengan userid dari data.txt dan mendapatkan token
def login_with_userid(userid):
    log_message(f"Login menggunakan userid: {userid}", Fore.YELLOW)
    try:
        response = session.post(f"{url}/login", data={"userid": userid}, timeout=10)
        if response.status_code == 200:
            log_message("Login berhasil, token diperoleh.", Fore.GREEN)
            return response.json().get('token')
        else:
            log_message(f"Gagal login dengan userid {userid}: {response.status_code}", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat login: {e}", Fore.RED)
        return None

# Fungsi utama untuk melakukan proses melukis
def main(userid):
    token = login_with_userid(userid)
    if not token:
        log_message("Tidak dapat melanjutkan tanpa token yang valid.", Fore.RED)
        return

    headers = get_headers(token)

    while True:
        try:
            if not fetch_mining_data(headers):
                log_message("Token expired. Meminta token baru...", Fore.YELLOW)
                token = login_with_userid(userid)
                if not token:
                    log_message("Gagal memperbarui token. Keluar.", Fore.RED)
                    return
                headers = get_headers(token)

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
                        log_message("Token expired. Meminta token baru...", Fore.RED)
                        break

                    if image[y][x] == ' ' or color == c[image[y][x]]:
                        continue

                    result = paint(get_canvas_pos(x, y), c[image[y][x]], headers)
                    if result == -1:
                        log_message("Token expired, meminta token baru...", Fore.RED)
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

# Muat satu userid dari data.txt
akun_list = load_accounts_from_file("data.txt")

# Panggil main hanya dengan satu userid
if akun_list:
    main(akun_list[0])
else:
    log_message("Tidak ada userid yang ditemukan di data.txt", Fore.RED)
