import os
from google.cloud import vision

class ImageRecognitionService:
    """
    A service for image recognition using Google Cloud Vision API.
    """

    def __init__(self):
        """
        Initializes the ImageRecognitionService.
        Requires Google Cloud credentials to be set up in the environment.
        """
        # TODO: Replace 'path/to/your/service-account-file.json' with the actual path to your service account file.
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/service-account-file.json'
        self.client = vision.ImageAnnotatorClient()

    def analyze_image(self, image_path: str) -> dict:
        """
        Analyzes an image using Google Cloud Vision API and returns suggested categories and attributes.
        """
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform label detection
            response = self.client.label_detection(image=image)
            labels = response.label_annotations

            # Perform text detection (OCR)
            response_text = self.client.text_detection(image=image)
            texts = response_text.text_annotations

            if response.error.message:
                raise Exception(
                    '{}\nFor more info on error messages, check: ' 
                    'https://cloud.google.com/apis/design/errors'.format(
                        response.error.message))

            # Process labels to determine category and attributes
            suggested_category = "Other School Supplies"
            suggested_attributes = {}
            confidence = 0.0

            if labels:
                # Use the label with the highest score as the primary category suggestion
                main_label = labels[0]
                suggested_category = main_label.description
                confidence = main_label.score

                # Extract other labels as attributes
                for label in labels[1:]:
                    suggested_attributes[label.description.lower()] = True

            # Extract text from the image to find potential size, brand, etc.
            if texts:
                full_text = texts[0].description
                # Simple parsing for size (look for "size" followed by a number or common size words)
                import re
                size_match = re.search(r'(size|sze|sz)[:\s]*([\d\w-]+)', full_text, re.IGNORECASE)
                if size_match:
                    suggested_attributes['size'] = size_match.group(2)

                # Simple parsing for color
                colors = ['black', 'white', 'grey', 'navy', 'blue', 'red', 'green', 'yellow']
                for color in colors:
                    if color in full_text.lower():
                        suggested_attributes['color'] = color.capitalize()
                        break
            
            return {
                "suggested_category": suggested_category,
                "suggested_attributes": suggested_attributes,
                "confidence": confidence
            }

        except Exception as e:
            print(f"An error occurred during image analysis: {e}")
            return {
                "suggested_category": "Error",
                "suggested_attributes": {},
                "confidence": 0.0,
                "error": str(e)
            }

    def get_mock_image_path(self, filename: str) -> str:
        """
        Returns a mock image path for testing purposes.
        """
        # In a real app, you'd have a proper way to access uploaded images.
        # For this mock, we'll just use a dummy path.
        return os.path.join("path", "to", "mock", "images", filename)
