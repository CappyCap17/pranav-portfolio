import asyncio
import math
import os
import re
import secrets
import time
from datetime import date
import httpx
import yaml
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from . import config
from .storage import storage

app = FastAPI(title='Pranav — Portfolio API', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=config.ORIGINS, allow_credentials=True,
                   allow_methods=['GET', 'POST', 'PUT', 'DELETE'], allow_headers=['Content-Type', 'X-CSRF-Token'])
app.add_middleware(SessionMiddleware, secret_key=config.SECRET, session_cookie='portfolio_session',
                   max_age=28800, same_site='lax', https_only=config.SECURE)
oauth = OAuth()
oauth.register('google', client_id=os.getenv('GOOGLE_CLIENT_ID'), client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
               server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
               client_kwargs={'scope': 'openid email profile'})


@app.middleware('http')
async def headers(request, call_next):
    if request.method in ('POST', 'PUT'):
        try:
            if int(request.headers.get('content-length', '0')) > 600_000:
                return JSONResponse({'detail': 'Request too large'}, status_code=413)
        except ValueError:
            return JSONResponse({'detail': 'Invalid request'}, status_code=400)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.exception_handler(httpx.HTTPError)
async def upstream_error(request, exc):
    return JSONResponse({'detail': 'External service unavailable. Please retry shortly.'}, status_code=502)


def csrf(request: Request):
    expected = request.session.get('csrf', '')
    actual = request.headers.get('x-csrf-token', '')
    if request.headers.get('origin') not in config.ORIGINS or not expected or not secrets.compare_digest(expected, actual):
        raise HTTPException(403, 'Invalid request origin or CSRF token')


def admin(request: Request):
    user = request.session.get('user')
    if not user: raise HTTPException(401, 'Please sign in')
    if not config.ADMIN or user['email'] != config.ADMIN: raise HTTPException(403, 'Administrator access required')
    if request.method != 'GET': csrf(request)
    return user


@app.get('/api/health')
async def health(): return {'status': 'ok', 'storage': config.STORAGE}


