import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from itsdangerous import TimestampSigner
from fastapi.testclient import TestClient
from backend.app import main, config
from backend.app.storage import LocalContentStorage, GitHubContentStorage


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=config.ROOT / '.tools')
        self.store = LocalContentStorage(Path(self.temp.name))
        self.original = main.storage
        main.storage = self.store
        self.old_admin = config.ADMIN
        config.ADMIN = 'owner@example.com'
        self.client = TestClient(main.app)
        self.post = {'title': 'Test --- with punctuation', 'slug': 'test-post', 'date': '2026-09-15', 'summary': 'Testing', 'published': False, 'body': '# Safe Markdown'}

    def tearDown(self):
        main.storage = self.original
        config.ADMIN = self.old_admin
        self.temp.cleanup()

    def auth(self, email='owner@example.com'):
        data = {'user': {'email': email, 'name': 'Test', 'picture': ''}, 'csrf': 'test-csrf'}
        cookie = TimestampSigner(config.SECRET).sign(base64.b64encode(json.dumps(data).encode())).decode()
        self.client.cookies.set('portfolio_session', cookie, domain='testserver.local', path='/')
        return {'Origin': config.ORIGINS[0], 'X-CSRF-Token': 'test-csrf'}

    def test_auth_boundaries(self):
        self.assertEqual(self.client.get('/api/admin/blog').status_code, 401)
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post).status_code, 401)
        headers = self.auth('visitor@example.com')
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post, headers=headers).status_code, 403)
        self.auth('Owner@example.com')
        self.assertEqual(self.client.get('/api/admin/blog').status_code, 403)
        self.auth()
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post).status_code, 403)
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post, headers={'Origin': 'https://evil.example', 'X-CSRF-Token': 'test-csrf'}).status_code, 403)

    def test_post_lifecycle_and_conflicts(self):
        headers = self.auth()
        created = self.client.post('/api/admin/blog', json=self.post, headers=headers)
        self.assertEqual(created.status_code, 201, created.text)
        revision = created.json()['revision']
        self.assertEqual(self.client.get('/api/blog').json(), [])
        self.assertEqual(self.client.get('/api/blog/test-post').status_code, 404)
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post, headers=headers).status_code, 409)
        self.post.update(published=True, revision=revision)
        result = self.client.put('/api/admin/blog/test-post', json=self.post, headers=headers)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.client.get('/api/blog').json()), 1)
        self.assertEqual(self.client.get('/api/blog/test-post').json()['body'], '# Safe Markdown')
        self.assertEqual(self.client.put('/api/admin/blog/test-post', json=self.post, headers=headers).status_code, 409)
        revision = result.json()['revision']
        self.post.update(published=False, revision=revision)
        unpublished = self.client.put('/api/admin/blog/test-post', json=self.post, headers=headers)
        self.assertEqual(self.client.get('/api/blog/test-post').status_code, 404)
        deleted = self.client.delete('/api/admin/blog/test-post', params={'revision': unpublished.json()['revision']}, headers=headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get('/api/admin/blog').json(), [])

    def test_about_slug_and_logout(self):
        headers = self.auth()
        result = self.client.put('/api/admin/about', json={'body': '# About'}, headers=headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get('/api/about').json()['body'], '# About')
        self.assertEqual(self.client.put('/api/admin/about', json={'body': 'overwrite'}, headers=headers).status_code, 409)
        self.post['slug'] = '../about'
        self.assertEqual(self.client.post('/api/admin/blog', json=self.post, headers=headers).status_code, 422)
        self.assertEqual(self.client.get('/api/blog/bad.slug').status_code, 400)
        self.assertEqual(self.client.post('/api/auth/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/admin/blog').status_code, 401)

    def test_session_cookie_and_health(self):
        response = self.client.get('/api/auth/me')
        self.assertIn('httponly', response.headers['set-cookie'].lower())
        self.assertIn('samesite=lax', response.headers['set-cookie'].lower())
        self.assertFalse(response.json()['is_admin'])
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ok')

    def test_github_rate_limit(self):
        old = main.project_cache.copy()
        main.project_cache.update(at=0, items=[])
        try:
            with patch('httpx.AsyncClient.get', new=AsyncMock(side_effect=__import__('httpx').ConnectError('offline'))):
                self.assertEqual(self.client.get('/api/projects').status_code, 503)
                main.project_cache['items'] = [{'name': 'cached'}]
                self.assertTrue(self.client.get('/api/projects').json()['stale'])
        finally:
            main.project_cache.update(old)


class GitHubStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_commit_payloads(self):
        store = GitHubContentStorage()
        store.request = AsyncMock(return_value={'content': {'sha': 'new'}, 'commit': {'html_url': 'https://github.com/example/commit/123'}})
        saved = await store.write('blog/test.md', 'hello', 'old')
        self.assertEqual(saved['revision'], 'new')
        args = store.request.call_args
        self.assertEqual(args.kwargs['json']['sha'], 'old')
        self.assertEqual(base64.b64decode(args.kwargs['json']['content']), b'hello')
        await store.delete('blog/test.md', 'new')
        self.assertEqual(store.request.call_args.args[0], 'DELETE')

    async def test_path_traversal(self):
        store = LocalContentStorage()
        with self.assertRaises(main.HTTPException): store.path('../.env')


if __name__ == '__main__': unittest.main()
