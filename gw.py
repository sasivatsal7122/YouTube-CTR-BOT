import subprocess
import sys

def change_gateway(gateway):
    proc = subprocess.Popen(['sudo','-S','ip', 'route', 'flush','0/0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=b'Success01!\n')
    proc = subprocess.Popen(['sudo','-S','route', 'add', 'default','gw',gateway], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input=b'Success01!\n')
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gw.py <gateway>")
    else:
        gateway = sys.argv[1]
        status = change_gateway(f"192.168.2.{gateway}")
        if status == 0:
            print(f"Gateway changed to 192.168.2.{gateway}")
        else:
            print("Failed to change the gateway. Error code:", status)

