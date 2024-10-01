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
import urllib.parse  # For decoding the URL-encoded initData

url = "https://notpx.app/api/v1"

# ACTIVITY
WAIT = 180 * 3
DELAY = 1

# IMAGE
WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

# Initialize colorama for colored output
init(autoreset=True)

setproctitle("notpixel")

# Retrieve the image configuration
image = get("")

# Define colors for pixel representation
c = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

# Function to log messages with timestamp in light grey color
def log_message(message, color=Style.RESET_ALL):
    current_time = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {color}{message}{Style.RESET_ALL}")

# Function to initialize a requests session with retry logic
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

# Create a session with retry logic
session = get_session_with_retries()

# Function to get the color of a pixel from the server
def get_color(pixel, header):
    try:
        response = session.get(f"{url}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 401:
            return -1
        return response.json()['pixel']['color']
    except KeyError:
        return "#000000"
    except requests.exceptions.Timeout:
        log_message("Request timed out", Fore.RED)
        return "#000000"
    except requests.exceptions.ConnectionError as e:
        log_message(f"Connection error: {e}", Fore.RED)
        return "#000000"
    except requests.exceptions.RequestException as e:
        log_message(f"Request failed: {e}", Fore.RED)
        return "#000000"

# Function to claim resources from the server
def claim(header, username):
    log_message(f"Claiming resources for {username}", Fore.CYAN)
    try:
        session.get(f"{url}/mining/claim", headers=header, timeout=10)
    except requests.exceptions.RequestException as e:
        log_message(f"Failed to claim resources for {username}: {e}", Fore.RED)

# Function to calculate pixel index based on x, y position
def get_pixel(x, y):
    return y * 1000 + x + 1

# Function to get x, y position from pixel index
def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

# Function to get pixel index based on canvas position
def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

# Starting coordinates
start_x = 920
start_y = 386

# Function to perform the painting action
def paint(canvas_pos, color, header, username):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }

    try:
        response = session.post(f"{url}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = get_pos(canvas_pos, 1000)

        if response.status_code == 400:
            log_message(f"Out of energy for {username}", Fore.RED)
            return False
        if response.status_code == 401:
            return -1

        log_message(f"Paint: {x},{y} for {username}", Fore.GREEN)
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"Failed to paint for {username}: {e}", Fore.RED)
        return False

# Function to extract the username from the URL-encoded init data
def extract_username_from_initdata(init_data):
    # URL decode the init data
    decoded_data = urllib.parse.unquote(init_data)
    
    # Find the part that contains "username"
    username_start = decoded_data.find('"username":"') + len('"username":"')
    username_end = decoded_data.find('"', username_start)
    
    if username_start != -1 and username_end != -1:
        return decoded_data[username_start:username_end]
    
    return "Unknown"

# Function to load accounts from data.txt
def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [f"initData {line.strip()}" for line in file if line.strip()]
    return accounts

# Function to fetch mining data (balance and other stats) with retry logic
def fetch_mining_data(header, username, retries=3):
    for attempt in range(retries):
        try:
            response = session.get(f"https://notpx.app/api/v1/mining/status", headers=header, timeout=10)
            if response.status_code == 200:
                data = response.json()
                user_balance = data.get('userBalance', 'Unknown')
                log_message(f"Balance for {username}: {user_balance}", Fore.MAGENTA)
                return True
            elif response.status_code == 401:
                log_message(f"Failed to fetch mining data for {username}: 401 Unauthorized", Fore.RED)
                return False
            else:
                log_message(f"Failed to fetch mining data for {username}: {response.status_code}", Fore.RED)
        except requests.exceptions.RequestException as e:
            log_message(f"Error fetching mining data for {username}: {e}", Fore.RED)
        time.sleep(1)  # Wait a bit before retrying
    return False

# Main function to perform the painting process
def main(auth, account):
    headers = {'authorization': auth}
    username = extract_username_from_initdata(account)

    try:
        # Fetch mining data (balance) before claiming resources
        if not fetch_mining_data(headers, username):
            log_message(f"{username} is DEAD :(", Fore.RED)
            print(headers["authorization"])
            return

        # Claim resources
        claim(headers, username)

        size = len(image) * len(image[0])
        order = [i for i in range(size)]
        random.shuffle(order)

        for pos_image in order:
            x, y = get_pos(pos_image, len(image[0]))
            time.sleep(0.05 + random.uniform(0.01, 0.1))
            try:
                color = get_color(get_canvas_pos(x, y), headers)
                if color == -1:
                    log_message(f"{username} is DEAD :(", Fore.RED)
                    print(headers["authorization"])
                    break

                if image[y][x] == ' ' or color == c[image[y][x]]:
                    log_message(f"Skip: {start_x + x - 1},{start_y + y - 1} for {username}", Fore.RED)
                    continue

                result = paint(get_canvas_pos(x, y), c[image[y][x]], headers, username)
                if result == -1:
                    log_message(f"{username} is DEAD :(", Fore.RED)
                    print(headers["authorization"])
                    break
                elif result:
                    continue
                else:
                    break

            except IndexError:
                log_message(f"IndexError at pos_image: {pos_image}, y: {y}, x: {x} for {username}", Fore.RED)

    except requests.exceptions.RequestException as e:
        log_message(f"Network error in account {username}: {e}", Fore.RED)

# Main process loop to manage accounts and sleep logic
def process_accounts(accounts):
    # Track the start time of the first account
    first_account_start_time = datetime.now()

    for account in accounts:
        # Process each account one by one
        username = extract_username_from_initdata(account)
        log_message(f"--- STARTING SESSION FOR ACCOUNT ---", Fore.BLUE)
        main(account, account)

    # Calculate the time elapsed since the first account started processing
    time_elapsed = datetime.now() - first_account_start_time
    time_to_wait = timedelta(minutes=35) - time_elapsed  # Changed to 35 minutes

    if time_to_wait.total_seconds() > 0:
        countdown_timer(time_to_wait.total_seconds())
    else:
        log_message(f"NO SLEEP NEEDED, TOTAL PROCESSING TIME: {time_elapsed}", Fore.GREEN)

# Function to display a countdown timer
def countdown_timer(duration):
    while duration > 0:
        mins, secs = divmod(duration, 60)
        timer = f'{int(mins):02}:{int(secs):02}'
        print(f'Countdown Timer: {timer}', end="\r")
        time.sleep(1)
        duration -= 1

# Load the accounts from data.txt
accounts = load_accounts_from_file("data.txt")

# Continuously process accounts in a loop
while True:
