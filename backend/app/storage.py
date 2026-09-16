import base64
import hashlib
import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
import httpx
from fastapi import HTTPException
from . import config


class ContentStorage(ABC):
    @abstractmethod
    async def list_posts(self): ...
    @abstractmethod
    async def read(self, path): ...
    @abstractmethod
    async def write(self, path, text, revision): ...
    @abstractmethod
    async def delete(self, path, revision): ...


class LocalContentStorage(ContentStorage):
    def __init__(self, root=None):
        self.root = (root or config.ROOT / 'content').resolve()
        self.lock = asyncio.Lock()

    def path(self, path):
        result = (self.root / path).resolve()
        if not result.is_relative_to(self.root):
            raise HTTPException(400, 'Invalid content path')
        return result

    async def list_posts(self):
        return [f'blog/{p.name}' for p in self.path('blog').glob('*.md')]

    async def read(self, path):
        try:
            data = self.path(path).read_bytes()
        except FileNotFoundError:
            raise HTTPException(404, 'Content not found')
        return data.decode('utf-8'), hashlib.sha256(data).hexdigest()

    async def check(self, path, revision):
        try:
            _, current = await self.read(path)
        except HTTPException as exc:
            if exc.status_code != 404: raise
            current = None
        if current != revision:
            raise HTTPException(409, 'Content changed. Reload before saving.')

    async def write(self, path, text, revision):
        async with self.lock:
            await self.check(path, revision)
            target = self.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=target.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
                    out.write(text)
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
            return {'revision': (await self.read(path))[1], 'commit_url': None}

    async def delete(self, path, revision):
        async with self.lock:
            await self.check(path, revision)
            self.path(path).unlink()
            return {'commit_url': None}


class GitHubContentStorage(ContentStorage):
    async def request(self, method, path, **kwargs):
        if not config.REPO or not config.TOKEN:
            raise HTTPException(503, 'GitHub content storage is not configured')
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(method,
                f'https://api.github.com/repos/{config.OWNER}/{config.REPO}/contents/content/{path}',
                headers={'Authorization': f'Bearer {config.TOKEN}', 'Accept': 'application/vnd.github+json',
                         'X-GitHub-Api-Version': '2022-11-28'}, **kwargs)
        if response.status_code == 404: raise HTTPException(404, 'Content not found')
        if response.status_code in (409, 422): raise HTTPException(409, 'Content changed or branch rejected the commit. Reload and retry.')
        if response.is_error: raise HTTPException(502, 'GitHub content request failed. Check repository permissions or rate limits.')
        return response.json()

    async def list_posts(self):
        try:
            data = await self.request('GET', 'blog', params={'ref': config.BRANCH})
        except HTTPException as exc:
            if exc.status_code == 404: return []
            raise
        return [f"blog/{item['name']}" for item in data if item['type'] == 'file' and item['name'].endswith('.md')]

    async def read(self, path):
        data = await self.request('GET', path, params={'ref': config.BRANCH})
        return base64.b64decode(data['content']).decode('utf-8'), data['sha']

    async def write(self, path, text, revision):
        body = {'message': f'Update {path}', 'branch': config.BRANCH,
                'content': base64.b64encode(text.encode()).decode()}
        if revision: body['sha'] = revision
        data = await self.request('PUT', path, json=body)
        return {'revision': data['content']['sha'], 'commit_url': data['commit']['html_url']}

    async def delete(self, path, revision):
        data = await self.request('DELETE', path, json={'message': f'Delete {path}', 'sha': revision, 'branch': config.BRANCH})
        return {'commit_url': data['commit']['html_url']}


if config.STORAGE not in ('local', 'github'):
    raise RuntimeError('CONTENT_STORAGE must be local or github')
storage = GitHubContentStorage() if config.STORAGE == 'github' else LocalContentStorage()
