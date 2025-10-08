# elrond Configuration

[Prepare Virtual Machine](https://github.com/cyberg3cko/elrond/blob/main/elrond/VIRTUALMACHINE.md)<br>

---
<br>

⚠️ _The following script will partition and format /dev/sdb. If you have not configured the second HDD as recommended above, it may delete data if you have another drive mounted. You can change this location, by editing the [init.sh](https://github.com/cyberg3cko/elrond/blob/main/elrond/tools/scripts/init.sh) script_<br><br>
<!-- sudo passwd elrond && sudo apt install git -y && sudo hostname elrond -->
`sudo git clone https://github.com/cyberg3cko/elrond.git /opt/elrond && sudo /opt/elrond/./make.sh`<br>
  - &darr; &darr; `ENTER c g` *(apfs-fuse on x64 architecture only)*<br>

---
<br>

[Revert Virtual Machine](https://github.com/cyberg3cko/elrond/blob/main/elrond/VIRTUALMACHINE.md)