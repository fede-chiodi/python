import subprocess
import platform
from threading import Thread
import socket

class Share:
    host_up_counter = 0
    host_down_counter = 0

def ping(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    process = subprocess.run(["ping", param, "1", host], capture_output=True)
    return (process.returncode == 0) \
        and ("100% persi" not in process.stdout.decode()) \
        and ("Host di destinazione non raggiungibile" not in process.stdout.decode())

def subnet_to_cidr(subnet_mask):
    octets = subnet_mask.split(".")
    binary_str = ''.join(bin(int(octet)) for octet in octets)
    cidr = binary_str.count('1')

    return cidr

def find_hosts_in_net(ip, subnet_mask):
    cidr = subnet_to_cidr(subnet_mask)
    ip_l = list(map(int, ip.split('.')))
    subnet_mask_l = list(map(int, subnet_mask.split('.')))
    network_ip = [ip_l[i] & subnet_mask_l[i] for i in range(4)]
    broadcast_ip = [ip_l[i] + 255 - subnet_mask_l[i] for i in range(4)]

    net_int = (network_ip[0] << 24) + (network_ip[1] << 16) + (network_ip[2] << 8) + network_ip[3]
    broadcast_int = (broadcast_ip[0] << 24) + (broadcast_ip[1] << 16) + (broadcast_ip[2] << 8) + broadcast_ip[3]
    hosts_number = 2**(32-cidr) 

    ip_list = []
    for i in range (1, hosts_number):
        ip_int = net_int + i
        if ip_int != broadcast_int:
            ip_str = ".".join(str((ip_int >> (8 * j)) & 0xFF) for j in reversed(range(4)))
            ip_list.append(ip_str)
        else:
            return ip_list

    return ip_list

hosts_up = []
def ping_host(hosts_range):
    for host in hosts_range:
        if ping(host):
            # print(f"Host {host} is up")
            Share.host_up_counter += 1
            hostname = socket.gethostbyaddr(host)[0]
            hosts_up.append((host, hostname))
        else:
            # print(f"Host {host} is down")
            Share.host_down_counter += 1

if __name__ == "__main__":
    net_ip_input = input("Inserisci indirizzo IP della rete [---.---.---.---]: ")
    sub_mask_input = input("Inserisci indirizzo della subnet mask [---.---.---.---]: ")
    intervals = 32
    threads = []

    ip_list = find_hosts_in_net(net_ip_input, sub_mask_input)

    chunk_size = len(ip_list) // intervals

    for i in range(intervals):
        start = i * chunk_size
        end = len(ip_list) if i == intervals - 1 else (i + 1) * chunk_size # si evita di perdere IP nel caso in cui len(ip_list) non sia perfettamente divisibile per intervals, percià all'ulitmo thread vengono assegnati anche gli IP rimanenti
        chunk = ip_list[start:end] # estrae una sottolista da ip_list (da start ad end), slicing operation
        thread = Thread(target=ping_host, args=(chunk,))
        thread.start()
        # print(f"Thread partito")
        threads.append(thread)

    for t in threads:
        t.join()

    print("\n--- REPORT ---")
    print(f"\nHost attivi: {Share.host_up_counter}")
    for host, hostname in hosts_up:
        print(f"Host Up: {host} - ({hostname})")
    print(f"\nHost non raggiungibili: {Share.host_down_counter}")