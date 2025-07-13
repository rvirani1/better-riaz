"""
Pydantic models for workflow result validation and parsing
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class VideoMetadata(BaseModel):
    """Video metadata information"""
    video_identifier: str
    frame_number: int
    frame_timestamp: datetime
    fps: int
    measured_fps: Optional[float] = None
    comes_from_video_file: Optional[bool] = None


class OutputImage(BaseModel):
    """Output image structure with base64 data and metadata"""
    type: str = "base64"
    value: str = ""
    video_metadata: VideoMetadata


class ImageInfo(BaseModel):
    """Image dimensions information"""
    width: int
    height: int


class ClassificationPrediction(BaseModel):
    """Individual classification prediction"""
    class_: str = Field(..., alias="class")
    class_id: int
    confidence: float
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class ClassificationPredictions(BaseModel):
    """Classification predictions structure"""
    inference_id: str
    time: float
    image: ImageInfo
    predictions: List[ClassificationPrediction]
    top: str
    confidence: float
    prediction_type: str = "classification"
    parent_id: str
    root_parent_id: str
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class DetectionPrediction(BaseModel):
    """Individual detection prediction with bounding box"""
    width: float
    height: float
    x: float
    y: float
    confidence: float
    class_id: int
    class_: str = Field(..., alias="class")
    detection_id: str
    parent_id: str
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class DetectionPredictions(BaseModel):
    """Detection predictions structure (can be empty)"""
    image: Optional[ImageInfo] = None
    predictions: List[DetectionPrediction] = []


class WorkflowResult(BaseModel):
    """Complete workflow result structure"""
    output_image: Optional[OutputImage] = None
    top_class: str
    classification_predictions: ClassificationPredictions
    detection_predictions: Optional[DetectionPredictions] = None
    
    @property
    def is_chomping_detected(self) -> bool:
        """Check if chomping was detected"""
        return self.top_class == "chomping"
    
    @property
    def detection_confidence(self) -> float:
        """Get the detection confidence"""
        return self.classification_predictions.confidence
    
    @property
    def has_detection_predictions(self) -> bool:
        """Check if detection predictions are present and not empty"""
        return (self.detection_predictions is not None and 
                len(self.detection_predictions.predictions) > 0)


class WorkflowResponse(BaseModel):
    """Top-level workflow response (list of results)"""
    results: List[WorkflowResult]
    
    @field_validator('results')
    @classmethod
    def validate_results(cls, v):
        if not v:
            raise ValueError('Results cannot be empty')
        return v
    
    @property
    def first_result(self) -> WorkflowResult:
        """Get the first result (convenience method)"""
        return self.results[0]
    
    @property
    def has_chomping_detection(self) -> bool:
        """Check if any result has chomping detection"""
        return any(result.is_chomping_detected for result in self.results)
    
    @property
    def max_confidence(self) -> float:
        """Get the maximum confidence across all results"""
        return max(result.detection_confidence for result in self.results)
    
    @property
    def chomping_results(self) -> List[WorkflowResult]:
        """Get only the results with chomping detection"""
        return [result for result in self.results if result.is_chomping_detected]


def parse_workflow_response(response_data: dict) -> WorkflowResponse:
    """
    Parse workflow response data into validated Pydantic models
    
    Args:
        response_data: Raw workflow response (single dict result)
        
    Returns:
        WorkflowResponse: Validated workflow response
        
    Raises:
        ValidationError: If the response doesn't match expected structure
    """
    # Wrap single dict result in a list for WorkflowResponse
    return WorkflowResponse(results=[response_data]) 