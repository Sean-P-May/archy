
import subprocess
from typing import List, Optional
from getpass import getpass
import sys


# -------------------------
# Process helpers
# -------------------------

def run_process_exit_on_fail(
    process: List[str] | str,
    *,
    input: Optional[str] = None,
):
    if isinstance(process, str):
        process = process.split(" ")

    print(f"Running command: {' '.join(process)}")
    cp = subprocess.run(
        process,
        input=input,
        text=True,
        capture_output=True,
    )

    if cp.stdout:
        print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, file=sys.stderr, end="")

    if cp.returncode != 0:
        print(f"Error running: {' '.join(process)} (exit code {cp.returncode})", file=sys.stderr)
        sys.exit(1)


def chroot_process(
    process: List[str] | str,
    *,
    input: Optional[str] = None,
):
    if isinstance(process, str):
        process = process.split(" ")

    run_process_exit_on_fail(
        ["arch-chroot", "/mnt"] + process,
        input=input,
    )


# -------------------------
# Password prompting
# -------------------------


def prompt_password(label: str) -> str:
    while True:
        pw1 = getpass(f"{label}: ")
        pw2 = getpass("Confirm password: ")

        if not pw1:
            print("Password cannot be empty.")
        elif pw1 != pw2:
            print("Passwords do not match.")
        else:
            return pw1



# -------------------------
# Root handling
# -------------------------

def set_root_password(*, password: str | None = None):
    pw = password or prompt_password("Root password")
    chroot_process(
        ["chpasswd"],
        input=f"root:{pw}\n",
    )
    pw = None


def lock_root():
    chroot_process(["passwd", "-l", "root"])


# -------------------------
# User + sudo
# -------------------------

def create_user(username: str):
    chroot_process(["useradd", "-m", "-G", "wheel", username])


def set_user_password(username: str, *, password: str | None = None):
    pw = password or prompt_password(f"Password for {username}")
    chroot_process(
        ["chpasswd"],
        input=f"{username}:{pw}\n",
    )
    pw = None


def enable_wheel_sudo():
    chroot_process([
        "sed", "-i",
        r"s/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/",
        "/etc/sudoers"
    ])
