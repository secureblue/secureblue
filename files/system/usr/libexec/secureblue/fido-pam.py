#!/usr/bin/env python3

"""
Adding easy support for FIDO based authentication

arguements:
python3 fido-pam.py 2fa
    This requires fido2 and configured password for any authentication systemwide for pam, WHEN USERS have fido2 key for their account
    This script uses without-pam-u2f-nouserok to try and ensure users can login with password only if no fido2 is provided.

python3 fido-pam.py passwordless
    This allows using just fido2 authentication systemwide for pam.
    This allows you use use an impractically long backup password for your wheel user, and primarily manage
    your device via fido2 authentication.

Using subprocess with shell is unfortunate, but necessary for some parts
Sources:
https://developers.yubico.com/pam-u2f/
https://devblog.jpcaparas.com/use-your-yubikey-as-a-system-level-authentication-pam-module-on-fedora-40-457ae7375254
https://github.com/secureblue/secureblue/issues/809
https://docs.python.org/3/library/subprocess.html
https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess
https://github.com/Zer0CoolX/Fedora-KDE-Yubikey-U2F-2FA-Logins-Guide
https://www.mankier.com/8/authselect
https://docs.python.org/3/library/grp.html
"""

import sys
import subprocess
import datetime
import os
import grp
import pwd

# Entry point, parse arguements
def main():
    if (os.geteuid() != 0):
        print("This script must be run with root (run0).")
        exit(1)

    print("Before continuing please open a root terminal (via run0) in a seperate tab to potentially restore your old authselect local profile if needed.")
    input("Press Enter to continue...")

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = None

    if (mode == '2fa'):
        pam_auth(0)
    elif (mode == 'passwordless'):
        pam_auth(1)
    else:
        loop = 0
        while (loop == 0):
            pam_type = input("Chose between using FIDO2 authentication as a second factor or to replace passwords? [2fa/passwordless] \n Note for second factor, authselect will be configured to allow login if no yubikey is configured for the user.")
            if (pam_type == "2fa"):
                pam_auth(0)
                loop = 1
            elif (pam_type == "passwordless"):
                pam_auth(1)
                loop = 1
            elif ((pam_type == "exit") | (pam_type == "quit")):
                return
            else:
                print("Please use repond either \"2fa\", \"passwordless\", or \"exit\" to exit")
    return

