#!/usr/bin/env python3
"""
The one file to run before playing Trailbound. Installs the Python
dependency (rich) and -- if you want it -- sets up local AI (Ollama plus
the default model) too, all in a single step.

Run it:
    python install.py     (or python3 install.py on macOS/Linux)

Or just double-click:
    install.bat            on Windows
    install.command         on macOS

Either way, this is the only command/click you need before `python
main.py`. Nothing here is required to play -- local AI setup is optional
and skippable, and the game runs fine with its own built-in story text
either way.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def install_python_deps() -> bool:
    print("Installing Python dependencies (rich)...\n")
    req_path = os.path.join(HERE, "requirements.txt")
    # Using `sys.executable -m pip` (rather than a bare `pip`/`pip3` command)
    # guarantees this installs into whichever Python is actually running
    # this script, avoiding any python/python3 or pip/pip3 mismatch.
    result = run([sys.executable, "-m", "pip", "install", "-r", req_path])
    if result.returncode != 0:
        print("\npip install failed -- see the error above.")
        return False
    print("\nPython dependencies installed.")
    return True


def offer_local_ai_setup():
    print("\nLocal AI (optional) adds AI-enhanced narration and lets you type")
    print("free-text actions instead of picking from a menu. It needs Ollama")
    print("plus a model (~3.3GB download) -- entirely skippable, and Trailbound")
    print("plays fine without it either way.")

    if not ask_yes_no("\nSet up local AI now?", default=True):
        print("Skipped -- run `python setup_ai.py` any time later if you change your mind.")
        return

    sys.path.insert(0, HERE)
    import setup_ai
    try:
        setup_ai.main()
    except SystemExit as e:
        if e.code not in (0, None):
            print("\nLocal AI setup didn't finish, but Trailbound still runs fine without it.")
            print("You can retry any time with: python setup_ai.py")


def main():
    print("Trailbound installer")
    print("=" * 40)

    if not install_python_deps():
        sys.exit(1)

    offer_local_ai_setup()

    py = os.path.basename(sys.executable)
    print("\nAll set. Run the game with:")
    print(f"  {py} {os.path.join(HERE, 'main.py')}")


if __name__ == "__main__":
    main()
