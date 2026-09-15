import importlib.util
import os
import shutil
import subprocess
import sys

HOME = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(HOME, ".."))
SPEC_FILE = os.path.join(HOME, "build_exe.spec")
BUILD_DIR = os.path.join(HOME, "_build")
DIST_DIR = os.path.join(HOME, "_dist")
FINAL_EXE = os.path.join(PROJECT_DIR, "ofrom.exe")


def ensure_pyinstaller():
    if importlib.util.find_spec("PyInstaller") is not None:
        return

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "PyInstaller n'est pas installé "
            "et son installation automatique a échoué. "
            "Vérifiez que Python/pip est accessible "
            "et que vous avez les droits nécessaires "
            "pour installer des packages."
        ) from e


def build():
    ensure_pyinstaller()

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--workpath", BUILD_DIR,
                "--distpath", DIST_DIR,
                SPEC_FILE,
            ],
            check=True,
            cwd=HOME,
        )
    except subprocess.CalledProcessError as e:
        print(f"La création du build a échoué : {e.returncode}")
        raise SystemExit(e.returncode)


    generated_exe = os.path.join(DIST_DIR, "ofrom.exe")
    if os.path.exists(FINAL_EXE):
        os.remove(FINAL_EXE)

    shutil.move(generated_exe, FINAL_EXE)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.rmtree(DIST_DIR, ignore_errors=True)

if __name__ == "__main__":
    build()
