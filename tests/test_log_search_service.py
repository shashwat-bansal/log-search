import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from app.api import app


class TestLogSearchAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_search_logs_local_no_results(self):
        with patch('app.api.get_log_source', return_value='local'):
            response = self.app.post('/search-logs', json={
                'searchKeyword': 'nonexistent',
                'from': '2023-01-01 00:00:00',
                'to': '2023-01-01 23:59:59'
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['metadata']['responseCode'], 200)
            self.assertEqual(data['metadata']['resultSize'], 0)

    def test_search_logs_local_with_results(self):
        with patch('app.api.get_log_source', return_value='local'):
            response = self.app.post('/search-logs', json={
                'searchKeyword': 'Log',
                'from': '2023-11-24 00:00:00',
                'to': '2023-11-26 23:59:59'
            })
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['metadata']['responseCode'], 200)
            self.assertEqual(data['metadata']['resultSize'], 9)

    @patch('app.api.get_s3_client')
    def test_search_logs_s3_with_results(self, mock_s3_client):
        mock_s3_client.return_value.get_object.return_value = {
            'Body': MagicMock(spec=BytesIO, read=lambda: b'2023-01-01 00:00:00 - Log entry 1\n')
        }

        with patch('app.api.get_log_source', return_value='s3'):
            response = self.app.post('/search-logs', json={
                'searchKeyword': 'test',
                'from': '2023-01-01 00:00:00',
                'to': '2023-01-01 23:59:59'
            })
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['metadata']['responseCode'], 200)
            self.assertEqual(data['metadata']['resultSize'], 1)
            self.assertIn('Log entry 1', data['result'][0])


if __name__ == '__main__':
    unittest.main()
