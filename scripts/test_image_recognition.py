import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.image_recognition_service import ImageRecognitionService

class TestImageRecognitionService(unittest.TestCase):

    def setUp(self):
        """Set up a mock image file for testing."""
        self.mock_image_path = 'mock_image.jpg'
        with open(self.mock_image_path, 'wb') as f:
            f.write(b"fake image data")

    def tearDown(self):
        """Remove the mock image file after tests."""
        if os.path.exists(self.mock_image_path):
            os.remove(self.mock_image_path)

    @patch('app.services.image_recognition_service.vision.ImageAnnotatorClient')
    def test_analyze_image_success(self, MockImageAnnotatorClient):
        """Test successful image analysis with mock Google Cloud Vision API response."""
        # Mock the Google Cloud Vision API client and its responses
        mock_client = MagicMock()
        MockImageAnnotatorClient.return_value = mock_client

        # Mock label detection response
        mock_label_response = MagicMock()
        mock_label = MagicMock()
        mock_label.description = 'School Shoe'
        mock_label.score = 0.95
        mock_label_response.label_annotations = [mock_label]
        mock_label_response.error.message = ''
        
        # Mock text detection response
        mock_text_response = MagicMock()
        mock_text = MagicMock()
        mock_text.description = 'Size: 7\nColor: Black'
        mock_text_response.text_annotations = [mock_text]

        # Configure the client mock to return the mock responses
        mock_client.label_detection.return_value = mock_label_response
        mock_client.text_detection.return_value = mock_text_response

        # Instantiate the service and call the method
        service = ImageRecognitionService()
        result = service.analyze_image(self.mock_image_path)

        # Assertions
        self.assertEqual(result['suggested_category'], 'School Shoe')
        self.assertAlmostEqual(result['confidence'], 0.95)
        self.assertIn('size', result['suggested_attributes'])
        self.assertEqual(result['suggested_attributes']['size'], '7')
        self.assertIn('color', result['suggested_attributes'])
        self.assertEqual(result['suggested_attributes']['color'], 'Black')
        self.assertNotIn('error', result)

    @patch('app.services.image_recognition_service.vision.ImageAnnotatorClient')
    def test_analyze_image_api_error(self, MockImageAnnotatorClient):
        """Test image analysis when the API returns an error."""
        # Mock the Google Cloud Vision API client to return an error
        mock_client = MagicMock()
        MockImageAnnotatorClient.return_value = mock_client
        mock_response = MagicMock()
        mock_response.error.message = 'API Error'
        mock_client.label_detection.return_value = mock_response

        # Instantiate the service and call the method
        service = ImageRecognitionService()
        result = service.analyze_image(self.mock_image_path)

        # Assertions
        self.assertEqual(result['suggested_category'], 'Error')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('error', result)

    def test_analyze_image_file_not_found(self):
        """Test image analysis when the image file does not exist."""
        # Instantiate the service and call the method with a non-existent file
        service = ImageRecognitionService()
        result = service.analyze_image('non_existent_file.jpg')

        # Assertions
        self.assertEqual(result['suggested_category'], 'Error')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()
