## OpenWrt-ConfigVisualizer
This script is a translation layer that takes standard OpenWrt config files and outputs text that can be passed to [Kroki](https://kroki.io) which will then generate a image in png/svg/pdf format, showing network interfaces, subnets and clients.
(Kroki is using [nwdiag](https://github.com/blockdiag/nwdiag) to generate the image.
## Usage

Put NetworkDiagram.py in the same folder as these config files from your OpenWrt device
````
/etc/config/network
/etc/config/dhcp
````
Optionally also create a file named "hosts" in the same folder, and populate it in this format
````
hostname1 IP1
hostname2 IP2
hostname3 IP3
````
Run the python script
````
python NetworkDiagram.py
````
which will output something like tihs
````
nwdiag{Internet[shape=cloud];Internet -- OpenWrt;
  network LAN {
    address = "192.168.1.x/24";
    OpenWrt [address = "192.168.1.1"];
    PC [address = "192.168.1.10"];
    Server [address = "192.168.1.25"];
  }
  network WireGuard_network {
    address = "10.0.100.1";
    OpenWrt [address = "10.0.100.1"];
    Laptop [address = "10.0.100.2"];
    Phone [address = "10.0.100.3"];
  }
}
````
This output can be used by Kroki to generate your image. Either directly on [kroki.io](https://kroki.io) or by running Kroki locally, for example by using the official [Docker image](https://hub.docker.com/r/yuzutech/kroki).
The final result will be something like this:
![image](https://github.com/user-attachments/assets/514139c8-6a9d-489f-afdd-34639d344ee7)
