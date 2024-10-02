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

# WAKTU TUNGGU
TUNGGU = 180 * 3
DELAY = 1

# GAMBAR
LEBAR = 1000
TINGGI = 1000
MAX_TINGGI = 50

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

setproctitle("notpixel")

# Mengambil konfigurasi gambar
image = get("")

# Definisi warna untuk representasi pixel
c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

# Fungsi untuk mencatat pesan dengan timestamp
def catat_pesan(pesan, warna=Style.RESET_ALL):
    waktu_sekarang = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.LIGHTBLACK_EX}{waktu_sekarang}{Style.RESET_ALL} {warna}{pesan}{Style.RESET_ALL}")

# Fungsi untuk inisialisasi sesi requests dengan retry
def sesi_dengan_retry(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
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

# Membuat sesi dengan logika retry
sesi = sesi_dengan_retry()

# Fungsi untuk mendapatkan warna pixel dari server
def ambil_warna(pixel, header):
    try:
        response = sesi.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except KeyError:
        return "#000000"
    except requests.exceptions.Timeout:
        catat_pesan("Permintaan waktu habis", Fore.RED)
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

# Fungsi untuk menghitung indeks pixel berdasarkan posisi x, y
def ambil_pixel(x, y):
    return y * 1000 + x + 1

# Fungsi untuk mengambil posisi x, y dari indeks pixel
def ambil_posisi(pixel, size_x):
    return pixel % size_x, pixel // size_x

# Fungsi untuk menghitung posisi canvas berdasarkan x, y
def ambil_canvas_pos(x, y):
    return ambil_pixel(start_x + x - 1, start_y + y - 1)

# Koordinat awal
start_x = 920
start_y = 386

# Fungsi untuk melakukan aksi pengecatan
def cat(canvas_pos, warna, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": warna
    }

    try:
        response = sesi.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = ambil_posisi(canvas_pos, 1000)

        if response.status_code == 400:
            catat_pesan("Kehabisan energi", Fore.RED)
            return False
        if response.status_code == 401:
            return -1

        catat_pesan(f"Cat: {x},{y}", Fore.GREEN)
        return True
    except requests.exceptions.RequestException as e:
        catat_pesan(f"Gagal mengecat: {e}", Fore.RED)
        return False

# Fungsi untuk menginisialisasi sesi untuk setiap akun
def proses_akun(akun):
    header = {'authorization': akun}
    
    # Ambil data mining
    if not ambil_data_mining(header):
        catat_pesan("Mati :(", Fore.RED)
        print(header["authorization"])
        return

    # Klaim sumber daya
    klaim(header)
    
    # Proses pixel acak
    ukuran = len(image) * len(image[0])
    urutan = [i for i in range(ukuran)]
    random.shuffle(urutan)

    for pos_image in urutan:
        x, y = ambil_posisi(pos_image, len(image[0]))
        time.sleep(0.05 + random.uniform(0.01, 0.1))
        try:
            warna = ambil_warna(ambil_canvas_pos(x, y), header)
            if warna == -1:
                catat_pesan("Mati :(", Fore.RED)
                print(header["authorization"])
                break

            if image[y][x] == ' ' or warna == c[image[y][x]]:
                catat_pesan(f"Skip: {start_x + x - 1},{start_y + y - 1}", Fore.RED)
                continue

            hasil = cat(ambil_canvas_pos(x, y), c[image[y][x]], header)
            if hasil == -1:
                catat_pesan("Mati :(", Fore.RED)
                print(header["authorization"])
                break
            elif hasil:
                continue
            else:
                break

        except IndexError:
            catat_pesan(f"IndexError di pos_image: {pos_image}, y: {y}, x: {x}", Fore.RED)

# Fungsi untuk mengambil data mining (balance, stats)
def ambil_data_mining(header, retries=3):
    for attempt in range(retries):
        try:
            response = sesi.get(f"https://notpx.app/api/v1/mining/status", headers=header, timeout=10)
            if response.status_code == 200:
                data = response.json()
                saldo = data.get('userBalance', 'Tidak diketahui')
                catat_pesan(f"Saldo: {saldo}", Fore.MAGENTA)
                return True
            elif response.status_code == 401:
                catat_pesan(f"Data mining gagal: 401 Unauthorized", Fore.RED)
                return False
            else:
                catat_pesan(f"Data mining gagal: {response.status_code}", Fore.RED)
        except requests.exceptions.RequestException as e:
            catat_pesan(f"Error ambil data mining: {e}", Fore.RED)
        time.sleep(1)
    return False

# Fungsi utama untuk memproses akun
def proses_akun_terus(akun_list):
    waktu_mulai_akun_pertama = datetime.now()

    for akun in akun_list:
        catat_pesan("--- MULAI SESI UNTUK AKUN ---", Fore.BLUE)
        proses_akun(akun)

    waktu_berjalan = datetime.now() - waktu_mulai_akun_pertama
    waktu_tunggu = timedelta(minutes=50) - waktu_berjalan

    if waktu_tunggu.total_seconds() > 0:
        countdown(waktu_tunggu.total_seconds())
    else:
        catat_pesan(f"Tidak perlu tunggu, total waktu proses: {waktu_berjalan}", Fore.GREEN)

# Fungsi untuk menampilkan timer hitung mundur
def countdown(durasi):
    while durasi > 0:
        menit, detik = divmod(durasi, 60)
        timer = f'{int(menit):02}:{int(detik):02}'
        print(f'Timer hitung mundur: {timer}', end="\r")
        time.sleep(1)
        durasi -= 1

# Membaca daftar akun dari file data.txt
def baca_akun_dari_file(nama_file):
    with open(nama_file, 'r') as file:
        return [f"initData {line.strip()}" for line in file if line.strip()]

# Memuat daftar akun
akun_list = baca_akun_dari_file("data.txt")

# Loop terus menerus memproses akun
while True:
    proses_akun_terus(akun_list)
