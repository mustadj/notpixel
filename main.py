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
  
# Define constants  
url = "https://notpx.app/api/v1"  
WAIT = 180 * 3  
DELAY = 1  
WIDTH = 1000  
HEIGHT = 1000  
MAX_HEIGHT = 50  
  
# Initialize colorama for colored output  
init(autoreset=True)  
  
# Set process title  
setproctitle("notpixel")  
  
# Define image data (replace with actual image data)  
image = [  
   ["#", "#", "#", "#", "#"],  
   ["#", ".", ".", ".", "#"],  
   ["#", ".", "*", ".", "#"],  
   ["#", ".", ".", ".", "#"],  
   ["#", "#", "#", "#", "#"]  
]  
  
# Define start coordinates (replace with actual coordinates)  
start_x = 920  
start_y = 386  
  
# Define color dictionary (replace with actual color data)  
c = {  
   "#": "#000000",  
   ".": "#3690EA",  
   "*": "#ffffff"  
}  
  
# Define accounts (replace with actual account data)  
accounts = ["account1", "account2", "account3"]  
  
# Define functions  
def log_message(message, color=Style.RESET_ALL):  
   print(f"{color}{message}{Style.RESET_ALL}")  
  
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
  
def claim(header):  
   log_message("Auto claiming started.", Fore.WHITE)  
   try:  
      session.get(f"{url}/mining/claim", headers=header, timeout=10)  
   except requests.exceptions.RequestException as e:  
      log_message(f"Gagal mengklaim sumber daya: {e}", Fore.RED)  
  
def get_pixel(x, y):  
   return y * 1000 + x + 1  
  
def get_pos(pixel, size_x):  
   return pixel % size_x, pixel // size_x  
  
def get_canvas_pos(x, y):  
   return get_pixel(start_x + x - 1, start_y + y - 1)  
  
def paint(canvas_pos, color, header):  
   data = {  
      "pixelId": canvas_pos,  
      "newColor": color  
   }  
   try:  
      response = session.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)  
      if response.status_code == 400:  
        log_message("Painter: No charge available. Sleeping for 10 minutes.", Fore.RED)  
        return False  
      if response.status_code == 401:  
        return -1  
      log_message(f"Painter: 1 Pixel painted successfully.", Fore.LIGHTGREEN_EX)  
      return True  
   except requests.exceptions.RequestException as e:  
      log_message(f"Gagal melukis: {e}", Fore.RED)  
      return False  
  
def load_accounts_from_file(filename):  
   with open(filename, 'r') as file:  
      accounts = [f"initData {line.strip()}" for line in file if line.strip()]  
   return accounts  
  
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
           log_message(f" Userid dari data.txt : 401 Unauthorized", Fore.RED)  
           return False  
        else:  
           log_message(f"Gagal mengambil data mining: {response.status_code}", Fore.RED)  
      except requests.exceptions.RequestException as e:  
        log_message(f"Kesalahan saat mengambil data mining: {e}", Fore.RED)  
      time.sleep(1)  # Tunggu sebentar sebelum mencoba lagi  
   return False  
  
def request_new_token(account):  
   log_message("Meminta token baru...", Fore.YELLOW)  
   try:  
      # Ganti dengan endpoint yang sesuai untuk mendapatkan token baru  
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
  
def main(auth, account):  
   headers = {'authorization': auth}  
   log_message("Auto painting started.", Fore.WHITE)  
   try:  
      # Ambil data mining (saldo) sebelum mengklaim sumber daya  
      if not fetch_mining_data(headers):  
        log_message("Token Dari data .txt Expired :(", Fore.RED)  
        # Mendapatkan token baru  
        new_auth = request_new_token(account)  # Mendapatkan token baru  
        if new_auth:  
           headers['authorization'] = new_auth  # Perbarui header dengan token baru  
           log_message("Token diperbarui.", Fore.GREEN)  
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
        time.sleep(random.uniform(0.05, 0.2))  # Jeda acak di antara permintaan  
        try:  
           color = get_color(get_canvas_pos(x, y), headers)  
           if color == -1:  
              log_message("Expired Bang", Fore.RED)  
              print(headers["authorization"])  
              break  
           if image[y][x] == ' ' or color == c[image[y][x]]:  
              continue  
           result = paint(get_canvas_pos(x, y), c[image[y][x]], headers)  
           if result == -1:  
              log_message("Token Expired :(", Fore.RED)  
              print(headers["authorization"])  
              break  
           elif not result:  
              break  
           # Simulasi pergerakan mouse dengan jeda acak  
           time.sleep(random.uniform(0.1, 0.3))  # Jeda tambahan  
        except IndexError:  
           log_message(f"IndexError pada pos_image: {pos_image}, y: {y}, x: {x}", Fore.RED)  
   except requests.exceptions.RequestException as e:  
      log_message(f"Kesalahan jaringan di akun: {e}", Fore.RED)
  
# Fungsi untuk memproses semua akun dan logika tidur  
def process_accounts(accounts):  
   for account in accounts:  
      # Proses setiap akun satu per satu  
      log_message(f"--- MEMULAI SESI UNTUK AKUN ---", Fore.WHITE)  
      main(account, account)  
      break  # Tambahkan break di sini untuk tidak mengulang sesi  
  
# Muat akun dari data.txt  
akun_list = load_accounts_from_file("data.txt")  
  
# Loop terus menerus untuk memproses akun  
while True:  
