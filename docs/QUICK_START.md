# elrond Quick Start Guide

Get up and running with elrond in under 5 minutes!

## Choose Your Platform

<table>
<tr>
<td width="33%">

### 🐧 Linux

```bash
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
chmod +x scripts/install_linux.sh
sudo ./scripts/install_linux.sh
```

[Full Linux Guide →](INSTALLATION_GUIDE.md#linux-installation-detailed)

</td>
<td width="33%">

### 🍎 macOS

```bash
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
chmod +x scripts/install_macos.sh
./scripts/install_macos.sh
```

[Full macOS Guide →](INSTALLATION_GUIDE.md#macos-installation-detailed)

</td>
<td width="33%">

### 🪟 Windows

```powershell
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
.\scripts\install_windows_wsl.ps1
```

[Full Windows Guide →](INSTALLATION_GUIDE.md#windows-installation-detailed)

</td>
</tr>
</table>

---

## Verify Installation

```bash
# Check all dependencies
elrond --check-dependencies

# Expected: "All required tools are available"
```

---

## Basic Usage

### Collect Mode (Process Evidence)

```bash
elrond -C \
  -c CASE-001 \
  -s /path/to/evidence \
  -o /path/to/output \
  --veryverbose
```

**What it does:**
1. Identifies forensic images (E01, VMDK, DD)
2. Mounts images automatically
3. Extracts artifacts (MFT, Registry, Event Logs, etc.)
4. Analyzes memory dumps
5. Creates timeline
6. Generates reports

### Gandalf Mode (Analyze Existing Extraction)

```bash
elrond -G \
  -c CASE-001 \
  -s /path/to/extracted/data \
  -o /path/to/output
```

**What it does:**
1. Analyzes pre-extracted artifacts
2. Parses Registry hives
3. Analyzes Event Logs
4. Creates timeline from artifacts
5. Generates comprehensive report

### Reorganize Mode (Re-structure Output)

```bash
elrond -R \
  -c CASE-001 \
  -s /path/to/previous/output \
  -o /path/to/new/output
```

**What it does:**
1. Reorganizes previous elrond output
2. Applies new structure
3. Preserves all data

---

## Common Options

| Flag | Description | Example |
|------|-------------|---------|
| `-C` | Collect mode (process evidence) | `elrond -C -c CASE-001 -s /evidence` |
| `-G` | Gandalf mode (analyze extraction) | `elrond -G -c CASE-001 -s /data` |
| `-R` | Reorganize mode | `elrond -R -c CASE-001 -s /old -o /new` |
| `-c <ID>` | Case identifier | `-c CASE-001` |
| `-s <PATH>` | Source directory/evidence | `-s /mnt/evidence` |
| `-o <PATH>` | Output directory | `-o /cases/CASE-001` |
| `-m` | Process memory dumps | `-m` |
| `-a` | Advanced analysis (slower) | `-a` |
| `--veryverbose` | Maximum output detail | `--veryverbose` |
| `--quiet` | Minimal output | `--quiet` |

---

## Memory Analysis

```bash
# With memory dump in source directory
elrond -C -c CASE-001 -s /evidence -m

# Specify memory dump explicitly
elrond -C -c CASE-001 -s /evidence -m /path/to/memory.dmp

# Memory dump with profile
elrond -C -c CASE-001 -s /evidence -m /memory.dmp -p Win10x64_19041
```

---

## Advanced Examples

### Process Multiple Images

```bash
# Put all images in source directory
# elrond will automatically find and process them
elrond -C -c CASE-001 -s /evidence/images/ -o /cases/CASE-001
```

### Timeline Analysis

```bash
# Include timeline creation
elrond -C -c CASE-001 -s /evidence -t

# Timeline with specific date range
elrond -C -c CASE-001 -s /evidence -t --start-date 2024-01-01 --end-date 2024-12-31
```

### Targeted Artifact Extraction

```bash
# Registry only
elrond -C -c CASE-001 -s /evidence --registry-only

# Event logs only
elrond -C -c CASE-001 -s /evidence --evtx-only

# Browser artifacts only
elrond -C -c CASE-001 -s /evidence --browser-only
```

---

## Platform-Specific Notes

### Linux

✅ **Best platform** - all 30 tools supported
✅ Native FUSE mounting
✅ All image formats (E01, VMDK, DD, VSS)

```bash
# May need sudo for mounting
sudo elrond -C -c CASE-001 -s /evidence
```

### macOS

✅ 27/30 tools supported (3 Linux-specific not needed)
✅ Works on Intel and **Apple Silicon (M1/M2/M3)**
✅ Native DMG and APFS support

```bash
# No sudo needed for most operations
elrond -C -c CASE-001 -s /evidence

# For E01 mounting, may need sudo
sudo elrond -C -c CASE-001 -s /evidence
```

**Apple Silicon Users**: All tools work natively on ARM64!

### Windows (WSL2)

✅ 100% tool compatibility via WSL2
✅ Access Windows files from WSL
✅ Native Linux tools

```powershell
# Run from Windows (calls WSL automatically)
wsl elrond -C -c CASE-001 -s /mnt/c/evidence

# Or enter WSL and run normally
wsl
elrond -C -c CASE-001 -s /mnt/c/evidence
```

**Path Mapping:**
- `C:\evidence` → `/mnt/c/evidence`
- `D:\cases` → `/mnt/d/cases`

---

## Troubleshooting

### "Tool not found" errors

```bash
# Check what's missing
elrond --check-dependencies

# Install missing tools
elrond --install
```

### "Permission denied" when mounting

```bash
# Use sudo (Linux/macOS)
sudo elrond -C -c CASE-001 -s /evidence
```

### "Module not found" errors

```bash
# Install Python dependencies
pip3 install -r requirements/base.txt

# Or reinstall elrond
cd /path/to/elrond
pip3 install -e .
```

### WSL issues (Windows)

```powershell
# Check WSL is installed
wsl --version

# Check Ubuntu is running
wsl --list --verbose

# Enter WSL to troubleshoot
wsl
elrond --check-dependencies
```

---

## Getting Help

### Built-in Help

```bash
# Main help
elrond --help

# Check dependencies
elrond --check-dependencies

# Check version
elrond --version
```

### Documentation

- **Installation**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Tool Compatibility**: [TOOL_COMPATIBILITY.md](TOOL_COMPATIBILITY.md)
- **Full README**: [README.md](README.md)
- **Implementation Details**: [PHASE3_IMPLEMENTATION.md](PHASE3_IMPLEMENTATION.md)

### Support

- **Issues**: https://github.com/cyberg3cko/elrond/issues
- **Discussions**: https://github.com/cyberg3cko/elrond/discussions

---

## Next Steps

1. ✅ Install elrond (see platform instructions above)
2. ✅ Verify installation: `elrond --check-dependencies`
3. ✅ Try processing test evidence
4. ✅ Read full documentation for advanced features
5. ✅ Star the repo ⭐ if you find it useful!

---

## Example Workflow

```bash
# 1. Install elrond
sudo ./scripts/install_linux.sh

# 2. Verify installation
elrond --check-dependencies

# 3. Process evidence
elrond -C \
  -c CASE-2024-001 \
  -s /mnt/evidence/disk.E01 \
  -o /cases/CASE-2024-001 \
  -m /mnt/evidence/memory.dmp \
  --veryverbose

# 4. View results
ls /cases/CASE-2024-001/
```

**Output Structure:**
```
/cases/CASE-2024-001/
├── registry/           # Registry hives and parsed data
├── timeline/           # Super timeline
├── memory/             # Memory analysis results
├── artifacts/          # Extracted artifacts
├── logs/               # Event logs
├── browser/            # Browser artifacts
└── reports/            # Generated reports
```

---

**You're ready to go!** 🚀

For detailed documentation, see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) and [README.md](README.md).
