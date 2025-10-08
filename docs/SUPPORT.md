# Additional Tools & Commands to Facilitate elrond Analysis

Additional commands and tools to help get data ready for elrond<br><br>
<!-- TABLE OF CONTENTS -->
# Table of Contents

* [Preparing Disk Images](#Preparing-Disk-Images)
    * [Merging Multiple VMDK Files](#Merging-multiple-VMDK-Files)
    * [Convert DMG to E01](#Convert-DMG-to-E01)
* [Preparing Memory Images](Preparing-Memory-Images)
    * [Capturing Memory](#Capturing-Memory)
    * [Creating Symbol Tables (volatility3)](#Creating-Symbol-Tables-volatility3)
    * [Creating Profiles (volatility2.6)](#Creating-Profiles-volatility26)
* [Exporting VM as OVA](#Exporting-VM-as-OVA)
* [Appendix](#Appendix)
<br><br>

# Preparing Disk Images

## Merging multiple VMDK Files
* VMware Fusion

`/Applications/VMware\ Fusion.app/Contents/Library/vmware-vdiskmanager -r <location of virtual machine>.vmwarevm/Virtual\ Disk.vmdk -t 0 <new disk name>.vmdk`
* VMware Workstation

`C:\Program Files (x86)\VMware\VMware Player\vmware-vdiskmanager.exe -r <location of virtual machine>.vmwarevm\VirtualDisk.vmdk -t 0 <new disk name>.vmdk`

<br><br>

## Convert DMG to E01
If you have collected a macOS disk image in the form of a DMG, you can convert it into E01. Note, this can only be done on a macOS device (preferably not the same host where the disk was acquired).<br>
`brew install libewf`<br>
>
`hdiutil attach -nomount <filename>.dmg`<br>
>
`diskutil list`
 * Confirm device name which DMG has been mounted<br>

`ewfacquire -t evidence -v /dev/diskN`
 * Create evidence.E01 from /dev/diskN (N being the number it has been assigned - usually 3 or 4 but depends on how many additional disks or images are mounted)<br>
 * Adjust 'Evidence segment file size' to a value larger then the size of the DMG - this forces it to create a single E01 file as opposed to multiple<br>

`hdiutil detach /dev/disk4`

<br><br>


# Preparing Memory Images

## Capturing Memory
### macOS
* Download osxpmem from https://github.com/cyberg3cko/elrond/tree/main/tools/<br>

`sudo chown -R root:wheel osxpmem.app/ && sudo chmod +x osxpmem.app/osxpmem && sudo osxpmem.app/osxpmem -o mem.aff4 && sudo osxpmem.app/osxpmem -e /dev/pmem -o mem.raw mem.aff4`
<br>
### Linux
* Download avml from https://github.com/cyberg3cko/elrond/tree/main/tools/<br>

` sudo chmod +x avml && sudo ./avml $(uname -r).mem`

<br>

## Creating Symbol Tables (volatility3)
### Linux
#### Analysis Machine
* Download relevant debug symbol and execute the following commands (relevant to your distro):<br>

Obtain the relevant debug symbol<br>
`wget <debugsymbol>`
* RHEL: https://access.redhat.com/solutions/9907<br>
`yum install <path-to-debug-package> /tmp/`<br>
* Ubuntu: http://ddebs.ubuntu.com/ubuntu/pool/main/l/linux/<br>
`dpkg -x <path-to-debug-package> /tmp/`<br><br>

Copy created symbol table to Analysis Machine<br>
`sudo ./dwarf2json linux --elf /tmp/usr/lib/debug/boot/<downloaded-ddeb>.ddeb > .../volatility3/volatility3/symbols/linux/<downloaded-ddeb>.json`<br>

See Appendix for information on additional Linux distros<br><br><br>


## Creating Profiles (volatility2.6)
### macOS
#### Target Machine
* Identify the relevant Kernel for the version of macOS you are analysing<br><br>

#### Analysis Machine
* Download the relevant Kernel Debug Kit: http://developer.apple.com/hardwaredrivers<br>
* Download volatility3 from https://github.com/cyberg3cko/elrond/tree/main/tools/<br>

`unzip volatility3.zip`<br>
>
`dwarfdump -arch x86_64 /Library/Developer/KDKs/KDK_<MACOSXVERSION>_16D32.kdk/System/Library/Kernels/kernel.dSYM > <MACOSXVERSION>_x64.dwarfdump`<br>
>
`python tools/mac/convert.py <MACOSXVERSION>.dwarfdump converted-<MACOSXVERSION>_x64.dwarfdump`<br>
>
`python tools/mac/convert.py converted-<MACOSXVERSION>_x64.dwarfdump > 10.12.3.64bit.vtypes`<br>
>
`dsymutil -s -arch x86_64 /Library/Developer/KDKs/KDK_<MACOSXVERSION>_16D32.kdk/System/Library/Kernels/kernel > <MACOSXVERSION>.64bit.symbol.dsymutil`<br>
>
`zip <MACOSXVERSION>.64bit.zip <MACOSXVERSION>.64bit.symbol.dsymutil <MACOSXVERSION>.64bit.vtypes`<br>
>
`cp <MACOSXVERSION>.64bit.zip volatility/plugins/overlays/mac/`

<br>


### Linux
#### Target Machine
* Identify the relevant Kernel for the version of Linux you are analysing<br>

`uname -r`<br>
>
`cd Downloads/ && sudo apt-get install build-essential && sudo apt-get install dwarfdump && git clone https://github.com/volatilityfoundation/volatility.git && cd volatility/tools/linux/ && sudo make -C /lib/modules/$(uname -r)-generic/build/ CONFIG_DEBUG_INFO=y M=$PWD modules && sudo rm -rf module.dwarf && sudo dwarfdump -di ./module.o > module.dwarf && sudo zip Ubuntu64-$(uname -r)-generic.zip module.dwarf /boot/System.map-$(uname -r)-generic && ls -lah`

<br><br>

### Analysis Machine
`cp [RHEL|Ubuntu]64-$(uname -r).zip volatility/plugins/overlays/linux/`<br>

* Download volatility from https://github.com/cyberg3cko/elrond/tree/main/tools/<br>

`sudo apt-get install build-essential && sudo apt-get install dwarfdump`<br>
>
`unzip volatility.zip && sudo rm -rf __MACOSX/ && cd volatility/tools/linux/ && HOSTNAME=$(uname -r)`<br>
>
`sudo make -C /lib/modules/$(uname -r)/build/ CONFIG_DEBUG_INFO=y M=$PWD modules`<br>
>
`sudo rm -rf module.dwarf && sudo dwarfdump -di ./module.o > module.dwarf`<br>
>
`sudo zip [RHEL|Ubuntu]64-$(uname -r).zip module.dwarf /boot/System.map-$(uname -r)`<br>

<br><br><br>

# Exporting VM as OVA
* VMware Fusion

`/Applications/VMware\ Fusion.app/Contents/Library/VMware\ OVF\ Tool/./ovftool  --acceptAllEulas <location of virtual machine>.vmwarevm/<name of virtual machine>.vmx <name of virtual machine>.ova`

<br><br><br>

# Appendix
### Additional Linux Distro debuginfo
Required for volatility3 symbol tables, you will need to obain the relevant debuginfo and then install it in accordance with your Linux distro<br>
* CentOS: http://debuginfo.centos.org<br>
* SUSE: http://blog.dynofu.me/post/2015/08/31/linux-kernel-dbuginfo.html<br>
* Debian: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=365349<br>
* Fedora: https://fedoraproject.org/wiki/Packaging:Debuginfo<br>
* Oracle UEK: https://oss.oracle.com/ol6/debuginfo/<br><br>


### Building avml (Analysis Machine)
**Only required if execution of avml fails**<br>
`sudo mkdir /tmp/make_avml && sudo cd /tmp/make_avml && sudo apt-get install musl-dev musl-tools musl && sudo chmod 777 -R /tmp && curl https://sh.rustup.rs -sSf | sh -s -- -y && sudo snap install rustup --classic && rustup install stable && rustup target add x86_64-unknown-linux-musl && cargo new avml-main --bin && cd avml-main/ && cargo build --release --target x86_64-unknown-linux-musl && cp target/x86_64-unknown-linux-musl/release/avml <output_directory>`<br>
>
`cd target/x86_64-unknown-linux-musl/release/` (directory path might be slightly different)

<br>

### Pre-created Profiles (volatility2.6)

For a full list/repository of currently developed profiles for volatility2.6 please visit https://github.com/cyberg3cko/profiles
Of course, you develop your own, please adhere to the following naming conventions:
* Uploading to GitHub (directory structure):
    * **profiles -> Mac -> 10.11 -> ElCapitan_10.11.1_15B42.zip**
    * **profiles -> Linux -> x64 -> Ubuntu1010[-4.4.0-203-generic].zip**
* Importing into volatility locally (.../volatility/plugins/overlays/[mac|linux]/):
    * **10.11/ElCapitan_10.11.1_15B42.zip**
    * **LinuxUbuntu1010[-4.4.0-203-generic]x64.zip**
