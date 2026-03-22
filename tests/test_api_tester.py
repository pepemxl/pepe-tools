import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import requests
from pepe_tools.api_tester import execute_api_test

class TestApiTester(unittest.TestCase):
    @patch('pepe_tools.api_tester.requests.request')
    def test_execute_api_test_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            execute_api_test("GET", "http://test.com", ["Auth: Token"], None)

        mock_request.assert_called_once_with("GET", "http://test.com", headers={"Auth": "Token"}, data=None)
        output = fake_out.getvalue()
        self.assertIn("Status Code: 200 OK", output)
        self.assertIn('"key": "value"', output)

    @patch('pepe_tools.api_tester.requests.request')
    def test_execute_api_test_invalid_header(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            execute_api_test("POST", "http://test.com", ["InvalidHeader"], "bodydata")

        mock_request.assert_called_once_with("POST", "http://test.com", headers={}, data="bodydata")
        output = fake_out.getvalue()
        self.assertIn("Warning: Invalid header format 'InvalidHeader'", output)
        self.assertIn("Body:\nNot Found", output)

    @patch('pepe_tools.api_tester.requests.request')
    def test_execute_api_test_exception(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException("Connection error")

        with patch('sys.stdout', new=io.StringIO()):
            with patch('sys.stderr', new=io.StringIO()) as fake_err:
                with self.assertRaises(SystemExit) as cm:
                    execute_api_test("GET", "http://test.com", [], None)
        
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error making request: Connection error", fake_err.getvalue())

if __name__ == '__main__':
    unittest.main()
