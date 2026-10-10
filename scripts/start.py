"""Supervise API, periodic worker and web server; Ctrl+C stops every child."""
import argparse
import os
import signal
import subprocess
import sys
import time
from runtime import ROOT, VENV_PYTHON, run, npm

def main():
    if not VENV_PYTHON.exists():
        raise SystemExit('Run python scripts/bootstrap.py first.')
    # Relaunch in the project venv so dotenv is available regardless of the caller.
    if os.path.abspath(sys.executable) != os.path.abspath(VENV_PYTHON):
        return subprocess.call([str(VENV_PYTHON), str(ROOT / 'scripts/start.py'), *sys.argv[1:]])
    from runtime import load_environment
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Build and serve the real PWA on localhost:5173')
    args = parser.parse_args()
    env = load_environment()
    if env.get('ENVIRONMENT') == 'production':
        raise SystemExit('Use production containers for production. This launcher serves local development only.')
    run([VENV_PYTHON, ROOT / 'scripts/manage.py', 'init', '--local'], env=env)
    if args.preview:
        run([npm(), 'run', 'build'], cwd=ROOT / 'web', env=env)
    children = []
    try:
        for command, cwd in [
            ([VENV_PYTHON, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], ROOT / 'api'),
            ([VENV_PYTHON, '-m', 'app.services.worker'], ROOT / 'api'),
            ([npm(), 'run', 'preview' if args.preview else 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort'], ROOT / 'web')]:
            children.append(subprocess.Popen([str(x) for x in command], cwd=cwd, env=env, start_new_session=(os.name != 'nt')))
        print('Open http://localhost:5173 — Ctrl+C stops all services.', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.3)
        raise RuntimeError('A service exited unexpectedly; see its log above.')
    except KeyboardInterrupt:
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], capture_output=True)
                else:
                    os.killpg(child.pid, signal.SIGTERM)
        for child in children:
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL) if os.name != 'nt' else child.kill()
    return 0

if __name__ == '__main__':
    sys.exit(main())
