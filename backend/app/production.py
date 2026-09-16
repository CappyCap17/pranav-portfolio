"""Production app: API routes followed by the compiled React frontend."""
from . import config
from .main import app
from .frontend import mount_frontend

mount_frontend(app, config.ROOT / 'frontend' / 'dist')
