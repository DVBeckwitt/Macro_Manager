# launcher.py
import sys, os, subprocess

def main():
    # Locate the “dist/launcher” folder when frozen,
    # otherwise run from the project root
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        python = sys.executable   # this is the exe
    else:
        base = os.path.dirname(__file__)
        python = sys.executable   # your real venv python
    os.chdir(base)

    # Exactly mirror your run.bat
    subprocess.call([
        python, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true"
    ])

if __name__ == "__main__":
    main()
