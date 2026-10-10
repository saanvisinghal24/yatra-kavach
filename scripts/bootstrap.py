"""Create a private, repeatable local development environment without replacing .env."""
import argparse
import os
import secrets
import sys
from runtime import ROOT, VENV_PYTHON, require_versions, run, npm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-deps', action='store_true', help='Reuse already installed Python dependencies')
    parser.add_argument('--skip-web', action='store_true', help='Skip npm ci (existing installation only)')
    args = parser.parse_args()
    require_versions()
    if not VENV_PYTHON.exists():
        run([sys.executable, '-m', 'venv', ROOT / '.venv'])
    if not args.skip_deps:
        run([VENV_PYTHON, '-m', 'pip', 'install', '-r', ROOT / 'api/requirements.txt'])
    path = ROOT / '.env'
    if not path.exists():
        values = dict(line.split('=', 1) for line in (ROOT / '.env.example').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
        db = (ROOT / 'local.sqlite3').as_posix()
        values.update(ENVIRONMENT='development', DEBUG='false', DEMO_MODE='true', PUBLIC_ORIGIN='http://localhost:5173', DOMAIN='localhost', DATABASE_URL='sqlite+aiosqlite:///' + db, SYNC_DATABASE_URL='sqlite:///' + db)
        for key in ('SECRET_KEY', 'QR_HMAC_SECRET', 'JWT_SECRET'):
            values[key] = secrets.token_hex(32)
        for role in ('ADMIN', 'HEALTH', 'POLICE', 'RESCUE', 'VOLUNTEER'):
            values[f'STAFF_{role}_EMAIL'] = role.lower() + '@demo.invalid'
            values[f'STAFF_{role}_PASSWORD'] = secrets.token_urlsafe(24)
        # Exclusive create: even concurrent launches cannot replace existing credentials.
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write('# Generated private LOCAL SQLite convenience configuration. Do not commit.\n')
            stream.write('\n'.join(f'{k}={v}' for k, v in values.items()) + '\n')
        print('Created private .env. Staff login credentials are stored there.')
    else:
        print('Preserving existing .env and all credentials.')
    run([VENV_PYTHON, ROOT / 'scripts/manage.py', 'init', '--local'])
    run([VENV_PYTHON, ROOT / 'scripts/credentials.py'])
    if not args.skip_web:
        run([npm(), 'ci'], cwd=ROOT / 'web')
    print('Ready. Run python scripts/start.py. SQLite mode is local convenience, not PostgreSQL evidence.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit(f'Bootstrap failed: {exc}') from exc
