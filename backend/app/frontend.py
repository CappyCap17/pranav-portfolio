"""Serve the built React application after the API routes."""
from pathlib import Path
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        path = path.replace('\\', '/')
        # Unknown API URLs and missing assets must never return the SPA shell.
        if path == 'api' or path.startswith('api/') or any(part.startswith('.') and part != '.' for part in path.split('/')):
            raise HTTPException(404, 'API route not found')
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or path.startswith('assets/') or Path(path).suffix:
                raise
            return await super().get_response('index.html', scope)


def mount_frontend(application: FastAPI, directory: Path):
    if not (directory / 'index.html').is_file():
        raise RuntimeError('Frontend build missing. Run npm run build in frontend first.')

    @application.middleware('http')
    async def production_headers(request, call_next):
        response = await call_next(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https: data:; connect-src 'self'; font-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    application.mount('/', FrontendFiles(directory=directory, html=True), name='frontend')
