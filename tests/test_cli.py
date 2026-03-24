import unittest
from unittest.mock import patch
import sys
import io

from pepe_tools import cli

class TestCLI(unittest.TestCase):
    def test_version(self):
        """Test the --version flag."""
        with patch('sys.argv', ['pepe-tools', '--version']):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new=io.StringIO()) as fake_out:
                    cli.main()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn('pepe-tools', fake_out.getvalue())

    def test_no_args_prints_help(self):
        with patch('sys.argv', ['pepe-tools']):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stdout', new=io.StringIO()) as fake_out:
                    cli.main()
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('usage:', fake_out.getvalue())

    @patch('pepe_tools.api_tester.execute_api_test')
    def test_api_command_dispatch(self, mock_execute):
        with patch('sys.argv', ['pepe-tools', 'api', 'GET', 'http://test.com']):
            cli.main()
        mock_execute.assert_called_once_with('GET', 'http://test.com', [], None)

    @patch('pepe_tools.load_tester.execute_load_test')
    def test_load_command_dispatch(self, mock_load):
        with patch('sys.argv', ['pepe-tools', 'load', 'config.json']):
            cli.main()
        mock_load.assert_called_once_with('config.json', None, None, [])

if __name__ == '__main__':
    unittest.main()
