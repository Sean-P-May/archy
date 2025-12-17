
import subprocess
from models import SystemSettings

def install():
    if not vefity_internet():
        print("No Internet!")
        exit()

    #Keyboard layout
    subprocess.run(["loadkeys", "us"])

    #check_efi
    with open("/sys/firmware/efi/fw_platform_size") as f:
        value = f.read().strip() 
    if value != "64":
        print("architecture not supported by this install script.")
        exit()
    





def set_setup_disks():
    pass


def vefity_internet():
    command = ["ping", "-c", "1", "archlinux.org"]   # Linux/macOS
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0
