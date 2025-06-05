"""Entry point for ``python -m macro_manager`` and ``macro-manager`` CLI.

This wrapper launches Streamlit with the bundled ``app.py`` so that the
application runs with full Streamlit context (no ``ScriptRunContext``
warnings). Additional command-line arguments are forwarded to Streamlit.
"""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    """Execute ``streamlit run`` for the packaged application."""
    app_path = Path(__file__).with_name("app.py")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless",
        "true",
        *sys.argv[1:],
    ]
    subprocess.call(cmd)


if __name__ == "__main__":
    main()
