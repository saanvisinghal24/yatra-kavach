"""Migrate and seed using the same explicit environment as API/worker."""
import argparse
from runtime import ROOT, VENV_PYTHON, load_environment, run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'migrate', 'seed'])
    parser.add_argument('--local', action='store_true', help='Refuse production configuration during bootstrap')
    args = parser.parse_args()
    env = load_environment()
    if args.local and env.get('ENVIRONMENT') == 'production':
        raise SystemExit('Existing .env is production; bootstrap will not migrate it. Use production deployment commands.')
    if args.action in ('init', 'migrate'):
        run([VENV_PYTHON, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT / 'api', env=env)
    if args.action in ('init', 'seed'):
        run([VENV_PYTHON, '-m', 'app.seed.seed_trails'], cwd=ROOT / 'api', env=env)
