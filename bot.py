import requests
import time
import random
from setproctitle import setproctitle
from getimage import get
from colorama import Fore, Style, init

# Konfigurasi URL
url = "https://notpx.app/api/v1"

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

# Fungsi untuk login menggunakan userid dari data.txt
def login_with_userid(userid):
    log_message(f"Login menggunakan userid: {userid}", Fore.YELLOW)
    try:
        # Kirim hanya userid yang berupa ID biasa
        response = requests.post(f"{url}/login", json={"userid": userid}, timeout=10)

        if response.status_code == 200:
            log_message("Login berhasil, token diperoleh.", Fore.GREEN)
            return response.json().get('token')
        else:
            log_message(f"Gagal login dengan userid {userid}: {response.status_code} - {response.text}", Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Kesalahan saat login: {e}", Fore.RED)
        return None

# Fungsi untuk mendapatkan headers dengan token
def get_headers(token=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    if token:
        headers['Authorization'] = f"Bearer {token}"
    return headers

# Fungsi untuk mengklaim sumber daya dari server
def claim(headers):
    log_message("Mengklaim sumber daya...", Fore.WHITE)
    try:
        response = requests.get(f"{url}/mining/claim", headers=headers, timeout=10)
        if response.status_code == 200:
            log_message("Sumber daya berhasil diklaim.", Fore.GREEN)
        else:
            log_message(f"Gagal mengklaim: {response.status_code} - {response.text}", Fore.RED)
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal mengklaim sumber daya: {e}", Fore.RED)

# Fungsi untuk memuat userid dari file data.txt
def load_userid_from_file(filename):
    try:
        with open(filename, 'r') as file:
            userid = file.readline().strip()  # Membaca userid dalam bentuk teks biasa
            log_message(f"User ID yang diambil: {userid}", Fore.CYAN)
            return userid
    except Exception as e:
        log_message(f"Error saat memuat userid dari {filename}: {e}", Fore.RED)
        return None

# Fungsi untuk mendapatkan warna pixel dari server
def get_color(pixel, headers):
    try:
        response = requests.get(f"{url}/image/get/{str(pixel)}", headers=headers, timeout=10)
        if response.status_code == 401:
            return -1  # Jika token kadaluwarsa, kembalikan kode -1
        return response.json().get('pixel', {}).get('color', "#000000")
    except requests.exceptions.RequestException as e:
        log_message(f"Gagal mendapatkan warna pixel: {e}", Fore.RED)
        return "#000000"

# Fungsi utama untuk melukis pixel dan menangani logika login dan token
def main():
    userid = load_userid_from_file("data.txt")
    if not userid:
        log_message("Tidak ada userid yang ditemukan di data.txt", Fore.RED)
        return
    
    token = login_with_userid(userid)
    if not token:
        log_message("Tidak dapat melanjutkan tanpa token yang valid.", Fore.RED)
        return

    headers = get_headers(token)

    # Melukis pixel pada kanvas
    for _ in range(10):  # Loop untuk 10 kali percobaan melukis
        try:
            # Contoh klaim sumber daya
            claim(headers)

            # Pilih pixel secara acak untuk dilukis
            pixel = random.randint(0, 1000)  # Ganti dengan logika pixel yang sesuai
            color = get_color(pixel, headers)

            # Jika token kadaluwarsa, login ulang
            if color == -1:
                log_message("Token kadaluwarsa, melakukan login ulang...", Fore.RED)
                token = login_with_userid(userid)
                if not token:
                    log_message("Gagal memperbarui token.", Fore.RED)
                    break
                headers = get_headers(token)
            else:
                log_message(f"Pixel {pixel} berhasil dilukis dengan warna {color}.", Fore.GREEN)

            time.sleep(random.uniform(1, 3))  # Jeda acak antara request

        except requests.exceptions.RequestException as e:
            log_message(f"Error saat melukis: {e}", Fore.RED)

# Jalankan program utama
if __name__ == "__main__":
    main()
