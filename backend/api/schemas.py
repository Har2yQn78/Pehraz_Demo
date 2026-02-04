from typing import List, Optional
from ninja import Schema


class HealthResponse(Schema):
    status: str
    message: str


class PlantIdentificationRequest(Schema):
    organs: List[str]  # e.g., ["leaf", "flower", "fruit", "bark", "habit", "other"]


class PlantScore(Schema):
    scientific_name: str
    common_names: Optional[List[str]] = None
    score: float
    genus: Optional[str] = None
    family: Optional[str] = None


class PlantIdentificationResponse(Schema):
    query: dict
    results: List[PlantScore]
    best_match: Optional[str] = None
    remaining_identification_requests: Optional[int] = None


class DiseaseDetectionRequest(Schema):
    organ: str = "leaf"  # Default to leaf for disease detection


class DiseaseScore(Schema):
    disease_name: str
    score: float
    description: Optional[str] = None


class DiseaseDetectionResponse(Schema):
    results: List[DiseaseScore]
    best_match: Optional[str] = None


class ErrorResponse(Schema):
    error: str
    detail: Optional[str] = None
