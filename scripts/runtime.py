"""Shared launcher utilities. Commands always load the repository .env explicitly."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

def run(args, cwd=ROOT, env=None):
    subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)

def load_environment():
    from dotenv import dotenv_values
    path = ROOT / '.env'
    if not path.is_file():
        raise SystemExit('Missing .env. Run the bootstrap command first.')
    values = dotenv_values(path)
    env = os.environ.copy()
    env.update({k: v for k, v in values.items() if v is not None})
    return env

def npm():
    result = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not result:
        raise SystemExit('Node.js/npm not found. Install Node.js 22 or 24 LTS and reopen the terminal.')
    return result

def require_versions():
    if not ((3, 11) <= sys.version_info[:2] < (3, 13)):
        raise SystemExit('Python 3.11 or 3.12 is required. Use py -3.12 on Windows or python3.12 on Linux.')
    node = shutil.which('node')
    if not node:
        raise SystemExit('Install Node.js 22 or 24 LTS, then reopen the terminal.')
    major = int(subprocess.check_output([node, '--version'], text=True).strip().lstrip('v').split('.')[0])
    if major not in (22, 24):
        raise SystemExit(f'Node.js 22 or 24 LTS required; detected major {major}.')
    npm()
