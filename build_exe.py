"""
Build Script for Audify.
Compiles the application into a standalone Windows .exe with embedded icon and metadata.
"""

import os
import subprocess
import sys


def build() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # 1. Ensure assets exist
    assets_dir = os.path.join(root_dir, "assets")
    ico_path = os.path.join(assets_dir, "icon.ico")
    if not os.path.exists(ico_path):
        print("[Build] Generating app icons...")
        from generate_assets import generate_icon
        generate_icon(assets_dir)

    # 2. Invoke PyInstaller
    spec_path = os.path.join(root_dir, "Audify.spec")
    print(f"[Build] Starting PyInstaller build with spec: {spec_path}...")

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_path]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.join(root_dir, "dist", "Audify.exe")
        print("\n===========================================")
        print("  BUILD SUCCESSFUL!")
        print(f"  Executable created at:\n  {exe_path}")
        print("===========================================\n")
    else:
        print("\n[Build Error] PyInstaller compilation failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
