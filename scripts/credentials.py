"""Write local-only credentials beside the launcher; never include in distributions."""
from runtime import ROOT, load_environment
import os

def main():
    env = load_environment()
    if env.get('ENVIRONMENT') == 'production':
        raise SystemExit('Credential export is only available for local development.')
    path = ROOT / 'LOCAL_CREDENTIALS.txt'
    content = ['YATRA KAVACH — PRIVATE LOCAL LOGIN DETAILS', 'Open http://localhost:5173 and select Staff / Control room.', 'Do not share this file or commit it to Git.', '']
    for role in ('ADMIN', 'HEALTH', 'POLICE', 'RESCUE', 'VOLUNTEER'):
        content += [role, 'Email: ' + env.get(f'STAFF_{role}_EMAIL', ''), 'Password: ' + env.get(f'STAFF_{role}_PASSWORD', ''), '']
    path.write_text('\n'.join(content), encoding='utf-8')
    os.chmod(path, 0o600)
    print('Staff credentials: LOCAL_CREDENTIALS.txt (private; open locally).')
if __name__ == '__main__':
    main()
