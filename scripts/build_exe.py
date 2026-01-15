#!/usr/bin/env python3
"""Build standalone executable using PyInstaller."""

import subprocess
import sys
from pathlib import Path


def build_cli():
    """Build CLI executable."""
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--name=kmz2shapefile',
        '--onefile',
        '--console',
        '--clean',
        'src/kmz2shapefile/cli.py',
    ]
    subprocess.run(cmd, check=True)


def build_gui():
    """Build GUI executable."""
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--name=kmz2shapefile-gui',
        '--onefile',
        '--windowed',  # No console window
        '--clean',
        'src/kmz2shapefile/gui.py',
    ]
    subprocess.run(cmd, check=True)


def main():
    """Build both executables."""
    project_root = Path(__file__).parent.parent

    print(f"Building in {project_root}")

    # Change to project root
    import os
    os.chdir(project_root)

    print("\n=== Building CLI executable ===")
    build_cli()

    print("\n=== Building GUI executable ===")
    build_gui()

    print("\n=== Build complete ===")
    print(f"Executables are in: {project_root / 'dist'}")


if __name__ == '__main__':
    main()
