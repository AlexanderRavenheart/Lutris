"""Automatically detects game executables in a folder"""
import os

from lutris.util import system
from lutris.util.log import logger

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None


if not MAGIC_AVAILABLE:
    logger.error("Magic not available. Unable to automatically find game executables. Please install python-magic")
else:
    if not hasattr(magic, "from_file"):
        if hasattr(magic, "detect_from_filename"):
            magic.from_file = lambda f: magic.detect_from_filename(f).name  # pylint: disable=no-member
        else:
            logger.error("Your version of python-magic is too old.")
            MAGIC_AVAILABLE = False


def is_excluded_elf(filename):
    excluded = (
        "xdg-open",
        "uninstall"
    )
    _fn = filename.lower()
    return any(exclude in _fn for exclude in excluded)


def find_linux_game_executable(path, make_executable=False):
    """Looks for a binary or shell script that launches the game in a directory"""
    if not MAGIC_AVAILABLE:
        logger.warning("Magic not available. Not finding Linux executables")
        return ""

    for base, _dirs, files in os.walk(path):
        candidates = {}
        for _file in files:
            if is_excluded_elf(_file):
                continue
            abspath = os.path.join(base, _file)
            file_type = magic.from_file(abspath)
            if "ASCII text executable" in file_type:
                candidates["shell"] = abspath
            if "Bourne-Again shell script" in file_type:
                candidates["bash"] = abspath
            if "POSIX shell script executable" in file_type:
                candidates["posix"] = abspath
            if "64-bit LSB executable" in file_type:
                candidates["64bit"] = abspath
            if "32-bit LSB executable" in file_type:
                candidates["32bit"] = abspath
        if candidates:
            if make_executable:
                for candidate in candidates.values():
                    system.make_executable(candidate)
            return (
                candidates.get("shell")
                or candidates.get("bash")
                or candidates.get("posix")
                or candidates.get("64bit")
                or candidates.get("32bit")
            )
    logger.error("Couldn't find a Linux executable in %s", path)
    return ""


def is_excluded_dir(path):
    excluded = (
        "Internet Explorer",
        "Windows NT",
        "Common Files",
        "Windows Media Player",
        "windows",
        "ProgramData",
        "users",
        "GameSpy Arcade"
    )
    return any(dir_name in excluded for dir_name in path.split("/"))


def is_excluded_exe(filename):
    excluded = (
        "unins000",
        "uninstal",
        "update",
        "config.exe",
        "gsarcade.exe",
        "dosbox.exe",
    )
    _fn = filename.lower()
    return any(exclude in _fn for exclude in excluded)


def find_windows_game_executable(path):
    if not MAGIC_AVAILABLE:
        logger.warning("Magic not available. Not finding Windows executables")
        return ""

    for base, _dirs, files in os.walk(path):
        candidates = {}
        if is_excluded_dir(base):
            continue
        for _file in files:
            if is_excluded_exe(_file):
                continue
            abspath = os.path.join(base, _file)
            if os.path.islink(abspath):
                continue
            file_type = magic.from_file(abspath)
            if "MS Windows shortcut" in file_type:
                candidates["link"] = abspath
            elif "PE32+ executable (GUI) x86-64" in file_type:
                candidates["64bit"] = abspath
            elif "PE32 executable (GUI) Intel 80386" in file_type:
                candidates["32bit"] = abspath
        if candidates:
            return (
                candidates.get("link")
                or candidates.get("64bit")
                or candidates.get("32bit")
            )
    logger.error("Couldn't find a Windows executable in %s", path)
    return ""
