"""Browser origin protection and a database-backed, multi-worker request limiter."""
from datetime import datetime, timezone
import hashlib
from sqlalchemy import text
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.db import AsyncSessionLocal


def apply_security_headers(response, path, production):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'camera=(self), geolocation=(self), microphone=()'
    if path.startswith('/api'):
        response.headers['Cache-Control'] = 'no-store'
    if production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


async def security_middleware(request, call_next):
    settings = get_settings()
    path = request.url.path.rstrip('/') or '/'
    def reject(detail, status_code, headers=None):
        return apply_security_headers(JSONResponse({'detail': detail}, status_code=status_code, headers=headers), path, settings.ENVIRONMENT == 'production')

    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        fetch_site = request.headers.get('sec-fetch-site')
        # Never accept suffix matches, null origins, or sibling subdomains.
        if origin is not None and origin != settings.PUBLIC_ORIGIN:
            return reject('Origin not allowed', 403)
        if origin is None:
            if fetch_site is not None and fetch_site != 'same-origin':
                return reject('Same-origin browser request required', 403)
            if request.cookies.get('staff_session') and fetch_site != 'same-origin':
                return reject('Session mutations require an exact Origin or same-origin Fetch Metadata', 403)
        limits = {'/api/v1/auth/login': 10, '/api/v1/checkins/batch': 60,
                  '/api/v1/sos': 10, '/api/v1/groups': 20, '/api/v1/symptom-reports': 30}
        if path in limits and settings.ENVIRONMENT != 'testing':
            # Use the ASGI peer address; only the trusted reverse proxy may supply it.
            # Never consume raw X-Forwarded-For here (clients can forge it).
            host = request.client.host if request.client else 'unknown'
            key = hashlib.sha256(f'{host}:{path}'.encode()).hexdigest()
            bucket = int(datetime.now(timezone.utc).timestamp()) // 60
            async with AsyncSessionLocal() as db:
                count = (await db.execute(text('INSERT INTO rate_bucket (key, bucket, count) VALUES (:key,:bucket,1) ON CONFLICT (key,bucket) DO UPDATE SET count=rate_bucket.count+1 RETURNING count'), {'key': key, 'bucket': bucket})).scalar_one()
                await db.execute(text('DELETE FROM rate_bucket WHERE bucket < :old'), {'old': bucket-2})
                await db.commit()
            if count > limits[path]:
                return reject('Too many requests; retry in one minute.', 429, {'Retry-After': '60'})
    response = await call_next(request)
    return apply_security_headers(response, path, settings.ENVIRONMENT == 'production')
