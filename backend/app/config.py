import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
STORAGE = os.getenv('CONTENT_STORAGE', 'local')
SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
SECRET = os.getenv('SESSION_SECRET', '')
if SECURE and len(SECRET) < 32:
    raise RuntimeError('Set SESSION_SECRET to at least 32 random characters')
SECRET = SECRET or secrets.token_urlsafe(48)
FRONTEND = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
ORIGINS = [s.strip().rstrip('/') for s in os.getenv('CORS_ORIGINS', FRONTEND).split(',')]
ADMIN = os.getenv('ADMIN_EMAIL', '')
OWNER = os.getenv('GITHUB_OWNER', 'CappyCap17')
REPO = os.getenv('GITHUB_REPO', '')
BRANCH = os.getenv('GITHUB_BRANCH', 'main')
TOKEN = os.getenv('GITHUB_TOKEN', '')
