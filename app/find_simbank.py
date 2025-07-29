import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

# Настрой диапазон своей подсети
SUBNET = "192.168.2.0/24"
TIMEOUT = 1.5  # секунды

def check_ip(ip):
    url = f"http://{ip}"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if "SIM Bank" in r.text or "GoIP" in r.text:
            print(f"[+] Найден SIM-банк по адресу: {ip}")
            return str(ip)
    except requests.RequestException:
        pass
    return None

def find_simbank():
    network = ipaddress.ip_network(SUBNET, strict=False)
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_ip, [str(ip) for ip in network.hosts()])
        for ip in results:
            if ip:
                return ip
    print("[-] SIM-банк не найден.")
    return None

if __name__ == "__main__":
    ip = find_simbank()
    if ip:
        print(f"[✓] SIM-банк GoIP найден: {ip}")
    else:
        print("[×] SIM-банк не найден в локальной сети.")
