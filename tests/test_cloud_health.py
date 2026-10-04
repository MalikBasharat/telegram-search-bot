"""
Unit Tests for Cloud Healthcheck & Keep-Alive Web Server
"""

import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from server.health import make_app
from db.database import init_db

class TestHealthServer(AioHTTPTestCase):
    async def get_application(self):
        init_db()
        return make_app()

    @unittest_run_loop
    async def test_health_endpoint(self):
        resp = await self.client.request("GET", "/health")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["bot"], "running")
        self.assertIn("total_files", data)

    @unittest_run_loop
    async def test_index_endpoint(self):
        resp = await self.client.request("GET", "/")
        self.assertEqual(resp.status, 200)
        text = await resp.text()
        self.assertIn("Telegram Bot Service", text)
        self.assertIn("Online 24/7", text)

if __name__ == "__main__":
    unittest.main()
