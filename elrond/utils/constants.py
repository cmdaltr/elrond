"""Constants used throughout elrond."""

from typing import List

# Size constants
ONE_KB = 1024
ONE_MB = 1024 * 1024
ONE_GB = 1024 * 1024 * 1024

# Minimum image size to process (1 GB)
MIN_IMAGE_SIZE = ONE_GB

# Default number of mount points to create
DEFAULT_MOUNT_COUNT = 20

# Excluded file extensions (E01 split files)
EXCLUDED_EXTENSIONS: List[str] = [f".F{chr(i)}" for i in range(ord("A"), ord("Z") + 1)]

# Supported image formats
SUPPORTED_IMAGE_EXTENSIONS = [
    ".e01",
    ".E01",
    ".vmdk",
    ".VMDK",
    ".dd",
    ".DD",
    ".raw",
    ".RAW",
    ".img",
    ".IMG",
    ".001",
    ".dmg",
    ".DMG",
]

# Image type identifiers (from 'file' command output)
IMAGE_TYPE_PATTERNS = {
    "ewf": ["Expert Witness", "EnCase"],
    "vmdk": ["VMDK", "VMware disk image"],
    "raw": ["DOS/MBR boot sector"],
    "memory": ["data", "crash dump", "Windows memory"],
}

# System artefacts to collect (from elrond.py)
WINDOWS_ARTEFACTS = [
    "/$MFT",
    "/$Extend/$UsnJrnl",
    "/$Extend/$ObjId",
    "/$Extend/$Reparse",
    "/$LogFile",
    "/$Recycle.Bin",
    "/Windows/AppCompat/Programs/RecentFileCache.bcf",
    "/Windows/AppCompat/Programs/Amcache.hve",
    "/Windows/inf/setupapi.dev.log",
    "/Windows/Prefetch/",
    "/Windows/System32/config/",
    "/Windows/System32/LogFiles/Sum/",
    "/Windows/System32/LogFiles/WMI/",
    "/Windows/System32/sru/",
    "/Windows/System32/wbem/Repository/",
    "/Windows/System32/wbem/Logs/",
    "/Windows/System32/winevt/Logs/",
    "/Users/",
]

LINUX_ARTEFACTS = [
    "/.Trashes",
    "/etc/passwd",
    "/etc/shadow",
    "/etc/group",
    "/etc/hosts",
    "/etc/crontab",
    "/etc/security",
    "/etc/systemd",
    "/etc/modules-load",
    "/home",
    "/root",
    "/tmp",
    "/usr/lib/systemd/user",
    "/var/cache/cups",
    "/var/log",
    "/var/log/journal",
    "/boot",
]

MACOS_ARTEFACTS = [
    "/.Trashes",
    "/Library/Logs",
    "/Library/Preferences",
    "/Library/LaunchAgents",
    "/Library/LaunchDaemons",
    "/Library/StartupItems",
    "/System/Library/Preferences",
    "/System/Library/LaunchAgents",
    "/System/Library/LaunchDaemons",
    "/System/Library/StartupItems",
    "/Users/",
    "/etc/passwd",
    "/etc/shadow",
    "/etc/group",
    "/etc/hosts",
    "/etc/crontab",
    "/etc/security",
    "/tmp",
    "/var/log",
]

# Combine all system artefacts
SYSTEM_ARTEFACTS = list(set(WINDOWS_ARTEFACTS + LINUX_ARTEFACTS + MACOS_ARTEFACTS))

# Command timeout (seconds)
DEFAULT_COMMAND_TIMEOUT = 300  # 5 minutes
LONG_COMMAND_TIMEOUT = 3600  # 1 hour

# Buffer size for file operations
FILE_READ_BUFFER_SIZE = 262144  # 256KB
