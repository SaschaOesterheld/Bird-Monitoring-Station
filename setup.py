"""
Installer and setup script for the Bird Monitoring Station.

This script automates the installation and configuration of the Bird
Monitoring Station on Raspberry Pi OS. It prepares the system by
installing the required Python version, creating a virtual environment,
installing project dependencies, cloning the project repository, and
configuring the operating system for automatic startup.

The installer performs the following tasks:
- Verifies that the target system is running Raspberry Pi OS.
- Installs required system packages and development libraries.
- Installs or configures pyenv to provide the required Python version.
- Clones the Bird Monitoring Station project repository.
- Creates a dedicated Python virtual environment.
- Installs all Python package dependencies.
- Enables the I²C interface required by supported hardware.
- Creates and enables a systemd service to automatically start the
Bird Monitoring Station after boot.

This script is intended to be executed once during installation and
requires administrative privileges for several system configuration
steps.
Author - Sascha Oesterheld
05.08.2026
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

#Setting up Variables###################################################################################################

#Sets the target python version
PYTHON_VERSION = "3.11.2"
#Sets the URL for the repo
REPO_URL = "https://github.com/SaschaOesterheld/Bird-Monitoring-Station.git"

#Ensures project dir exists
project_dir = Path.home() / "bimo2"
project_dir.mkdir(parents=True, exist_ok=True)
#Also set names for other dirs
venv_dir = project_dir / "venv"
pip_dir = venv_dir / "bin" / "pip"

#gives the systems python version
current_python = subprocess.check_output(["python3", "--version"],text=True)
#stores the python executable currently in use
python_executable = shutil.which("python3")

#Helper Functions#######################################################################################################

def pyenv_exists():
    """Return True if pyenv is installed."""
    return (Path.home() / ".pyenv" / "bin" / "pyenv").exists()

def install_python(version):
    """Install the requested Python version if needed."""
    try:
        pyenv = str(Path.home() / ".pyenv" / "bin" / "pyenv")
        installed = subprocess.check_output(
            [pyenv, "versions", "--bare"],
            text=True
        )
        if version not in installed:
            subprocess.run([pyenv, "install", version], check=True)
    except Exception as e:
        prRed(f"Something has gone wrong installing the correct python version ({PYTHON_VERSION}) to pyenv:")
        prRed(e)
        prRed("Aborting Installation")
        sys.exit()

def set_local_python(version):
    """Use the requested version in the project."""
    try:
        pyenv = str(Path.home() / ".pyenv" / "bin" / "pyenv")
        subprocess.run([pyenv, "local", version], cwd=project_dir, check=True)
    except Exception as e:
        prRed("Something has gone wrong setting the local python version on the raspi:")
        prRed(e)
        prRed("Aborting Installation")
        sys.exit()

def install_systemd_service():
    """Install and enable the Bird Monitoring Station systemd service."""
    try:
        #Setup service Vars
        print("Setting up Systemd service for the Program. This will make it start automatically on boot.")
        service_name = "bird-monitoring-station.service"
        working_dir = (project_dir/ "bimo2_project_files" / "birdnet_mini")
        log_location = (project_dir / "bimo2_project_files" /  "logs" / "systemlog_main.log")
        log_location.parent.mkdir(parents=True, exist_ok=True)
        main_script = working_dir / "main.py"
        python_exec = venv_dir / "bin" / "python"
        user = os.getenv("SUDO_USER") or os.getenv("USER") or "pi"

        #Remove old Service if it exists
        service_name = "bird-monitoring-station.service"
        service_path = Path("/etc/systemd/system") / service_name
        print("Removing old systemd service (if present)...")
        subprocess.run(["sudo", "systemctl", "stop", service_name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "systemctl", "disable", service_name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if service_path.exists():
            subprocess.run(["sudo", "rm", str(service_path)],check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"],check=True)

        #Setup Service File
        service = \
        f"""[Unit]
