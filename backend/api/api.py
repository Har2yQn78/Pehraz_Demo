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
from .services import PlantNetService, PlantIdDiseaseService

router = Router()
plantnet_service = PlantNetService()
_plant_id_disease_service = None


def get_plant_id_disease_service():
    """Lazy init so server can start without PLANT_ID_API_KEY (required only for disease detection)."""
    global _plant_id_disease_service
    if _plant_id_disease_service is None:
        _plant_id_disease_service = PlantIdDiseaseService()
    return _plant_id_disease_service


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
        # Read image data ONCE
        image_data = image.read()

        # Store filename before any processing
        filename = image.name

        # Validate image (now safely without corrupting data)
        plantnet_service.validate_image(image_data)

        # Parse organs parameter
        organs_list = [organ.strip() for organ in organs.split(',')]

        # Call PlantNet API with the original image_data
        raw_result = plantnet_service.identify_plant(
            image_data=image_data,
            organs=organs_list,
            filename=filename
        )

        # Parse and return result
        result = plantnet_service.parse_identification_result(raw_result)
        return 200, result

    except ValueError as e:
        return 400, {"error": "Validation Error", "detail": str(e)}
    except Exception as e:
        return 400, {"error": "Identification Error", "detail": str(e)}


@router.get("/disease-models", response=List[dict], tags=["Disease Detection"])
def list_disease_models(request):
    """Return available disease detection models for frontend selector."""
    return [
        {"id": "plantid", "name": "Plant.id", "description": "Kindwise Health Assessment (recommended)"},
        {"id": "plantnet", "name": "PlantNet", "description": "PlantNet Disease API"},
    ]


@router.post("/detect-disease", response={200: DiseaseDetectionResponse, 400: ErrorResponse}, tags=["Disease Detection"])
def detect_disease(
    request,
    image: UploadedFile = File(...),
    organ: str = "leaf",
    model: str = "plantid"
):
    """
    Run disease detection. Use query param model=plantid (default) or model=plantnet.
    """
    try:
        image_data = image.read()
        filename = image.name
        plantnet_service.validate_image(image_data)

        model = (model or "plantid").strip().lower()
        if model not in ("plantid", "plantnet"):
            return 400, {
                "error": "Validation Error",
                "detail": f"Invalid model '{model}'. Use 'plantid' or 'plantnet'.",
            }

        if model == "plantid":
            disease_service = get_plant_id_disease_service()
            raw_result = disease_service.detect_disease(
                image_data=image_data, organ=organ, filename=filename
            )
            result = disease_service.parse_disease_result(raw_result)
        else:
            # PlantNet disease API
            if not plantnet_service.disease_api_key:
                return 400, {
                    "error": "Configuration Error",
                    "detail": "PLANTNET_DISEASE_API_KEY not set. Required for PlantNet disease model.",
                }
            raw_result = plantnet_service.detect_disease(
                image_data=image_data, organ=organ, filename=filename
            )
            result = plantnet_service.parse_disease_result(raw_result)

        return 200, result

    except ValueError as e:
        return 400, {"error": "Validation Error", "detail": str(e)}
    except Exception as e:
        return 400, {"error": "Disease Detection Error", "detail": str(e)}


@router.get("/organs", response=List[str], tags=["Info"])
def get_valid_organs(request):
    """Get list of valid plant organs for identification"""
    return ["leaf", "flower", "fruit", "bark", "habit", "other"]
