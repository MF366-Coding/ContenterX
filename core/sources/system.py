import os
import sys
import platform
import distro
import subprocess


class UnderterminatedPkgManager(OSError): ...


def get_os() -> tuple[str, str, str]:
    basic = os.name # [i] Basic Info
    advanced = sys.platform # [i] Advacned Info
    architecture = platform.machine().lower() # [i] System Architecture
    
    if not basic:
        basic = 'unknown'
        
    if not advanced:
        advanced = 'unknown'
        
    if not architecture:
        architecture = 'unknown'
        
    return (basic, advanced, architecture)


def get_system_package_manager(system: tuple[str, str, str]):
    if system[1].startswith('linux'):
        family = distro.family().lower()

        if "debian" in family:
            if system[2] in ('sparcv9', 'sparc'):
                raise UnderterminatedPkgManager(f'could not determine the official CLI package manager for Debian-based (arch: {system[2]})')
            
            return "apt"  # [<] apt my beloved
        
        if "arch" in family:
            # TODO
            
            return "pacman"  # [<] pacman my beloved
        
        if "redhat" in family:
            if system[2] in ('sparcv9', 'sparc'):
                raise UnderterminatedPkgManager(f'could not determine the official CLI package manager for RedHat-based (arch: {system[2]})')
            
            result = subprocess.run(['which', 'dnf'], capture_output=True, text=True)
            
            if result.returncode == 0:
                return 'dnf'
            
            return "yum"
        
        if "suse" in family:
            if system[2] in ('armhf', 'aarch64', 'i686', 'sparcv9', 'sparc', 'armv7l'):
                raise UnderterminatedPkgManager(f'could not determine the official CLI package manager for SUSE-based (arch: {system[2]})')
            
            return "zypper"
        
        if "alpine" in family:
            # TODO
            return "apk"
        
        if "gentoo" in family:
            # TODO
            return "emerge"  # [<] compiling your system for 1000 hours straight <3
        
        if "void" in family:
            # TODO
            return "xbps-install"
        
        if "slackware" in family:
            # TODO
            return "slackpkg"
        
        return 'unknown'
    
    match system[1]:
        case 'win32':
            if system[2] != 'amd64':
                raise UnderterminatedPkgManager(f'could not determine the official CLI package manager for Windows (arch: {system[2]})')
            
            return 'winget'
        
        # TODO: add other cases
        
    
    