Description=Bird Monitoring Station Main Program controlling BIMO2 Funtionalities
After=network.target
            
[Service]
User={user}
ExecStart={python_exec} {main_script}
Restart=always
RestartSec=5
           
StandardOutput=append:{log_location}
StandardError=append:{log_location}
           
Environment=PYTHONUNBUFFERED=1
            
[Install]
WantedBy=multi-user.target
        """
        tmp_service = Path("/tmp") / service_name
        tmp_service.write_text(service)
        #Apply service file to created service
        subprocess.run(["sudo","cp",str(tmp_service),f"/etc/systemd/system/{service_name}",],check=True)
        #reload daemon
        subprocess.run(["sudo", "systemctl", "daemon-reload"],check=True)
        #enable and start new service
        subprocess.run(["sudo", "systemctl", "enable", service_name],check=True)
        subprocess.run(["sudo", "systemctl", "restart", service_name],check=True)
        #unlink temp service from setup
        tmp_service.unlink(missing_ok=True)
        prGreen("Successfully installed and enabled systemd service! The program should run automatically on boot.")
    except Exception as e:
        prRed("Installing the systemd service failed:")
        prRed(e)
        prRed("Autostart could not be set up automatically. Either rerun the installer or try to do it manually.")
        sys.exit(1)

def prRed(s): print("\033[91m {}\033[00m".format(s))
def prGreen(s): print("\033[92m {}\033[00m".format(s))
def prYellow(s): print("\033[93m {}\033[00m".format(s))

########################################################################################################################
# Start Main Code ######################################################################################################
########################################################################################################################

#Tell people that are not on RaspianOS to fuck off
if not Path("/etc/rpi-issue").exists():
    prRed("This installer only supports Raspberry Pi OS.")
    print("Install Raspberry Pi OS and try again.")
    sys.exit(1)
print("Raspberry Pi OS detected.")
#Show RasPi Hardware Version
raspi_model = Path("/proc/device-tree/model").read_text().strip()
print(f"Detected {raspi_model}, which is irrelevant for this script but nice to know ^u^")

#Update the RasPi
print("Updating System...")
subprocess.run(["sudo", "apt-get", "update"], check=True)
prGreen("System Update Complete!")

try:#Install some meta libraries for installation
    print("Installing prerequisite libraries...")
    subprocess.run(["sudo","apt","install","-y","build-essential","libssl-dev","zlib1g-dev","libbz2-dev","libreadline-dev","libsqlite3-dev","libffi-dev","liblzma-dev","tk-dev","wget","curl"], check=True)
    prGreen("Successfully installed prerequisites!")
except Exception as e:
    prRed("Installing necessary libraries has failed:")
    prRed(e)
    prRed("Aborting Installation")
    sys.exit(1)

try:#Checking python version and setting up pyenv
    print(current_python)
    if "3.11.2" not in current_python:
        print("You have a different python version than required. Getting correct python version via pyenv.")
        if not pyenv_exists():
            print("Installing pyenv...")
            #Install pyenv
            subprocess.run(["bash","-c","curl https://pyenv.run | bash"],check=True)
            #adjust bash
            bashrc = Path.home() / ".bashrc"
            lines = [
                'export PYENV_ROOT="$HOME/.pyenv"',
                'export PATH="$PYENV_ROOT/bin:$PATH"',
                'eval "$(pyenv init --path)"',
                'eval "$(pyenv init -)"'
            ]
            content = bashrc.read_text() if bashrc.exists() else ""
            with bashrc.open("a") as f:
                for line in lines:
                    if line not in content:
                        f.write("\n" + line)
            prGreen("Successfully installed pyenv!")
        print(f"Installing Python {PYTHON_VERSION} to pyenv. This might take up to an hour, since it has to compile binaries for an old python version.")
        prYellow(f"Be worried only if the prints stop for more than an hour. It is {datetime.now()}")
        install_python(PYTHON_VERSION)
        prGreen(f"Successfully installed Python {PYTHON_VERSION} to pyenv!")
        set_local_python(PYTHON_VERSION)
        prGreen(f"Successfully set Python {PYTHON_VERSION} for project directory {project_dir}!")
        python_executable = str(Path.home()/ ".pyenv"/ "versions"/ PYTHON_VERSION/ "bin"/ "python")
    else:
        assert python_executable is not None

except Exception as e:
    prRed("Either fetching python or setting up pyenv has failed:")
    prRed(e)
    prRed("Aborting Installation")
    sys.exit(1)


try:#Try to fetch the latest version of the project
    if project_dir.exists():
        print(f"Removing old installation at {project_dir}")
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True)
    print(f"Installing project to {project_dir}. Cloning from {REPO_URL}")
    subprocess.run(["git", "clone", REPO_URL, str(project_dir)],check=True)
    prGreen("Successfully cloned project!")
except Exception as e:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    prRed("Fetching the project from Git failed:")
    prRed(e)
    prRed("Aborting Installation")
    sys.exit(1)

try:
    #create Virtual Environment(venv) for Project
    print("Creating venv Instance for Project")
    subprocess.run([python_executable, "-m", "venv", str(venv_dir)],check=True)
    prGreen(f"Successfully created venv at {venv_dir}!")
except Exception as e:
    prRed("Creating Virtual Environment failed:")
    prRed(e)
    prRed("Aborting Installation")
    sys.exit(1)

try:#install requirements to the venv
    prYellow("Installing Requirements to Project venv. This might take a while...")
    subprocess.run([str(pip_dir), "install", "--upgrade", "pip"], check=True)
    #This is manual installation because automated req install cant do it. I know its jank. I'm not sorry
    subprocess.run(["sudo","apt","install","-y","libhdf5-dev","hdf5-tools"],check=True) #needed for tensorflow
    subprocess.run(["sudo", "apt", "install", "-y", "libportaudio2", "portaudio19-dev"], check=True) #needed for USB Microphones
    #Actual Installation via requirements.txt
    subprocess.run([str(pip_dir),"install","-r",str(project_dir/ "bimo2_project_files" / "requirements.txt")],check=True)
    prGreen("Successfully installed requirements to Project venv!")
except Exception as e:
    prRed("Installing required packages and libraries from requirements.txt failed:")
    prRed(e)
    prRed("Aborting Installation")
    print("This is probably pretty bad, and might be time intensive. Good Luck :)")
    sys.exit(1)

try:#activate i2c interface
    print("Activating I2C Interface")
    subprocess.run([
        "sudo","raspi-config","nonint","do_i2c","0"
    ], check=True)
    prGreen("Successfully activated I2C Interface!")
except Exception as e:
    prYellow("Failed to activate I2C Interface:")
    prYellow(e)
    prRed(r"Installation has concluded correctly elsewhise, you can activate the Interface manually via the Interface Rider here: 'sudo raspi-config' and 'sudo raspi-config nonint do_i2c 0'(the latter is important if the bme680 Sensor is used!)")

install_systemd_service()

prGreen("Successfully installed most things! Check I2C Interface activation though... ('sudo raspi-config' in the rider Interfaces)")
prYellow("The program will start itself after reboot. You can check on it via journactl or systemctl or via the log in the project files afterward. It helps writing down these options to make your life easier!")
prRed("Reboot required for all System Changes and Program Startup to go into effect! Reboot now? (Y for YES/ Anything else for NO)")
answer=input().strip().lower()
if answer in ("y", "yes"):
    prRed("Rebooting in 5 Seconds!")
    prRed("5")
    time.sleep(1)
    prRed("4")
    time.sleep(1)
    prRed("3")
    time.sleep(1)
    prRed("2")
    time.sleep(1)
    prRed("1")
    time.sleep(1)
    subprocess.run(["sudo","reboot"])
else:
    print("Not rebooting. Installation finished elsewhise!")