#Handles authselect config and adding fido2 keys to users
def pam_auth(pam_type):
    # pam_type == 0 is 2fa
    # pam_type == 1 is passwordless

    ts = datetime.datetime.isoformat(datetime.datetime.now()) #Note datetime.now() creates datetime object, and .isoformat converts it to a string
    os.environ["time"] = ts

    result = subprocess.run(["run0","authselect","select", "local",f"--backup={ts}"], text=True, capture_output=True) # nosec
    if (result.returncode != 0):
        print(result.stderr)
        return
    
    print(f"A backup of your current authselect local profile has been created at /var/lib/authselect/backups/{os.getenv('time')}g.")
    print(f"If needed you can restore your old profile with this command \'authselect backup-restore /var/lib/authselect/backups/{os.getenv('time')}\'.")

    result = subprocess.run(["run0", "authselect", "enable-feature", "without-pam-u2f-nouserok"], text=True, capture_output=True) # nosec
    if (result.returncode != 0):
        print(result.stderr)
        return

    if (pam_type == 0):
        result = subprocess.run(["run0", "authselect", "enable-feature", "with-pam-u2f-2fa"], text=True, capture_output=True) # nosec
    elif (pam_type == 1):
        result = subprocess.run(["run0", "authselect", "enable-feature", "with-pam-u2f"], text=True, capture_output=True) # nosec
    if (result.returncode != 0):
        print(result.stderr)
        return

    print("Before continuing please plug in ONLY ONE fido2. (The utility used does not support more than one fido2 key at a time. To add more later use \'pamu2fcfg -n >> ~/.config/Yubico/u2f_keys\'")
    print("When your fido2 key blinks (if it supports PIV), touch it.")
    input("Press Enter to continue...")

    result = subprocess.run(["pamu2fcfg"], text=True, capture_output=True) # nosec
    if (result.returncode != 0):
        print(result.stderr)
        return
    os.environ["fido_key"] = result.stdout.strip()

    loop = 0
    # chmod of 644 for fido2 files is chosen so user can edit their own configured accepted fido2 keys, and other users can see them (as they are basically public keys) for ease of use
    while (loop == 0):
        key_choice = input("Do you want the currently logged user, all wheel users, or both to add the currently connected fido2 key to their authentication? [current,wheel,both]")
        if (key_choice == "current"):
            path = os.path.join(f"{os.getenv('HOME')}", ".config", "Yubico")
            os.makedirs(path, exist_ok=True)
            keyfile = os.path.join(path, "u2f_keys")
            with open(keyfile, "w") as f:
                f.write(f"{os.getenv('fido_key')}")
            os.chmod(keyfile, 0o644)
            os.chown(keyfile, pwd.getpwnam((f"{os.getenv('USER')}")).pw_uid, pwd.getpwnam((f"{os.getenv('USER')}")).pw_gid)
            loop = 1
        elif (key_choice == "wheel"):
            for user in (grp.getgrnam("wheel")[3]):
                home = (get_home_directory(user)) 
                if (home != None):
                    path = os.path.join(home, ".config", "Yubico")
                    os.makedirs(path, exist_ok=True)
                    keyfile = os.path.join(path, "u2f_keys")
                    with open(keyfile, "w") as f:
                        f.write(f"{os.getenv('fido_key')}")
                    os.chmod(keyfile, 0o644)
                    os.chown(keyfile, pwd.getpwnam(user).pw_uid, pwd.getpwnam(user).pw_gid)                
                else:
                    print(f"{user}'s home appears to not exist, no fido key has been configured for it.")
            loop = 1
        elif (key_choice == "both"):
            #Note currently logged in user being a wheel user is not a problem for this, as it will just overwrite fido_key again with the same data
            path = os.path.join(f"{os.getenv('HOME')}", ".config", "Yubico")
            os.makedirs(path, exist_ok=True)
            keyfile = os.path.join(path, "u2f_keys")
            with open(keyfile, "w") as f:
                f.write(f"{os.getenv('fido_key')}")
            os.chmod(keyfile, 0o644)
            os.chown(keyfile, pwd.getpwnam((f"{os.getenv('USER')}")).pw_uid, pwd.getpwnam((f"{os.getenv('USER')}")).pw_gid)
            for user in (grp.getgrnam("wheel")[3]):
                home = (get_home_directory(user)) 
                if (home != None):
                    path = os.path.join(home, ".config", "Yubico")
                    os.makedirs(path, exist_ok=True)
                    keyfile = os.path.join(path, "u2f_keys")
                    with open(keyfile, "w") as f:
                        f.write(f"{os.getenv('fido_key')}")
                    os.chmod(keyfile, 0o644)
                    os.chown(keyfile, pwd.getpwnam(user).pw_uid, pwd.getpwnam(user).pw_gid)                
                else:
                    print(f"{user}'s home appears to not exist, no fido key has been configured for it.")
            loop = 1
        else:
            print("Please use repond either \"current\", \"wheel\", or \"both\"")

    print("Congratulations!\nYour secureblue install is now configured to use fido2 PAM.\nNote that fido2 data that PAM uses has been added to ~/.config/Yubico/u2f_keys")
    print(f"Reminder: To restore the old authset use \'authselect backup-restore /var/lib/authselect/backups/{os.getenv('time')}\'")
    return

#Returns string of given username's home directory
def get_home_directory(username):
    try:
        user_info = pwd.getpwnam(username)
        return user_info.pw_dir
    except KeyError:
        return None  # User not found

if __name__ == "__main__":
    main()
