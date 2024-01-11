# secureblue

After rebasing to secureblue, the following steps are recommended.

## Set a GRUB password

*to be added*

## Create a separate wheel account for admin purposes

Creating a dedicated wheel user and removing wheel from your primary user helps prevent certain attack vectors:

https://www.kicksecure.com/wiki/Dev/Strong_Linux_User_Account_Isolation#LD_PRELOAD
https://www.kicksecure.com/wiki/Root#Prevent_Malware_from_Sniffing_the_Root_Password

1. ```adduser admin```
2. ```usermod -aG wheel admin```
3. ```gpasswd -d {your username here} wheel```
4. reboot

## Chromium Extension

1. Go to [uBlock Origin Lite](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh?pli=1) ([Why Lite?](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security))
2. Install it
3. In the extension's settings, make sure all of the lists under Default and Miscellaneous are checked (and at your preference, lists in the Annoyances section or country-specific lists)

