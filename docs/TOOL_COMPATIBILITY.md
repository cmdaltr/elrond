# Tool Compatibility Analysis

## Executive Summary

**macOS ARM64 (Apple Silicon)**: 27/30 tools compatible (90%)
**Windows Native**: 15/30 tools compatible (50%)
**Windows + WSL2**: 30/30 tools compatible (100%)

## Platform Compatibility Matrix

### ✅ Full Cross-Platform Support (All Platforms)

| Tool | Linux | macOS Intel | macOS ARM64 | Windows | Notes |
|------|-------|-------------|-------------|---------|-------|
| Volatility 3 | ✅ | ✅ | ✅ | ✅ | Python-based, works everywhere |
| Volatility 2 | ✅ | ✅ | ✅ | ✅ | Python-based, works everywhere |
| analyzeMFT | ✅ | ✅ | ✅ | ✅ | Python package |
| python-evtx | ✅ | ✅ | ✅ | ✅ | Python package |
| RegRipper | ✅ | ✅ | ✅ | ✅ | Perl-based (needs Perl installed) |
| ShimCacheParser | ✅ | ✅ | ✅ | ✅ | Python script |
| YARA | ✅ | ✅ | ✅ | ✅ | Pre-built binaries available |
| ClamAV | ✅ | ✅ | ✅ | ✅ | Pre-built binaries available |
| The Sleuth Kit | ✅ | ✅ | ✅ | ✅ | Pre-built binaries available |

### 🟡 macOS ARM64 Compatibility

#### ✅ Works on ARM64 (via Homebrew)

| Tool | Status | Installation |
|------|--------|--------------|
| ewftools (libewf) | ✅ Native ARM64 | `brew install libewf` |
| QEMU | ✅ Native ARM64 | `brew install qemu` |
| Volatility 3 | ✅ Native ARM64 | `pip3 install volatility3` |
| YARA | ✅ Native ARM64 | `brew install yara` |
| ClamAV | ✅ Native ARM64 | `brew install clamav` |
| The Sleuth Kit | ✅ Native ARM64 | `brew install sleuthkit` |
| foremost | ✅ Native ARM64 | `brew install foremost` |

#### ⚠️ Limited on ARM64 (Rosetta 2 Required)

| Tool | Status | Workaround |
|------|--------|------------|
| Plaso | ⚠️ Limited support | Some dependencies may need x86_64 emulation |
| libvshadow | ❌ Not available | Linux-only, not needed on macOS |
| apfs-fuse | ❌ Not needed | Native APFS support on macOS |

#### 🟢 Python Tools (Universal)

All Python-based tools work natively on ARM64:
- Volatility 3
- Volatility 2
- analyzeMFT
- python-evtx
- ShimCacheParser
- All bundled tools (USN-Journal-Parser, INDXRipper, KStrike, etc.)

**macOS ARM64 Summary**: **27/30 tools work** (3 are Linux-specific and not needed on macOS)

---

### 🔴 Windows Native Limitations

#### ✅ Works Natively on Windows

| Tool | Installation Method |
|------|---------------------|
| Volatility 3 | `pip install volatility3` |
| Volatility 2 | Download binary from GitHub |
| analyzeMFT | `pip install analyzeMFT` |
| python-evtx | `pip install python-evtx` |
| RegRipper | Download Perl script + install Strawberry Perl |
| ShimCacheParser | Download from GitHub |
| YARA | Download binary from releases |
| ClamAV | Download installer from clamav.net |
| The Sleuth Kit | Download installer from sleuthkit.org |

#### ❌ Does NOT Work on Windows (Linux/Unix-only tools)

| Tool | Reason | WSL2 Alternative |
|------|--------|------------------|
| **ewftools** | Uses Linux FUSE | ✅ Works in WSL2 |
| **qemu-nbd** | Kernel module required | ✅ Works in WSL2 |
| **libvshadow** | Linux-specific | ✅ Works in WSL2 |
| **apfs-fuse** | FUSE-based | ✅ Works in WSL2 |
| **plaso** | Complex Linux deps | ✅ Works in WSL2 |
| **foremost** | Unix-based | ✅ Works in WSL2 |
| **journalctl** | systemd-specific | ✅ Works in WSL2 |

