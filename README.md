<p align="center">
  <a href="https://github.com/cyberg3cko/elrond"><img src="elrond.jpg" alt="Logo" width="600" height="220"></a>
  <p align="center">
    Accelerating the collection, processing, analysis and outputting of digital forensic artefacts.
    <br><br>
    <a href="https://mit-license.org"><img src="https://img.shields.io/github/license/cyberg3cko/elrond" alt="License: MIT"></a>
    <a href="https://github.com/cyberg3cko/elrond/issues"><img src="https://img.shields.io/github/issues/cyberg3cko/elrond" alt="Issues"></a>
    <a href="https://github.com/cyberg3cko/elrond/network/members"><img src="https://img.shields.io/github/forks/cyberg3cko/elrond" alt="Forks"></a>
    <a href="https://github.com/cyberg3cko/elrond/stargazers"><img src="https://img.shields.io/github/stars/cyberg3cko/elrond" alt="Stars"></a>
    <a><img src="https://img.shields.io/badge/subject-DFIR-red" alt="Subject"></a>
    <a><img src="https://img.shields.io/github/last-commit/cyberg3cko/elrond" alt="Last Commit"></a>
    <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
    <br><br>
  </p>
</p>

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About](#about)
  - [Wild West Hackin' Fest 2023](#wild-west-hackin-fest-2023)
  - [Related Projects](#related-projects)
- [Configuration](#configuration)
  - [SIFT-elrond (recommended)](#sift-elrond-recommended)
  - [Self-build](#self-build)
- [Usage](#usage)
  - [Collect (-C)](#collect--c)
  - [Gandalf (-G)](#gandalf--g)
  - [Reorganise (-R)](#reorganise--r)
  - [Support](#support)
- [Artefacts](#artefacts)
  - [Windows](#windows)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Notices](#notices)
- [Acknowledgements](#acknowledgements)

<br><br>

## About

elrond has been created to help fellow digitial forensicators with the identification, extraction, collection, processing, analysis and outputting of forensic artefacts from (up to 20 paritions for) Windows E01 or VMDK, macOS DMG/E01 or VMDK, Linux dd or VMDK disk images as well as raw memory images and previously collected artefacts which can all be outputted into Splunk. I have spent many an incident repeating the same processes by mounting, collecting (mainly Windows) forensic artefacts and then attempting to correlate them together with other data sources and artefacts. Thus, as mentioned above elrond has been built to consolidate those seperate processes into one single script helping to accerlate and automate these otherwise repetitive, tedious and often occasionally-referenced commands. As elrond outputs the artefact information as either CSV or JSON, they can be processed by many commonly-used log file analysis tools, consequently, elrond does have the capability to stand up a local [Splunk](https://www.splunk.com/) (with acompanying [app](https://splunkbase.splunk.com/app/6606/)) or [elastic](https://www.elastic.co/) instance, whereby the artefacts are automatically assigned and aligned with the [MITRE ATT&CK® Framework](https://attack.mitre.org/). In addition, elrond can also populate a local [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) instance providing a visual representation of potential attack techniques leveraged as part of said incident.<br>
Additional features include image and file hashing, metadata extraction, file recovery and carving, AV scanning, IOC extraction, keyword searching and timelining.
<br>

It is important to note that elrond utilises many existing tools which have been built by other developers. elrond does do custom structuring of the outputted data but the conversion of the data is done by the other aforementioned toolsets.

### Wild West Hackin' Fest 2023

I presented elrond, at [Wild West Hackin' Fest 2023](https://wildwesthackinfest.com) as part of the Toolshed Talks.

[![Tool Shed Demo: ELROND | Ben Smith | WWHF 2023](https://img.youtube.com/vi/vjSHPhDPlks/0.jpg)](https://www.youtube.com/watch?v=vjSHPhDPlks "Tool Shed Demo: ELROND | Ben Smith | WWHF 2023")
- [Slidedeck](https://github.com/cyberg3cko/elrond/blob/main/elrond.pdf)
<br>

### Related Projects

elrond is responsible for the analysis-side of digital forensics, but what about acquisition? An acompanying script called [gandalf](https://github.com/cyberg3cko/gandalf) can be deployed (locally or remotely) on either Windows (using [PowerShell](https://learn.microsoft.com/en-us/powershell/)), Linux, or macOS (using [Python](https://www.python.org) or [bash]()) hosts to acquire forensic artefacts. 
<br><br><br>

## Configuration

### SIFT-elrond (recommended)

> Download the respective elrond OVA; the latest version of SIFT (20.04) or Ubuntu (22.04) with all of the elrond software packages, pre-installed.
  - For **x64**, download [SIFT-elrond](https://1drv.ms/u/s!Asg_rIbKaSxrgcTPRr4bgy8RdQhTnMk?e=xhiaaV) OVA (20.04)
    - `sansforensics:forensics`
  - For **ARM**, download [elrond](https://1drv.ms/u/s!Asg_rIbKaSxrgcWiQxIrP9mLAJWgLuI?e=RIJesL) archive (22.04)
    - `elrond:elrond`
> *Neither OVA contains the NSRL dataset; execute [nsrl.sh](https://github.com/cyberg3cko/elrond/blob/main/elrond/tools/config/scripts/nsrl.sh) and follow instructions to download.*<br>
>
> It is recommended to run [/opt/elrond/update.sh](https://github.com/cyberg3cko/elrond/blob/main/elrond/update.sh) which will download and configure the **latest version of elrond** onto your existing system.
<br>

### Self-build

**Download Virtual Machine**<br>
> There are several software package required for using elrond. Almost all of them are contained within the [SANS SIFT Worksation](https://www.sans.org/tools/sift-workstation/) virtual machine OVA. For the software which is not included ([make.sh](https://github.com/cyberg3cko/elrond/blob/main/make.sh)) installs and configures the additional software required for all potential functionality leveraged by elrond (volatility3, apfs-fuse, ClamAV etc.).
- For **x64** download [SANS SIFT Workstation](https://digital-forensics.sans.org/community/downloads) (20.04 LTS)
- For **ARM** download [Ubuntu 22.04](https://cdimage.ubuntu.com/jammy/daily-live/current/)
<br>

**Configure**<br>
Follow instructions in [CONFIG.md](https://github.com/cyberg3cko/elrond/blob/main/elrond/CONFIG.md)
> *You will only need to run the make.sh script once, per 'elrond VM' instance; if you encounter errors with [CONFIG.md](https://github.com/cyberg3cko/elrond/blob/main/elrond/CONFIG.md), individual scripts for each of the software packages are contained in [.../elrond/elrond/tools/config/scripts/](https://github.com/cyberg3cko/elrond/tree/main/elrond/tools/config/scripts/)*
<br>

## Usage

`python3 elrond.py <case_id> <directory> [<output_directory>] [-h] [-AaBCcDEGIiMmNnPQqRSsTtUuVXZ] [-K <keyword_file>] [-Y <yara_dir>] -F (include|exclude):[<include/exclude_file>]`
<br>

### Collect (-C)<br>
**Examples**<br>

- Invoking DBM (-B) flag (instead of using -acINoPQqUVv), Process (**-P**) index artefacts in Splunk (**-S**) and conduct File Collection (-F) with inclusion list<br>

`python3 elrond.py case_name /path/to/disk/images -BCPS  -F include:./include_file.txt`

- Automatically (**-a**) and super-quietly (**-Q**) Collect (**-C**), Process (**-P**), Analyse (**-A**) and index artefacts (including memory (**-M**)) in Splunk (**-S**)<br>

`python3 elrond.py case_name /path/to/disk_and_memory/images -aqQvVMCPAS`

- Very verbosely (**-V**), automatically (**-a**), super-quietly (**-Q**) Collect (**-C**), Process (**-P**) and conduct IOC Extraction (**-I**)<br>

`python3 elrond.py case_name /path/to/disk/images -avVqQCPI`
<br><br>

### Gandalf (-G)<br>
**Examples**<br>

- Automatically (**-a**) and superquietly (**-Q**) Process (**-P**), Analyse (**-A**) and index artefacts in Splunk (**-S**) (acquired using [gandalf](https://github.com/cyberg3cko/gandalf))<br>

`python3 elrond.py case_name /path/to/disk/images -aqvVGPAS`

- Invoking DBM (-B) flag (instead of using -acINoPQqUVv), Process (**-P**) index artefacts in Splunk (**-S**) and conduct Keyword Searching (-K <file_name>)<br>

`python3 elrond.py case_name /path/to/disk/images -BGPS -K keywords.txt`
<br><br>


### Reorganise (-R)<br>
**Examples**<br>

- Automatically (**-a**) and quietly (**-q**) Process (**-P**), Analyse (**-A**) and index artefacts in Splunk (**-S**) (reorganise previously collected disk artefacts (**-R**))<br>

`python3 elrond.py case_name /path/to/disk/images -aqvVRPAS`

- Invoking DBM (-B) flag (instead of using -acINoPQqUVv), Process (**-P**) index artefacts in Splunk (**-S**) and conduct Yara Searching (-Y <yara_dir>)<br>

`python3 elrond.py case_name /path/to/disk/images -BRPS -Y <directory/of/yara/files>`
<br><br>

### Support

See [SUPPORT.md](https://github.com/cyberg3cko/elrond/blob/main/elrond/SUPPORT.md) for a list of commands and additional third-party tools to help with preparing images or data for elrond.
<br><br>

## Artefacts

Below is a list of all the artefacts collected and processed from the respective operating systems.

### Windows

- C:\\$MFT
- C:\\$LogFile
- C:\\$ObjId
- C:\\$Recycle.Bin
- C:\\$Reparse
- C:\\$UsnJrnl
- C:\\Windows\\AppCompat\\Programs\\RecentFileCache.bcf
- C:\\Windows\\AppCompat\\Programs\\Amcache.hve
- C:\\Windows\\inf\\setupapi.dev.log
- C:\\Windows\\Prefetch\\*.pf
- C:\\Windows\\System32\\config\\SAM
- C:\\Windows\\System32\\config\\SAM.LOG
- C:\\Windows\\System32\\config\\SAM.LOG1
- C:\\Windows\\System32\\config\\SAM.LOG2
- C:\\Windows\\System32\\config\\SECURITY
- C:\\Windows\\System32\\config\\SECURITY.LOG
- C:\\Windows\\System32\\config\\SECURITY.LOG1
- C:\\Windows\\System32\\config\\SECURITY.LOG2
- C:\\Windows\\System32\\config\\SOFTWARE
- C:\\Windows\\System32\\config\\SOFTWARE.LOG
- C:\\Windows\\System32\\config\\SOFTWARE.LOG1
- C:\\Windows\\System32\\config\\SOFTWARE.LOG2
- C:\\Windows\\System32\\config\\SYSTEM
- C:\\Windows\\System32\\config\\SYSTEM.LOG
- C:\\Windows\\System32\\config\\SYSTEM.LOG1
- C:\\Windows\\System32\\config\\SYSTEM.LOG2
- C:\\Windows\\System32\\winevt\\Logs\\*.evt(x)
- C:\\Windows\\System32\\wbem\\Repository\\
- C:\\Windows\\System32\\LogFiles\\WMI\\
- C:\\Windows\\System32\\LogFiles\\
- C:\\Users\\%USERPROFILE%\\NTUSER.DAT
- C:\\Users\\%USERPROFILE%\\UsrClass.DAT
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\ConnectedDevicesPlatform\\ActivitiesCache.db
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\ConnectedDevicesPlatform\\ActivitiesCache.db-shm
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\ConnectedDevicesPlatform\\ActivitiesCache.db-wal
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\History\\Content.IE5
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\History\\History.IE5
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\History\\Low\\
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\Temporary Internet Files\\
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\Temporary Internet Files\\Content.Outlook\\
- C:\\Users\\%USERPROFILE%\\AppData\\Local\\Mozilla\\Firefox\\Profiles\\
- C:\\Users\\%USERPROFILE%\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\AutomaticDestinations\\
- C:\\Users\\%USERPROFILE%\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\CustomDestinations\\
- C:\\Users\\%USERPROFILE%\\AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadline\\ConsoleHost_history.txt
- C:\\Users\\%USERPROFILE%\\Documents\\Outlook Files\\
- C:\\Users\\%USERPROFILE%\\*
<br>

### Linux

- /.Trashes
- /etc/passwd
- /etc/shadow
- /etc/group
- /etc/hosts
- /etc/crontab
- /etc/security
- /etc/systemd
- /etc/modules-load
- /home/%USERPROFILE%/
- /home/%USERPROFILE%/.bash_aliases
- /home/%USERPROFILE%/.bash_history
- /home/%USERPROFILE%/.bash_logout
- /home/%USERPROFILE%/.bashrc
- /home/%USERPROFILE%/.bash_session
- /home/%USERPROFILE%/.config/autostart/
- /home/%USERPROFILE%/.config/google-chrome/%DIR%/History
- /home/%USERPROFILE%/.local/share/Trash/files
- /home/%USERPROFILE%/.local/share/keyrings/
- /home/%USERPROFILE%/.local/share/recently-used.xbel
- /home/%USERPROFILE%/.mozilla/firefox/%DIR%/places.sqlite
- /home/%USERPROFILE%/.ssh
- /home/%USERPROFILE%/.thunderbird/.default
- /home/%USERPROFILE%/.thunderbird/global-messages-db.sqlite
- /home/%USERPROFILE%/.thunderbird/places.sqlite
- /home/%USERPROFILE%/.thunderbird/downloads.sqlite
- /home/%USERPROFILE%/.thunderbird/panacea.dat
- /root/.bash_aliases
- /root/.bash_history
- /root/.bash_logout
- /root/.bashrc
- /root/.bash_session
- /root/.local/share/keyrings/
- /root/.ssh
- /tmp/*
- /usr/lib/systemd/user/*.service
- /usr/lib/systemd/user/*.target
- /usr/lib/systemd/user/*.socket
- /var/cache/cups/job.*
- /var/cups/job.*
- /var/log
- /var/vm/sleepimage
- /var/vm/swapfile
<br>

### macOS

- /.Trashes
- /Library/Logs
- /Library/Preferences
- /Library/LaunchAgents
- /Library/LaunchDaemons
- /Library/StartupItems
- /System/Library/Preferences
- /System/Library/LaunchAgents
- /System/Library/LaunchDaemons
- /System/Library/StartupItems
- /Users/%USERPROFILE%/
- /Users/%USERPROFILE%/.bash_aliases
- /Users/%USERPROFILE%/.bash_history
- /Users/%USERPROFILE%/.bash_logout
- /Users/%USERPROFILE%/.bashrc
- /Users/%USERPROFILE%/.bash_session
- /Users/%USERPROFILE%/.ssh
- /Users/%USERPROFILE%/.Trash/
- /Users/%USERPROFILE%/Library/keychains/.keychain-db
- /Users/%USERPROFILE%/Library/Mail/*.plist
- /Users/%USERPROFILE%/Library/Preferences/*.plist
- /Users/%USERPROFILE%/Library/Safari/*.plist
- /Users/%USERPROFILE%/Library/Safari/History.db
- /Users/%USERPROFILE%/Library/Application Support/Google/Chrome/Default/
- /Users/%USERPROFILE%/Library/Application Support/Firefox/Profiles/
- /etc/passwd
- /etc/shadow
- /etc/group
- /etc/hosts
- /etc/crontab
- /etc/security
- /tmp/*
- /var/log
<br><br>

### Notices

If you notice 'nixCommand' or 'nixProcess' in files processed from a Windows OS, this is somewhat intentional. I debated with myself whether to try and change these to 'WinCommand' and 'WinProcess', respectively but also considered the situation of Windows Subsystem for Linux (WSL) being installed. As a result, I have left them as they are. If you know of a way to identify whether a file belongs inside the Linux element of WSL based on file path, file type, file content etc. please raise an [issue](https://github.com/cyberg3cko/elrond/issues) and let me know.
<br><br><br>


<!-- ACKNOWLEDGEMENTS -->

## Acknowledgements

- [Joff Thyor](https://www.blackhillsinfosec.com/team/joff-thyer/)
- [alexandercarruthers](https://github.com/alexandercarruthers)
- [SANS](https://www.sans.org)
- [Harbingers LLC](https://uspto.report/company/Harbingers-L-L-C)<br><br>
- Tooling
  - [joachimmetz](https://github.com/joachimmetz)
  - [Harlan Carvey](https://github.com/hcarvey)
  - [@JRick_3](https://obscurite-hateblo-jp.translate.goog/entry/2022/02/28/003408?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en-US&_x_tr_pto=wapp)
  - [williballenthin](https://github.com/williballenthin)
  - [dkovar](https://github.com/dkovar)
  - [Richard Penman](https://github.com/richardpenman)
  - [harelsegev](https://github.com/harelsegev/INDXRipper)
  - [KStrike](https://github.com/brimorlabs/KStrike)
  - [srum-dump](https://github.com/MarkBaggett/srum-dump)
  - [mnrkbys](https://github.com/mnrkbys/macosac)
  - [The Volatility Foundation](https://github.com/volatilityfoundation)
  - [AVML](https://github.com/microsoft/avml)
  - [Jonathon Poling](https://ponderthebits.com/2017/02/osx-mac-memory-acquisition-and-analysis-using-osxpmem-and-volatility/)
  - [@binaryz0ne](https://www.binary-zone.com/2019/06/20/acquiring-linux-memory-using-avml-and-using-it-with-volatility/)
  - [JPCERTCC](https://github.com/JPCERTCC/Windows-Symbol-Tables)
  - [John - Python Awesome](https://pythonawesome.com/windows-symbol-tables-for-volatility-3-in-python/)<br><br>
- Documentation
  - [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
  - [hatchful](https://hatchful.shopify.com)
  - [Image Shields](https://shields.io)<br><br>
- Theme &amp; Artwork
  - [J.R.R. Tolkien](https://en.wikipedia.org/wiki/J._R._R._Tolkien)
  - [Peter Jackson](https://twitter.com/ReaPeterJackson)
  - [ASCII Text Generator](https://textkool.com/en/ascii-art-generator?hl=default&vl=default&font=Red%20Phoenix&text=Your%20text%20here%20)
  - [ASCII Art Generator](https://www.ascii-art-generator.org)
  - [ASCII Art](http://www.asciiworld.com/-Lord-of-the-Rings-.html)
  - [SIFT-elrond Desktop background](https://www.hdwallpaper.nu/wp-content/uploads/2015/04/rings_the_lord_of_the_rings_one_ring_hd_wallpaper.jpg)
  - [lómi](https://www.elfdict.com/w/cloud)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
