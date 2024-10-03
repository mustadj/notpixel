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
        if response.status_code == 200:
            log_message("Claim berhasil.", Fore.LIGHTGREEN_EX)
        else:
            log_message(f"Claim gagal dengan status: {response.status_code}", Fore.RED)
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
            countdown_timer(10 * 60)  # Tambahkan countdown timer 10 menit di sini
            return False
        if response.status_code == 401:
            return -1

        log_message(f"Painter: 1 Pixel painted successfully.", Fore.LIGHTGREEN_EX)
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal melukis: {e}", Fore.RED)
        return False

# Fungsi untuk mendapatkan token dari file data.txt
def load_token_from_file(filename):
    with open(filename, 'r') as file:
        token = file.readline().strip()  # Ambil token dari baris pertama
    return token

# Fungsi untuk memperbarui token jika expired
def refresh_token():
    log_message("Meminta token baru...", Fore.YELLOW)
    # Implementasikan logika yang benar di sini untuk mendapatkan token baru
    # Hapus 'NEW_TOKEN_HERE' dan gunakan cara yang benar untuk mengambil token baru.
    
    new_token = "NEW_TOKEN_HERE"  # Ganti dengan logika yang benar untuk mendapatkan token baru
    if new_token:
        with open("data.txt", 'w') as file:
            file.write(new_token)  # Simpan token baru ke file
        return new_token
    return None

# Fungsi utama untuk melakukan proses melukis
def main():
    token = load_token_from_file("data.txt")
    headers = {
        'Authorization': token,  # Gunakan token dari file
    }

    log_message("Auto painting started.", Fore.WHITE)

    try:
        # Lakukan klaim dengan header yang benar
        claim(headers)

        size = len(image) * len(image[0])
        order = [i for i in range(size)]
        random.shuffle(order)

        for pos_image in order:
            x, y = get_pos(pos_image, len(image[0]))
            time.sleep(random.uniform(0.05, 0.2))  # Jeda acak di antara permintaan

            try:
                color = get_color(get_canvas_pos(x, y), headers)
                if color == -1:
                    log_message("Expired Bang", Fore.RED)
                    print(headers["Authorization"])
                    # Jika token expired, refresh token
                    new_token = refresh_token()
                    if new_token:
                        headers["Authorization"] = new_token
                    else:
                        log_message("Gagal memperbarui token.", Fore.RED)
                        break
                elif image[y][x] != ' ' and color != c[image[y][x]]:
                    result = paint(get_canvas_pos(x, y), c[image[y][x]], headers)
                    if result == -1:
                        log_message("Token Expired :(", Fore.RED)
                        print(headers["Authorization"])
                        break
                    elif not result:
                        break
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

# Panggil main dengan token
main()
