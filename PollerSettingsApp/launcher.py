import subprocess
import sys
import sys
import shutil
import os
import time

def launch_chat_bot():
    print("Launching chat_bot.py in new terminal...")
    # Prefer venv Python if available
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = shutil.which("python") or shutil.which("python3")
    if not python_exe:
        print("Python interpreter not found!")
        return
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = f'start cmd /k "cd /d {script_dir} && {python_exe} chat_bot.py"'
    subprocess.Popen(cmd, shell=True)

def launch_poller():
    print("Launching poller.py in new terminal...")
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = shutil.which("python") or shutil.which("python3")
    if not python_exe:
        print("Python interpreter not found!")
        return
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = f'start cmd /k "cd /d {script_dir} && {python_exe} poller.py"'
    subprocess.Popen(cmd, shell=True)

def launch_gui():
    print("Launching GUI in new terminal...")
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = f'start cmd /k "cd /d {script_dir} && dotnet run"'
    subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    launch_chat_bot()
    launch_poller()
    launch_gui()