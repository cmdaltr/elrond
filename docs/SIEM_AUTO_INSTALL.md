# SIEM Automatic Installation

**Feature**: Automatic download and installation of SIEM tools (Splunk, Elasticsearch, Kibana)
**Version**: elrond v2.1+
**Status**: ✅ Implemented

---

## Overview

elrond now automatically detects and installs the appropriate version of SIEM tools based on your platform when they are needed. This eliminates the manual process of downloading, version-checking, and installing Splunk, Elasticsearch, and Kibana.

## How It Works

### Automatic Detection

When you run elrond with Splunk (`--splunk`) or Elastic (`--elastic`) flags, elrond will:

1. **Detect your platform** - OS type, distribution, and version
2. **Check if SIEM tool is installed** - Look for existing installations
3. **Verify version compatibility** - Ensure installed version matches platform requirements
4. **Prompt for installation** - If not installed or incompatible, offer to auto-install
5. **Download correct version** - Select platform-specific package automatically
6. **Install and configure** - Install using native package manager

### User Experience

```bash
$ elrond -C case-001 /evidence/disk.E01 --splunk
```

**Output**:
```
======================================================================
SPLUNK is required but not installed (or incompatible)
Platform: linux (ubuntu_22.04)
Recommended version: 9.2.0
======================================================================
Would you like to automatically download and install splunk? [Y/n]:
```

**If user types `Y` or presses Enter**:
```
Downloading https://download.splunk.com/products/splunk/releases/9.2.0/linux/splunk-9.2.0-1fff88043d5f-linux-2.6-amd64.deb...
  Download progress: 25.0%
  Download progress: 50.0%
  Download progress: 75.0%
  Download progress: 100.0%
Downloaded to /tmp/tmpXXXXXX/splunk-9.2.0-1fff88043d5f-linux-2.6-amd64.deb
Installing splunk-9.2.0-1fff88043d5f-linux-2.6-amd64.deb...
splunk-9.2.0-1fff88043d5f-linux-2.6-amd64.deb installed successfully
splunk 9.2.0 installed successfully

✓ splunk 9.2.0 installed successfully

  -> Commencing Splunk Phase...
  ----------------------------------------
```

**If user types `n`**:
```
Skipping splunk installation.
To install manually, visit: Auto-downloaded and installed based on platform

  WARNING: Splunk is not installed. Skipping Splunk phase.
```

---

## Supported Platforms

### Linux

| Distribution | Versions Supported | Default Version Installed |
|-------------|-------------------|---------------------------|
| Ubuntu      | 20.04, 22.04, 24.04 | 9.1.0 (20.04), 9.2.0 (22.04+) |
| Debian      | 10, 11, 12       | 9.1.0 (10), 9.2.0 (11+) |
| RHEL        | 8, 9             | 9.1.0 (8), 9.2.0 (9) |
| CentOS      | 8                | 9.1.0 |

**Package Format**: .deb (Debian/Ubuntu), .rpm (RHEL/CentOS)

### macOS

| macOS Version | Name | Default Version Installed |
|--------------|------|---------------------------|
| 11.x | Big Sur | 8.1.0 |
| 12.x | Monterey | 8.2.0 |
| 13.x | Ventura | 9.2.0 |
| 14.x | Sonoma | 9.2.0 |
| 15.x | Sequoia | 9.2.0 |

**Package Format**: .dmg (Splunk), .tar.gz (Elasticsearch/Kibana)

### Windows

| Windows Version | Default Version Installed |
|----------------|---------------------------|
| Windows 10 | 9.2.0 |
| Windows 11 | 9.2.0 |
| Windows Server 2019 | 9.1.0 |
| Windows Server 2022 | 9.2.0 |

**Package Format**: .msi (Splunk), .zip (Elasticsearch/Kibana)

---

## SIEM Tools

### Splunk Enterprise

**What gets installed**:
- Splunk Enterprise (trial license, 60 days)
- Version: Platform-specific (see table above)
- Installation path:
  - Linux/macOS: `/opt/splunk`
  - Windows: `C:\Program Files\Splunk`

**Configuration**:
- Creates admin user credentials (prompted during elrond setup)
- Configures index for case data
- Installs elrond Splunk apps for visualization
- Adjusts memory limits for optimal performance

**Post-Installation**:
- Splunk Web: http://localhost:8000
- Splunk API: http://localhost:8089

### Elasticsearch

**What gets installed**:
- Elasticsearch (free tier)
- Version: Platform-specific and auto-matched to system
- Installation path:
  - Linux: `/usr/share/elasticsearch`
  - macOS: `/usr/local/elasticsearch`
  - Windows: `C:\Program Files\Elastic\Elasticsearch`

