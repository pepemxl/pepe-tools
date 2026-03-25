import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import queue
import time
from pepe_tools.load_tester import execute_load_test, _worker
import json

class TestLoadTester(unittest.TestCase):
    @patch('pepe_tools.load_tester.time.time')
    @patch('requests.Session.request')
    def test_worker_success(self, mock_request, mock_time):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"Hello, World!"
        mock_request.return_value = mock_response

        # Setup mock time to allow 1 loop iteration then stop
        mock_time.side_effect = [0, 0, 0, 10, 10]
        
        results_queue = queue.Queue()
        endpoints = [{"url": "http://test.com", "weight": 1}]
        
        _worker(0, endpoints, 1, results_queue)
        
        self.assertEqual(results_queue.qsize(), 1)
        res = results_queue.get()
        self.assertEqual(res["status"], 200)
        self.assertEqual(res["size"], 13)
        self.assertEqual(res["endpoint"], "GET http://test.com")
        self.assertEqual(res["user"], "worker-0")
        self.assertIsNone(res["error"])

    @patch('pepe_tools.load_tester._worker')
    def test_execute_load_test(self, mock_worker):
        config_data = {
            "duration_seconds": 1,
            "users": 1,
            "endpoints": [{"url": "http://test.com"}]
        }
        
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(config_data))):
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                execute_load_test("dummy.json")
                
        output = fake_out.getvalue()
        self.assertIn("Starting Load Test with 1 users for 1 seconds...", output)
        self.assertIn("LOAD TEST RESULTS", output)

    @patch('pepe_tools.load_tester._worker')
    def test_execute_load_test_with_env(self, mock_worker):
        config_data = {
            "duration_seconds": 1,
            "users": 1,
            "endpoints": [{"url": "http://{{baseUrl}}/api", "headers": {"Auth": "{{authToken}}"}}]
        }
        env_data = {
            "values": [
                {"key": "baseUrl", "value": "my-server.com", "enabled": True},
                {"key": "authToken", "value": "secret123", "enabled": True},
                {"key": "ignored", "value": "test", "enabled": False}
            ]
        }
        
        def mock_open_impl(filename, *args, **kwargs):
            if filename == "dummy.json":
                return io.StringIO(json.dumps(config_data))
            elif filename == "env.json":
                return io.StringIO(json.dumps(env_data))
            return io.StringIO("")

        with patch('builtins.open', side_effect=mock_open_impl):
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                execute_load_test("dummy.json", env_file="env.json")
                
        # Verify that _worker was called with the interpolated endpoints
        mock_worker.assert_called_once()
        args, _ = mock_worker.call_args
        endpoints_passed = args[1]
        self.assertEqual(endpoints_passed[0]["url"], "http://my-server.com/api")
        self.assertEqual(endpoints_passed[0]["headers"]["Auth"], "secret123")

if __name__ == '__main__':
    unittest.main()
