import socket
import requests
from ipaddress import ip_network
from concurrent.futures import ThreadPoolExecutor

SUBNET = "192.168.0.0/24"
PORT = 80
TIMEOUT = 1
PATH = "/default/en_US/tools.html"

def scan_port(ip):
    """Проверка открытого порта 80"""
    try:
        with socket.create_connection((str(ip), PORT), timeout=TIMEOUT):
            return str(ip)
    except:
        return None

def check_http_path(ip):
    """Проверка наличия нужного URL"""
    url = f"http://{ip}{PATH}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"[✔] {ip} — найден путь {PATH}")
        else:
            print(f"[✖] {ip} — {PATH} вернул статус {response.status_code}")
    except:
        print(f"[!] {ip} — ошибка соединения при запросе {PATH}")

if __name__ == "__main__":
    print(f"🔍 Сканируем подсеть {SUBNET} на открытый порт 80...")
    ips = list(ip_network(SUBNET).hosts())

    # Сканируем IP на наличие открытого порта
    with ThreadPoolExecutor(max_workers=254) as executor:
        results = list(executor.map(scan_port, ips))

    # Фильтруем только успешные
    live_hosts = [ip for ip in results if ip]

    print(f"\n🌐 Найдено {len(live_hosts)} устройств с портом 80\n")

    # Проверяем путь на найденных IP
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(check_http_path, live_hosts)