**Configuration**:
- Cluster name: `elrond`
- Node name: `elrond-es1`
- Network host: `127.0.0.1`
- HTTP port: `9200`
- Memory allocation: Auto-detected based on system RAM

**Post-Installation**:
- Elasticsearch API: http://localhost:9200

### Kibana

**What gets installed**:
- Kibana (free tier)
- Version: **MUST match Elasticsearch version exactly**
- Installation path:
  - Linux: `/usr/share/kibana`
  - macOS: `/usr/local/kibana`
  - Windows: `C:\Program Files\Elastic\Kibana`

**Configuration**:
- Server host: `127.0.0.1`
- Server port: `5601`
- Elasticsearch hosts: `["http://127.0.0.1:9200"]`

**Post-Installation**:
- Kibana Web: http://localhost:5601

---

## Version Compatibility

### How Version Selection Works

elrond uses a **platform-aware version compatibility matrix** defined in [tools/config.yaml](elrond/tools/config.yaml).

**Example for Elasticsearch on Ubuntu 22.04**:
```yaml
elasticsearch:
  version_compatibility:
    linux:
      ubuntu_22.04: ">=8.0.0,<9.0.0"
  download_urls:
    linux:
      ubuntu_22.04: "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.0-amd64.deb"
```

This means:
- Minimum version: 8.0.0
- Maximum version: < 9.0.0
- Recommended/default: 8.11.0 (from download URL)

### Elasticsearch ↔ Kibana Version Matching

**Critical**: Elasticsearch and Kibana **major.minor** versions MUST match.

✅ **Compatible**:
- Elasticsearch 8.11.0 + Kibana 8.11.4 (major.minor match: 8.11)
- Elasticsearch 8.15.0 + Kibana 8.15.0 (major.minor match: 8.15)

❌ **Incompatible**:
- Elasticsearch 8.11.0 + Kibana 8.10.0 (8.11 ≠ 8.10)
- Elasticsearch 8.15.0 + Kibana 7.17.0 (8.15 ≠ 7.17)

**Auto-matching**: When installing Elastic Stack, elrond automatically:
1. Installs Elasticsearch first
2. Detects installed Elasticsearch version
3. Installs matching Kibana version
4. Verifies version compatibility before proceeding

### Version Upgrade

If you already have an incompatible version installed:

```
Elasticsearch 7.10.0 is installed but incompatible: Version 7.10.0 is below minimum 8.0.0 for ubuntu_22.04
Will attempt to install compatible version...

Would you like to automatically download and install elasticsearch? [Y/n]:
```

Selecting `Y` will:
- Download compatible version (8.11.0)
- Install alongside or replace existing version
- Verify new version is compatible

---

## Manual Installation

If you prefer to install SIEM tools manually, or the auto-installer fails:

### Splunk Enterprise

**Download**:
- Visit: https://www.splunk.com/en_us/download/splunk-enterprise.html
- Select platform and version (see compatibility table)
- Requires Splunk.com account (free)

**Install**:
```bash
# Debian/Ubuntu
sudo dpkg -i splunk-*-linux-*.deb

# RHEL/CentOS
sudo rpm -i splunk-*.x86_64.rpm

# macOS
# Open .dmg and drag Splunk to Applications

# Windows
# Run .msi installer
```

### Elasticsearch

**Download**:
- Visit: https://www.elastic.co/downloads/elasticsearch
- Select platform and version (see compatibility table)

**Install**:
```bash
# Debian/Ubuntu
sudo dpkg -i elasticsearch-*-amd64.deb
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# RHEL/CentOS
sudo rpm -i elasticsearch-*.x86_64.rpm
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# macOS (Homebrew)
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full

# macOS (Manual)
tar -xzf elasticsearch-*-darwin-*.tar.gz
cd elasticsearch-*/
./bin/elasticsearch

# Windows
# Extract .zip to desired location
# Run bin\elasticsearch.bat
```

### Kibana

**Download**:
- Visit: https://www.elastic.co/downloads/kibana
- Select **SAME VERSION** as Elasticsearch

**Install**:
```bash
# Debian/Ubuntu
sudo dpkg -i kibana-*-amd64.deb
sudo systemctl enable kibana
sudo systemctl start kibana

# RHEL/CentOS
sudo rpm -i kibana-*.x86_64.rpm
sudo systemctl enable kibana
sudo systemctl start kibana

# macOS (Homebrew)
brew install elastic/tap/kibana-full

# macOS (Manual)
tar -xzf kibana-*-darwin-*.tar.gz
cd kibana-*/
./bin/kibana

# Windows
# Extract .zip to desired location
# Run bin\kibana.bat
```

---

## Programmatic Usage

