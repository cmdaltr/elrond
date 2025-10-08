"""
Web Backend Models

Pydantic models for API requests and responses.
"""

from elrond.web.backend.models.image import Image, ImageCreate, ImageResponse
from elrond.web.backend.models.analysis import (
    Analysis,
    AnalysisCreate,
    AnalysisResponse,
    AnalysisStatus,
)
from elrond.web.backend.models.progress import (
    ProgressUpdate,
    TaskProgress,
    OverallProgress,
)

__all__ = [
    "Image",
    "ImageCreate",
    "ImageResponse",
    "Analysis",
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisStatus",
    "ProgressUpdate",
    "TaskProgress",
    "OverallProgress",
]
