import base64
import os
import requests
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO


class PlantIdDiseaseService:
    """
    Disease detection using plant.id API v3 Health Assessment.
    Docs: https://documenter.getpostman.com/view/24599534/2s93z5A4v2
    See also: https://github.com/flowerchecker/plant-id-examples (Health Assessment)
    """
    BASE_URL = "https://api.plant.id/v3/identification"

    def __init__(self):
        # Get API key from env (plant.id / Kindwise). Get a key at https://admin.kindwise.com
        self.api_key = os.getenv('PLANT_ID_API_KEY') or os.getenv('PLANTID_API_KEY')
        if not self.api_key:
            raise ValueError(
                "PLANT_ID_API_KEY (or PLANTID_API_KEY) not set. "
                "Required for disease detection. Get a key at https://admin.kindwise.com"
            )

    def detect_disease(
        self,
        image_data: bytes,
        organ: str = "leaf",
        filename: str = "image.jpg"
    ) -> Dict:
        """
        Run health assessment (disease detection) via plant.id API v3.
        Uses identification endpoint with health='only' and disease_details for rich results.
        """
        images_b64 = [base64.b64encode(image_data).decode('ascii')]
        payload = {
            'images': images_b64,
            'health': 'only',
        }
        params = {
            'details': 'local_name,description,treatment,common_names',
        }
        headers = {
            'Api-Key': self.api_key,
            'Content-Type': 'application/json',
        }
        try:
            response = requests.post(
                self.BASE_URL,
                params=params,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                err = response.json()
                raise Exception(f"plant.id API error: {response.status_code} - {err}")
            except Exception:
                raise Exception(f"plant.id API error: {response.status_code} - {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"plant.id API error: {str(e)}")

    @staticmethod
    def parse_disease_result(api_response: Dict) -> Dict:
        """
        Map plant.id health assessment response to our DiseaseDetectionResponse shape.
        Expects result.disease.suggestions with name, probability, details (description, etc.).
        """
        results = []
        result = api_response.get('result') or {}
        disease = result.get('disease') or {}
        suggestions = disease.get('suggestions') or []

        for item in suggestions:
            name = item.get('name') or 'Unknown'
            prob = item.get('probability', 0)
            details = item.get('details') or {}
            description = details.get('description')

            results.append({
                'disease_name': name,
                'score': round(prob * 100, 2),
                'description': description,
            })

        results.sort(key=lambda x: x['score'], reverse=True)

        return {
            'results': results,
            'best_match': results[0]['disease_name'] if results else None,
        }


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
        """
        Identify plant using PlantNet API.

        CRITICAL: According to official PlantNet documentation, organs must be
        sent as SEPARATE form fields, one per image, NOT as a list.

        Example from official docs:
        form.append('organs', 'flower');
        form.append('images', image1);
        form.append('organs', 'leaf');
        form.append('images', image2);
        """
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

        # CRITICAL FIX: For a single image with multiple organ types,
        # we need to send the FIRST organ that matches
        # According to PlantNet docs: "Number of values for organs must match number of input images"
        # Since we have 1 image, we send 1 organ (the first one in the list)

        # Build multipart form data manually using requests
        # We send organs as separate fields to match the API expectation
        files = {
            'images': (filename, image_data, 'image/jpeg')
        }

        # Send only the FIRST organ since we have ONE image
        # This matches the API requirement: same number of organs as images
        data = {
            'organs': organs[0]  # Single organ for single image
        }

        try:
            response = requests.post(url, params=params, files=files, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try to get error message from response
            try:
                error_detail = response.json()
                raise Exception(f"PlantNet API error: {response.status_code} - {error_detail}")
            except:
                raise Exception(f"PlantNet API error: {response.status_code} - {response.text[:200]}")
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

        url = f"{self.DISEASE_URL}/identify"
        params = {
            'api-key': self.disease_api_key
        }

        files = {
            'images': (filename, image_data, 'image/jpeg')
        }

        try:
            response = requests.post(url, params=params, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"PlantNet Disease API error: {str(e)}")

    @staticmethod
    def validate_image(image_data: bytes, max_size_mb: int = 10) -> bool:
        """
        Validate image without corrupting the data.

        IMPORTANT: Do NOT use img.verify() - it corrupts the file pointer!
        """
        # Check file size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"Image too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")

        # Validate it's a real image
        try:
            img = Image.open(BytesIO(image_data))
            # Check format is valid (raises exception if invalid)
            if img.format is None:
                raise ValueError("Cannot determine image format")
            # Load image data to ensure it's valid
            img.load()
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
                # Disease API returns 'name' with EPPO code and 'score' directly
                disease_name = result.get('name', 'Unknown')
                score = result.get('score', 0)

                results.append({
                    'disease_name': disease_name,
                    'score': round(score * 100, 2),  # Convert to percentage
                    'description': None,  # Description not in basic response
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        return {
            'results': results,
            'best_match': results[0]['disease_name'] if results else None
        }
