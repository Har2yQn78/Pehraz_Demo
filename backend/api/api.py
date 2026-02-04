from ninja import Router, File
from ninja.files import UploadedFile
from typing import List
from .schemas import (
    HealthResponse,
    PlantIdentificationRequest,
    PlantIdentificationResponse,
    DiseaseDetectionRequest,
    DiseaseDetectionResponse,
    ErrorResponse
)
from .services import PlantNetService

router = Router()
plantnet_service = PlantNetService()


@router.get("/health", response=HealthResponse, tags=["Health"])
def health_check(request):
    return {
        "status": "ok",
        "message": "PlantNet API backend is running"
    }


@router.post("/identify", response={200: PlantIdentificationResponse, 400: ErrorResponse}, tags=["Identification"])
def identify_plant(
    request,
    image: UploadedFile = File(...),
    organs: str = "leaf"
):
    try:
        # Read image data
        image_data = image.read()

        # Validate image
        plantnet_service.validate_image(image_data)

        # Parse organs parameter
        organs_list = [organ.strip() for organ in organs.split(',')]

        # Call PlantNet API
        raw_result = plantnet_service.identify_plant(
            image_data=image_data,
            organs=organs_list,
            filename=image.name
        )

        # Parse and return result
        result = plantnet_service.parse_identification_result(raw_result)
        return 200, result

    except ValueError as e:
        return 400, {"error": "Validation Error", "detail": str(e)}
    except Exception as e:
        return 400, {"error": "Identification Error", "detail": str(e)}


@router.post("/detect-disease", response={200: DiseaseDetectionResponse, 400: ErrorResponse}, tags=["Disease Detection"])
def detect_disease(
    request,
    image: UploadedFile = File(...),
    organ: str = "leaf"
):
    try:
        # Read image data
        image_data = image.read()

        # Validate image
        plantnet_service.validate_image(image_data)

        # Call PlantNet Disease API
        raw_result = plantnet_service.detect_disease(
            image_data=image_data,
            organ=organ,
            filename=image.name
        )

        # Parse and return result
        result = plantnet_service.parse_disease_result(raw_result)
        return 200, result

    except ValueError as e:
        return 400, {"error": "Validation Error", "detail": str(e)}
    except Exception as e:
        # Disease detection might not be available
        return 400, {"error": "Disease Detection Error", "detail": str(e)}


@router.get("/organs", response=List[str], tags=["Info"])
def get_valid_organs(request):
    """Get list of valid plant organs for identification"""
    return ["leaf", "flower", "fruit", "bark", "habit", "other"]
