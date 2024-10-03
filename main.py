import requests
import json
import time
import random
from setproctitle import setproctitle
from convert import get
from colorama import Fore, Style, init
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib.parse  # Untuk decoding URL-encoded initData

url = "https://notpx.app/api/v1"

# Konfigurasi waktu tunggu
WAIT = 180 * 3
DELAY = 1

# Ukuran gambar
WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

setproctitle("notpixel")

# Ambil konfigurasi gambar
image = get("")

# Warna pixel
c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

# Fungsi untuk mencatat pesan dengan timestamp
def catat_pesan(pesan, warna=Style.RESET_ALL):
    waktu_sekarang = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.LIGHTBLACK_EX}{waktu_sekarang}{Style.RESET_ALL} {warna}{pesan}{Style.RESET_ALL}")

# Fungsi untuk inisialisasi sesi request dengan retry
def buat_sesi_dengan_retry(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    sesi = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    sesi.mount("http://", adapter)
    sesi.mount("https://", adapter)
    return sesi

# Buat sesi dengan retry
sesi = buat_sesi_dengan_retry()

# Fungsi untuk mendapatkan warna pixel dari server
def get_warna(pixel, header):
    try:
        response = sesi.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except KeyError:
        return "#000000"
    except requests.exceptions.Timeout:
        catat_pesan("Permintaan timeout", Fore.RED)
        return "#000000"
    except requests.exceptions.ConnectionError as e:
        catat_pesan(f"Kesalahan koneksi: {e}", Fore.RED)
        return "#000000"
    except requests.exceptions.RequestException as e:
        catat_pesan(f"Permintaan gagal: {e}", Fore.RED)
        return "#000000"

# Fungsi untuk klaim sumber daya dari server
def klaim(header):
    catat_pesan("Mengklaim sumber daya", Fore.CYAN)
    try:
        sesi.get(f"{url}/mining/claim", headers=header, timeout=10)
    except requests.exceptions.RequestException as e:
        catat_pesan(f"Gagal klaim sumber daya: {e}", Fore.RED)

# Fungsi untuk mendapatkan pixel berdasarkan koordinat x, y
def get_pixel(x, y):
    return y * 1000 + x + 1

# Fungsi untuk mendapatkan posisi x, y berdasarkan pixel
def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

# Fungsi untuk mengambil posisi canvas berdasarkan koordinat
def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

# Koordinat awal
start_x = 920
start_y = 386

# Fungsi untuk melukis pixel
def paint(canvas_pos, warna, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": warna
    }

    try:
        response = sesi.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = get_pos(canvas_pos, 1000)

        if response.status_code == 400:
            catat_pesan("Kehabisan energi", Fore.RED)
            return False
        if response.status_code == 401:
            return -1

        catat_pesan(f"Melukis: {x},{y}", Fore.GREEN)
        return True
    except requests.exceptions.RequestException as e:
        catat_pesan(f"Gagal melukis: {e}", Fore.RED)
        return False

# Fungsi untuk memuat akun dari data.txt
def load_accounts_from_file(filename):
    try:
        with open(filename, 'r') as file:
            akun = [line.strip() for line in file if line.strip()]
        return akun
    except FileNotFoundError:
        catat_pesan("File tidak ditemukan, pastikan data.txt ada.", Fore.RED)
        return []

# Fungsi untuk mengambil data mining
def fetch_mining_data(header, retries=3):
    for attempt in range(retries):
        try:
            response = sesi.get(f"{url}/mining/status", headers=header, timeout=10)
            if response.status_code == 200:
                data = response.json()
                user_balance = data.get('userBalance', 'Unknown')
                catat_pesan(f"Saldo: {user_balance}", Fore.MAGENTA)
                return True
            elif response.status_code == 401:
                catat_pesan(f"Gagal mengambil data mining: 401 Unauthorized", Fore.RED)
                return False
            else:
                catat_pesan(f"Gagal mengambil data mining: {response.status_code}", Fore.RED)
        except requests.exceptions.RequestException as e:
            catat_pesan(f"Kesalahan saat mengambil data mining: {e}", Fore.RED)
        time.sleep(1)  # Tunggu sedikit sebelum mencoba lagi
    return False

# Fungsi utama untuk proses akun
def proses_akun(akun):
    headers = {'authorization': akun}

    # Ambil data mining
    if not fetch_mining_data(headers):
        catat_pesan("DEAD :(", Fore.RED)
        print(headers["authorization"])
        return

    # Klaim sumber daya
    klaim(headers)

    size = len(image) * len(image[0])
    order = [i for i in range(size)]
    random.shuffle(order)

    for pos_image in order:
        x, y = get_pos(pos_image, len(image[0]))
        time.sleep(0.05 + random.uniform(0.01, 0.1))
        try:
            warna = get_warna(get_canvas_pos(x, y), headers)
            if warna == -1:
                catat_pesan("DEAD :(", Fore.RED)
                print(headers["authorization"])
                break

            if image[y][x] == ' ' or warna == c[image[y][x]]:
                catat_pesan(f"Skip: {start_x + x - 1},{start_y + y - 1}", Fore.RED)
                continue

            hasil = paint(get_canvas_pos(x, y), c[image[y][x]], headers)
            if hasil == -1:
                catat_pesan("DEAD :(", Fore.RED)
                print(headers["authorization"])
                break
            elif hasil:
                continue
            else:
                break

        except IndexError:
            catat_pesan(f"IndexError pada pos_image: {pos_image}, y: {y}, x: {x}", Fore.RED)

# Fungsi untuk proses akun secara berulang
def proses_semua_akun(akun_list):
    for akun in akun_list:
        catat_pesan(f"--- MEMULAI SESI UNTUK AKUN ---", Fore.BLUE)
        proses_akun(akun)

# Fungsi utama
if __name__ == "__main__":
    akun_list = load_accounts_from_file("data.txt")
    while True:
        proses_semua_akun(akun_list)
        time.sleep(5 * 60)  # Tunggu 5 menit sebelum memulai ulang sesi