You can also use the SIEM installer programmatically:

```python
from elrond.tools.siem_installer import SIEMInstaller

installer = SIEMInstaller()

# Install Splunk
success, msg = installer.install_siem_tool('splunk')
if success:
    print(f"✓ {msg}")
else:
    print(f"✗ {msg}")

# Install Elastic Stack (Elasticsearch + Kibana with version matching)
success, msg = installer.install_elastic_stack()
if success:
    print(f"✓ {msg}")
else:
    print(f"✗ {msg}")

# Ensure tool is installed (prompts user if not)
if installer.ensure_siem_installed('splunk'):
    print("Splunk is ready to use")
else:
    print("Splunk installation failed or was declined")
```

**Check version compatibility**:
```python
from elrond.utils.version_compat import VersionCompatibilityChecker

checker = VersionCompatibilityChecker()

# Check specific tool
is_compat, reason = checker.is_version_compatible('elasticsearch')
print(f"Elasticsearch compatible: {is_compat} - {reason}")

# Check Elasticsearch/Kibana match
match, msg = checker.check_elasticsearch_kibana_match()
print(f"ES/Kibana match: {match} - {msg}")

# Get recommended version
recommended = checker.get_recommended_versions('splunk')
print(f"Recommended Splunk version: {recommended}")
```

---

## Troubleshooting

### "Download failed"

**Cause**: Network issues, URL changes, or authentication requirements

**Solution**:
- Check internet connection
- For Splunk: May require Splunk.com account credentials
- Try manual download and installation

### "Installation failed"

**Cause**: Permission issues, conflicting installations, or missing dependencies

**Solution**:
```bash
# Ensure running with sufficient privileges
sudo elrond -C case-001 /evidence/disk.E01 --splunk

# Fix package dependencies (Debian/Ubuntu)
sudo apt-get install -f

# Fix package dependencies (RHEL/CentOS)
sudo yum install -y
```

### "Version could not be verified"

**Cause**: Tool installed but not in PATH, or version command failed

**Solution**:
- Check installation path manually
- Add to PATH:
  ```bash
  export PATH="/opt/splunk/bin:$PATH"
  export PATH="/usr/share/elasticsearch/bin:$PATH"
  export PATH="/usr/share/kibana/bin:$PATH"
  ```

### "Elasticsearch and Kibana versions don't match"

**Cause**: Installed versions have different major.minor versions

**Solution**:
```bash
# Check versions
/usr/share/elasticsearch/bin/elasticsearch --version
/usr/share/kibana/bin/kibana --version

# Reinstall Kibana to match Elasticsearch
sudo apt-get remove kibana
# Then re-run elrond with --elastic flag to auto-install matching version
```

---

## Configuration Files

SIEM tools are configured in [elrond/tools/config.yaml](elrond/tools/config.yaml):

```yaml
splunk:
  version_compatibility:
    linux:
      ubuntu_22.04: ">=8.2.0,<10.0.0"
  download_urls:
    linux:
      ubuntu_22.04: "https://download.splunk.com/..."
  auto_install: true

elasticsearch:
  version_compatibility:
    linux:
      ubuntu_22.04: ">=8.0.0,<9.0.0"
  download_urls:
    linux:
      ubuntu_22.04: "https://artifacts.elastic.co/..."
  auto_install: true

kibana:
  requires_version_match: "elasticsearch"
  auto_install: true
```

To update URLs or versions, edit this file.

---

## Security Considerations

### Splunk

- **Trial License**: Auto-installed Splunk has 60-day trial, 500MB/day limit
- **Credentials**: User prompted to create admin credentials during setup
- **Network**: Default binds to localhost (127.0.0.1)
- **Production**: Obtain license from Splunk.com for production use

### Elasticsearch/Kibana

- **Free Tier**: Auto-installed is Elastic Free tier (no authentication by default)
- **Security**: For production, enable X-Pack security features
- **Network**: Default binds to localhost (127.0.0.1)
- **Data**: No data sent to Elastic cloud

### Downloads

- **Verification**: Downloaded packages are from official sources
- **HTTPS**: All downloads use HTTPS
- **No bundling**: elrond does not bundle SIEM packages, always downloads latest

---

## Disabling Auto-Install

To disable automatic installation:

**Edit [elrond/tools/config.yaml](elrond/tools/config.yaml)**:
```yaml
splunk:
  auto_install: false  # Change to false

elasticsearch:
  auto_install: false  # Change to false

kibana:
  auto_install: false  # Change to false
```

When disabled, elrond will skip the installation prompt and warn that the tool is not installed.

---

*Document created: October 2025*
*elrond v2.1 - SIEM Auto-Installation Feature*
