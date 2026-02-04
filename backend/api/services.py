import os
import requests
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO


class PlantNetService:
    BASE_URL = "https://my-api.plantnet.org/v2"
    DISEASE_URL = "https://my-api.plantnet.org/v2/diseases"

    def __init__(self):
        self.api_key = os.getenv('PLANTNET_API_KEY')
        self.disease_api_key = os.getenv('PLANTNET_DISEASE_API_KEY', self.api_key)
        self.project = os.getenv('PLANTNET_PROJECT', 'all')

        if not self.api_key:
            raise ValueError("PLANTNET_API_KEY not found in environment variables")

    def identify_plant(
        self,
        image_data: bytes,
        organs: List[str],
        filename: str = "image.jpg"
    ) -> Dict:
        # Validate organs
        valid_organs = ["leaf", "flower", "fruit", "bark", "habit", "other"]
        organs = [organ for organ in organs if organ in valid_organs]

        if not organs:
            organs = ["leaf"]  # Default to leaf

        # Prepare the API request
        url = f"{self.BASE_URL}/identify/{self.project}"
        params = {
            'api-key': self.api_key
        }

        # Send organs as form data, not URL params
        data = {
            'organs': organs  # Send as list
        }

        files = {
            'images': (filename, image_data, 'image/jpeg')
        }

        try:
            response = requests.post(url, params=params, data=data, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"PlantNet API error: {str(e)}")

    def detect_disease(
        self,
        image_data: bytes,
        organ: str = "leaf",
        filename: str = "image.jpg"
    ) -> Dict:
        if not self.disease_api_key:
            raise ValueError("PLANTNET_DISEASE_API_KEY not configured")

        # Prepare the API request
        url = f"{self.DISEASE_URL}/identify"
        params = {
            'api-key': self.disease_api_key,
            'organ': organ
        }

        files = {
            'images': (filename, image_data, 'image/jpeg')
        }

        try:
            response = requests.post(url, params=params, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Disease API might not be available or configured
            raise Exception(f"PlantNet Disease API error: {str(e)}")

    @staticmethod
    def validate_image(image_data: bytes, max_size_mb: int = 10) -> bool:
        # Check file size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"Image too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")

        # Try to open as image
        try:
            img = Image.open(BytesIO(image_data))
            img.verify()
            return True
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")

    def parse_identification_result(self, api_response: Dict) -> Dict:
        results = []

        if 'results' in api_response:
            for result in api_response['results']:
                species = result.get('species', {})
                score_data = result.get('score', 0)

                results.append({
                    'scientific_name': species.get('scientificNameWithoutAuthor', 'Unknown'),
                    'common_names': species.get('commonNames', []),
                    'score': round(score_data * 100, 2),  # Convert to percentage
                    'genus': species.get('genus', {}).get('scientificNameWithoutAuthor'),
                    'family': species.get('family', {}).get('scientificNameWithoutAuthor'),
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        return {
            'query': api_response.get('query', {}),
            'results': results,
            'best_match': results[0]['scientific_name'] if results else None,
            'remaining_identification_requests': api_response.get('remainingIdentificationRequests')
        }

    def parse_disease_result(self, api_response: Dict) -> Dict:
        results = []

        if 'results' in api_response:
            for result in api_response['results']:
                results.append({
                    'disease_name': result.get('disease', {}).get('name', 'Unknown'),
                    'score': round(result.get('score', 0) * 100, 2),
                    'description': result.get('disease', {}).get('description'),
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        return {
            'results': results,
            'best_match': results[0]['disease_name'] if results else None
        }
