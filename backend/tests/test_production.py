import unittest
import tempfile
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.frontend import mount_frontend
from backend.app import config


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=config.ROOT / '.tools')
        directory = Path(self.temp.name)
        (directory / 'index.html').write_text('<div id="root"></div>', encoding='utf-8')
        application = FastAPI()
        @application.get('/api/health')
        async def health(): return {'status': 'ok'}
        mount_frontend(application, directory)
        self.client = TestClient(application)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_spa_and_api_routing(self):
        for path in ('/', '/projects', '/blog/hello-world', '/admin/blog/new'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn('<div id="root">', response.text)
            self.assertIn("frame-ancestors 'none'", response.headers['content-security-policy'])
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ok')
        self.assertEqual(self.client.get('/api/nonexistent').status_code, 404)
        self.assertEqual(self.client.get('/assets/missing.js').status_code, 404)
        self.assertEqual(self.client.get('/background.jpg').status_code, 404)
        self.assertEqual(self.client.get('/.env').status_code, 404)


if __name__ == '__main__': unittest.main()
