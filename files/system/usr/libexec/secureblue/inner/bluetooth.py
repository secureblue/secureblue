import os
import sys
import typing

BLUE_MOD_FILE: Final[str] = "/etc/modprobe.d/99-bluetooth.conf"
BLUE_MOD_TEXT: Final[str] = """install bluetooth /sbin/modprobe --ignore-install bluetooth
install btusb /sbin/modprobe --ignore-install btusb"""

def main():
    if len(sys.argv) != 2:
        return 1

    mode = sys.argv[1]
    match mode:
        case "off":
            with open(BLUE_MOD_FILE, "w", encoding="utf8") as fd:
                fd.write(BLUE_MOD_TEXT)
            os.chmod(BLUE_MOD_FILE, 0o644)
            print("Bluetooth has been disabled. Reboot for effect.")
            return 0
        case "on":
            os.remove(BLUE_MOD_FILE)
            print("Bluetooth has been enabled. Reboot for effect.")
            return 0
        case _:
            print("Invalid inner script argument.")
            return 1

if __name__ == "__main__":
    sys.exit(main())