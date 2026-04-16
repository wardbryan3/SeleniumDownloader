"""
Build script for creating Windows executable
Run: python build.py
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def build():
    project_root = Path(__file__).parent.parent.resolve()
    spec_file = project_root / 'AudioDownloader.spec'
    
    if not spec_file.exists():
        print('ERROR: AudioDownloader.spec not found!')
        print('Make sure you are running from the windows folder')
        sys.exit(1)
    
    print('Building executable using spec file...')
    PyInstaller.__main__.run([str(spec_file), '--clean'])
    
    print()
    print('Build complete!')
    print(f'Executable: {project_root / "dist" / "AudioDownloader.exe"}')

if __name__ == '__main__':
    build()