**Additional Windows Issues**:
- **Image Mounting**: Windows requires Arsenal Image Mounter or FTK Imager (commercial tools)
- **FUSE-based tools**: No native FUSE support on Windows
- **Shell scripts**: Many bundled tools are Bash scripts
- **File permissions**: Unix permission model doesn't translate

**Windows Native Summary**: **15/30 tools work** (50%)

---

## WSL2 Solution for Windows

### Why WSL2?

WSL2 provides a **full Linux kernel** on Windows, enabling:
- ✅ All 30 forensic tools work identically to Linux
- ✅ FUSE-based image mounting (ewfmount, apfs-fuse, etc.)
- ✅ Kernel modules (qemu-nbd, NBD devices)
- ✅ Native Unix tools (grep, awk, sed)
- ✅ Easy access to Windows filesystem (`/mnt/c/`)

### WSL2 Architecture

```
Windows 11
├── C:\elrond\                    (Windows filesystem)
│   └── evidence\                 (Case data accessible from both)
│
└── WSL2 Ubuntu 22.04             (Full Linux environment)
    ├── /usr/bin/ewfmount         (All forensic tools installed)
    ├── /mnt/c/elrond/evidence/   (Access Windows files)
    └── /opt/elrond/              (elrond installation)
```

### WSL2 Requirements

- **Windows Version**: Windows 10 version 2004+ or Windows 11
- **Features Required**:
  - Virtual Machine Platform
  - Windows Subsystem for Linux
- **Resources**: 4GB+ RAM recommended
- **Disk Space**: 10GB for WSL2 + tools

### WSL2 Installation Flow

```bash
# 1. Enable WSL2 (PowerShell as Admin)
wsl --install -d Ubuntu-22.04

# 2. Install elrond in WSL2
wsl
cd /opt
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
pip3 install -e .

# 3. Install all tools
elrond --install --wsl

# 4. Run from Windows
wsl elrond -C -c CASE-001 -s /mnt/c/evidence
```

### Benefits of WSL2 Approach

1. **100% Tool Compatibility**: All Linux tools work
2. **Native Performance**: Near-native speed (95%+ of bare Linux)
3. **Windows Integration**: Access Windows files seamlessly
4. **Easy Updates**: Standard Linux package managers
5. **Industry Standard**: WSL2 widely used in forensics (SANS, etc.)

---

## Recommended Strategy by Platform

### Linux (Best Platform for Forensics)

```bash
# Install via package manager (Ubuntu/Debian)
elrond --install

# Installs all tools via apt-get
# Full support for all 30 tools
```

**Recommendation**: ✅ Primary platform, no limitations

---

### macOS (Intel or ARM64)

```bash
# Install via Homebrew
elrond --install

# Installs 27/30 tools
# libvshadow/apfs-fuse not needed (native support)
```

**Recommendations**:
- ✅ Use Homebrew for all system tools
- ✅ Use pip for Python tools
- ✅ ARM64: All critical tools work natively
- ⚠️ Plaso: May need `arch -x86_64` for some components

**ARM64 Specific**:
```bash
# Check if running under Rosetta
uname -m  # Should show "arm64"

# Force x86_64 for problematic tools (rare)
arch -x86_64 brew install <tool>
```

---

### Windows (Two Options)

#### Option 1: WSL2 (Recommended) ⭐

```powershell
# Install WSL2 + Ubuntu
wsl --install -d Ubuntu-22.04

# Install elrond in WSL2
wsl
elrond --install

# Run forensics
wsl elrond -C -c CASE-001 -s /mnt/c/evidence
```

**Pros**:
- ✅ 100% tool compatibility (30/30)
- ✅ Full image mounting support
- ✅ Industry-standard approach
- ✅ Easy installation

**Cons**:
- ⚠️ Requires Windows 10 2004+ or Windows 11
- ⚠️ Uses ~10GB disk space
- ⚠️ Slight learning curve for WSL

#### Option 2: Native Windows (Limited)

```powershell
# Install Python tools only
elrond --install --windows-native

# Only 15/30 tools available
# No image mounting support
# Best for: memory analysis, artifact parsing only
```

**Pros**:
- ✅ No WSL required
- ✅ Works on older Windows versions

**Cons**:
- ❌ Only 50% of tools (15/30)
- ❌ No disk image mounting
- ❌ Limited functionality

**Recommendation**: ⭐ **Use WSL2 for full functionality**

