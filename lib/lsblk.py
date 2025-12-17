from os import name
import subprocess
import json
def get_disks_info():
    result = subprocess.run(
        ["lsblk", "-b", "-J"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)
    return data


def confirm_disk_exist(disk_name: str, disks_info: dict):
    for disk in disks_info['blockdevices']:
        
        if disk['name'] == disk_name:
            return True
    return False
        






disks_info = get_disks_info()

print(confirm_disk_exist("nvme0n1", disks_info))




