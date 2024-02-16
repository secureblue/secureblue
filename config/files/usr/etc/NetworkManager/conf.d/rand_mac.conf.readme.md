# Random MAC Address Settings

The `rand_mac.conf` is a configuration file to let network manager using random mac address when possible.
See https://www.networkmanager.dev/docs/api/latest/NetworkManager.conf.html 
or `man NetworkManager.conf` for detailed official documentation on the configurations.

### Random MAC Address For Scanning

`wifi.scan-rand-mac-address=yes` use a random mac address when scanning networks,
this is already the default on fedora systems.

### Random MAC Address For Connection

`ethernet.cloned-mac-address=random` and `wifi.cloned-mac-address=random` 
will generate a random mac address for **each connection** to network.

The `random` setting is different from `stable` setting:
for `stable`, the system will generate a permanent mac address and associate it with each network.
`stable` setting is useful when you are on a home/company network, 
where stable mac addresses are important for admin purposes.

You can manually change the random mac address setting to `stable` for individual networks in Gnome: 
`Setting > Wifi > Gear icon on the right of the network name > Identity > Cloned Mac Address`.
The global setting can also be changed by editing the `rand_mac.conf` file.