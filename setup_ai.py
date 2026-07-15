#!/usr/bin/env python3
"""
One-command setup for Trailbound's optional local AI narration: installs
Ollama if it isn't already present, makes sure it's running, and pulls the
default model (gemma3:4b, ~3.3GB download).

Ollama is a separate system application, not a Python package -- pip can't
install it, which is why this is a standalone script rather than something
in requirements.txt. Everything that IS pip-installable (just `rich`) is
still handled by `pip install -r requirements.txt` as usual.

Run it:
    python setup_ai.py

Entirely optional -- Trailbound runs fine without any of this, just
without AI-enhanced narration and free-text actions. Nothing here is
required to play.
"""
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error

DEFAULT_MODEL = "gemma3:4b"
OLLAMA_API = "http://localhost:11434"


def ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def ollama_reachable() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=2):
            return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")


def install_ollama() -> bool:
    system = platform.system()

    if system in ("Linux", "Darwin"):
        print("This will run Ollama's official install script:")
        print("  curl -fsSL https://ollama.com/install.sh | sh")
        if not confirm("Proceed?"):
            print("Skipped. Install Ollama yourself from https://ollama.com/download and re-run this script.")
            return False
        result = subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
        return result.returncode == 0

    if system == "Windows":
        if shutil.which("winget"):
            print("This will run: winget install -e --id Ollama.Ollama")
            if not confirm("Proceed?"):
                print("Skipped. Install Ollama yourself from https://ollama.com/download and re-run this script.")
                return False
            result = subprocess.run(["winget", "install", "-e", "--id", "Ollama.Ollama"])
            return result.returncode == 0
        print("Couldn't find winget. Download and run the installer yourself from:")
        print("  https://ollama.com/download")
        print("Then re-run this script.")
        return False

    print(f"Unrecognized platform ({system}). Install Ollama manually from https://ollama.com/download.")
    return False


def wait_for_ollama(retries=10, delay=1.5) -> bool:
    for _ in range(retries):
        if ollama_reachable():
            return True
        time.sleep(delay)
    return False


def pull_model(model: str) -> bool:
    print(f"\nPulling {model} (a few GB -- this can take a while on a slow connection)...\n")
    result = subprocess.run(["ollama", "pull", model])
    return result.returncode == 0


def main():
    print("Trailbound local AI setup")
    print("=" * 40)

    if not ollama_installed():
        print("Ollama not found on PATH.")
        if not install_ollama():
            print("\nSetup incomplete -- Trailbound will run fine without AI, just without narration/free-text actions.")
            sys.exit(1)
        if not ollama_installed():
            print("\nOllama was installed, but this terminal session doesn't see it on PATH yet.")
            print("Open a new terminal and re-run: python setup_ai.py")
            sys.exit(1)
    else:
        print("Ollama is already installed.")

    if not ollama_reachable():
        print("Ollama doesn't seem to be running yet -- trying to start it in the background...")
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
        if not wait_for_ollama():
            print("\nCouldn't reach Ollama at http://localhost:11434.")
            print("Try starting it yourself (`ollama serve`, or launch the Ollama app) and re-run this script.")
            sys.exit(1)
    print("Ollama is running.")

    if pull_model(DEFAULT_MODEL):
        print(f"\n{DEFAULT_MODEL} is ready. Run `python main.py` to play with local AI narration.")
    else:
        print(f"\nSomething went wrong pulling {DEFAULT_MODEL}. You can retry manually with:")
        print(f"  ollama pull {DEFAULT_MODEL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
