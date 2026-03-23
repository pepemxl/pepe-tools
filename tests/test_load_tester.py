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

if __name__ == '__main__':
    unittest.main()