@app.get('/api/auth/me')
async def me(request: Request):
    request.session.setdefault('csrf', secrets.token_urlsafe(32))
    user = request.session.get('user')
    return {'user': user, 'is_admin': bool(user and config.ADMIN and user['email'] == config.ADMIN),
            'csrf': request.session['csrf'], 'login_enabled': bool(os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'))}


@app.get('/api/auth/login')
async def login(request: Request):
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        return RedirectResponse(config.FRONTEND + '/login?error=configuration')
    return await oauth.google.authorize_redirect(request, os.getenv('GOOGLE_REDIRECT_URI', config.FRONTEND + '/api/auth/callback'))


@app.get('/api/auth/callback')
async def callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        info = token['userinfo']
        if info.get('email_verified') is not True: raise ValueError('Unverified email')
        request.session.clear()
        request.session['user'] = {k: info.get(k, '') for k in ('name', 'email', 'picture')}
        request.session['csrf'] = secrets.token_urlsafe(32)
    except Exception:
        request.session.clear()
        return RedirectResponse(config.FRONTEND + '/login?error=oauth')
    return RedirectResponse(config.FRONTEND + '/projects')


@app.post('/api/auth/logout', dependencies=[Depends(csrf)])
async def logout(request: Request):
    request.session.clear()
    return {'ok': True}


class Post(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    slug: str = Field(pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=100)
    date: date
    summary: str = Field(default='', max_length=600)
    published: bool = False
    body: str = Field(max_length=500_000)
    revision: str | None = None


class About(BaseModel):
    body: str = Field(max_length=500_000)
    revision: str | None = None


def path_for(slug):
    if len(slug) > 100 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise HTTPException(400, 'Invalid slug')
    return f'blog/{slug}.md'


async def read_post(slug):
    raw, revision = await storage.read(path_for(slug))
    try:
        match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)(.*)\Z', raw, re.DOTALL)
        if not match: raise ValueError('Missing frontmatter')
        metadata, body = match.groups()
        post = Post(**{**yaml.safe_load(metadata), 'body': body.strip(), 'revision': revision})
        if post.slug != slug: raise ValueError('Slug does not match filename')
    except Exception:
        raise HTTPException(500, 'Invalid Markdown frontmatter')
    return {**post.model_dump(mode='json'), 'reading_time': max(1, math.ceil(len(body.split()) / 220))}


async def posts(include_drafts=False):
    result = []
    for path in await storage.list_posts():
        post = await read_post(path.removeprefix('blog/').removesuffix('.md'))
        if include_drafts or post['published']: result.append(post)
    return sorted(result, key=lambda p: p['date'], reverse=True)


@app.get('/api/blog')
async def blog():
    return [{k: v for k, v in p.items() if k not in ('body', 'revision')} for p in await posts()]


@app.get('/api/blog/{slug}')
async def article(slug: str):
    post = await read_post(slug)
    if not post['published']: raise HTTPException(404, 'Post not found')
    post.pop('revision')
    return post


@app.get('/api/about')
async def about(): return {'body': (await storage.read('about.md'))[0]}


@app.get('/api/admin/blog', dependencies=[Depends(admin)])
async def admin_posts(): return await posts(True)


@app.get('/api/admin/blog/{slug}', dependencies=[Depends(admin)])
async def admin_post(slug: str): return await read_post(slug)


async def save_post(post):
    metadata = post.model_dump(mode='json', exclude={'body', 'revision'})
    text = '---\n' + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True) + '---\n\n' + post.body + '\n'
    return await storage.write(path_for(post.slug), text, post.revision)


@app.post('/api/admin/blog', dependencies=[Depends(admin)], status_code=201)
async def create(post: Post):
    post.revision = None
    return await save_post(post)


@app.put('/api/admin/blog/{slug}', dependencies=[Depends(admin)])
async def update(slug: str, post: Post):
    if slug != post.slug: raise HTTPException(400, 'Existing post slugs cannot be changed')
    if not post.revision: raise HTTPException(400, 'Revision required')
    return await save_post(post)


@app.delete('/api/admin/blog/{slug}', dependencies=[Depends(admin)])
async def delete(slug: str, revision: str): return await storage.delete(path_for(slug), revision)


@app.get('/api/admin/about', dependencies=[Depends(admin)])
async def admin_about():
    body, revision = await storage.read('about.md')
    return {'body': body, 'revision': revision}


@app.put('/api/admin/about', dependencies=[Depends(admin)])
async def save_about(data: About): return await storage.write('about.md', data.body, data.revision)


project_cache = {'at': 0, 'items': []}
project_lock = asyncio.Lock()


@app.get('/api/projects')
async def projects():
    async with project_lock:
        if time.monotonic() - project_cache['at'] < 300: return {'items': project_cache['items'], 'stale': False}
        try:
            items = []
            async with httpx.AsyncClient(timeout=15) as client:
                for page in range(1, 101):
                    response = await client.get(f'https://api.github.com/users/{config.OWNER}/repos',
                        params={'per_page': 100, 'page': page, 'sort': 'updated'}, headers={'Accept': 'application/vnd.github+json'})
                    response.raise_for_status()
                    batch = response.json()
                    items.extend({key: repo.get(key) for key in ('id', 'name', 'description', 'language', 'stargazers_count', 'updated_at', 'html_url', 'homepage', 'fork')} for repo in batch)
                    if len(batch) < 100: break
            project_cache.update(at=time.monotonic(), items=items)
            return {'items': items, 'stale': False}
        except httpx.HTTPError:
            if project_cache['items']: return {'items': project_cache['items'], 'stale': True}
            raise HTTPException(503, 'GitHub is unavailable or rate limited. Please try again shortly.')
