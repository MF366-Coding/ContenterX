import os
import sys
import platform
import distro
import subprocess


class IncompatibleSystem(OSError): ...
class UnderterminatedPkgManager(OSError): ...


def get_os_info() -> tuple[str, str, str]:
    basic = os.name # [i] Basic Info
    advanced = sys.platform # [i] Advacned Info
    architecture = platform.machine().lower() # [i] System Architecture
    
    if basic not in ('posix', 'nt'):
        basic = 'unknown'
        
    if advanced not in ('win32', 'linux', 'linux2', 'darwin', 'freebsd', 'openbsd'):
        raise IncompatibleSystem(f'unrecognized or incompatible system - {advanced}')
        
    if architecture not in ('x86_64', 'amd64', 'x86', 'arm64', 'arm', 'i386', 'ppc64le', 'aarch64'):
        raise IncompatibleSystem(f'unrecognizable or incompatible system architecture - {architecture}')
    
    return (basic, advanced, architecture)


def get_system_package_manager(system: tuple[str, str, str]):
    if system[1].startswith('linux'):
        family = distro.family().lower()

        if "debian" in family:
            return "apt"  # [<] apt my beloved
        
        if "arch" in family:
            return "pacman"  # [<] pacman my beloved
        
        if "redhat" in family:
            result = subprocess.run(['which', 'dnf'], capture_output=True, text=True)
            
            if result.returncode == 0:
                return 'dnf'
            
            return "yum"
        
        if "suse" in family:
            return "zypper"
        
        if "alpine" in family:
            return "apk"
        
        if "gentoo" in family:
            return "emerge"  # [<] compiling your system for 1000 hours straight <3
        
        if "void" in family:
            return "xbps-install"
        
        if "slackware" in family:
            return "slackpkg"
        
        return 'unknown'
    
    match system[1]:
        case 'win32':
            if system[2] not in ('x86_64', 'amd64'):
                raise UnderterminatedPkgManager(f'could not determine the official CLI package manager for Windows (arch: {system[2]})')
            
            return 'winget'
        
        case 'darwin':
            raise UnderterminatedPkgManager('macOS/darwin has no built-in CLI package manager')
        
        case 'freebsd':
            return 'pkg'
        
        case 'openbsd':
            return 'pkg_add'
        
        case _:
            raise UnderterminatedPkgManager("could not recognize the system's package manager")
        
    raise UnderterminatedPkgManager("could not recognize the system's package manager")    