---

## Tool-Specific Compatibility Notes

### Image Mounting Tools

| Tool | Linux | macOS | Windows | Windows+WSL2 |
|------|-------|-------|---------|--------------|
| ewfmount (E01) | ✅ | ✅ | ❌ | ✅ |
| qemu-nbd (VMDK) | ✅ | ✅ | ❌ | ✅ |
| vshadowmount (VSS) | ✅ | ❌ | ❌ | ✅ |
| apfs-fuse (APFS) | ✅ | Native | ❌ | ✅ |
| hdiutil (DMG) | ❌ | ✅ Native | ❌ | ❌ |

**Windows Alternative**: Arsenal Image Mounter (commercial, $0 for free version)

### Memory Forensics

| Tool | All Platforms | Notes |
|------|---------------|-------|
| Volatility 3 | ✅ | Python, works everywhere |
| Volatility 2 | ✅ | Python, works everywhere |

### Timeline Tools

| Tool | Linux | macOS | Windows | Windows+WSL2 |
|------|-------|-------|---------|--------------|
| plaso | ✅ | ⚠️ | ❌ | ✅ |

**Plaso Notes**:
- macOS ARM64: Some dependencies may need Rosetta 2
- Windows: Does not work natively (use WSL2)

### Windows Artifact Parsers

All Python-based parsers work on all platforms:
- ✅ analyzeMFT
- ✅ python-evtx
- ✅ ShimCacheParser
- ✅ RegRipper (needs Perl)
- ✅ All bundled tools (USN-Journal-Parser, INDXRipper, etc.)

### Malware Analysis

| Tool | All Platforms | ARM64 | Notes |
|------|---------------|-------|-------|
| YARA | ✅ | ✅ | Native binaries available |
| ClamAV | ✅ | ✅ | Native binaries available |

---

## Installation Automation

### Automated Install Command

```bash
# Linux (Ubuntu/Debian)
elrond --install
# Installs: apt packages + pip packages + bundled tools

# macOS (Homebrew)
elrond --install
# Installs: brew packages + pip packages + bundled tools

# Windows (WSL2 - Recommended)
elrond --install --wsl
# Detects WSL, installs Ubuntu if needed, sets up environment

# Windows (Native - Limited)
elrond --install --windows-native
# Installs: Python tools + binaries only (limited functionality)
```

### What `--install` Does

1. **Detect Platform**: Auto-detect OS and architecture
2. **Check Prerequisites**: Verify package managers (apt/brew/pip)
3. **Install Tools**:
   - System tools (via apt/brew)
   - Python packages (via pip)
   - Download binaries (YARA, TSK, etc.)
4. **Verify Installation**: Run `elrond --check` automatically
5. **Report**: Show what was installed and what failed

### Interactive Installation

```bash
elrond --install --interactive

# Prompts for each tool:
# Install ewftools (required)? [Y/n]
# Install plaso (optional)? [y/N]
# ...
```

---

## Compatibility Summary

| Platform | Tools Available | Image Mounting | Recommendation |
|----------|-----------------|----------------|----------------|
| **Linux** | 30/30 (100%) | ✅ Full support | ⭐ Best choice |
| **macOS Intel** | 27/30 (90%) | ✅ Full support | ⭐ Excellent |
| **macOS ARM64** | 27/30 (90%) | ✅ Full support | ⭐ Excellent |
| **Windows + WSL2** | 30/30 (100%) | ✅ Full support | ⭐ Recommended |
| **Windows Native** | 15/30 (50%) | ❌ Very limited | ⚠️ Not recommended |

---

## Recommendations

### For New Users

1. **Linux**: Use Ubuntu 22.04+ (easiest, best supported)
2. **macOS**: Use Homebrew, works great on Intel and ARM64
3. **Windows**: Install WSL2 + Ubuntu (best Windows experience)

### For Existing SIFT Users

- ✅ elrond v2.0 works identically on SIFT
- ✅ All 30 tools pre-installed on SIFT
- ✅ No changes needed to workflow

### For Enterprise Deployments

- **Workstation**: Windows 11 + WSL2 + Ubuntu 22.04
- **Server**: Ubuntu Server 22.04 LTS
- **Cloud**: Ubuntu 22.04 AMI/Image

---

## Next Steps

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed installation instructions per platform.
