"""
Utility functions for working with workflow responses and Pydantic models
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pydantic import ValidationError
from .models import parse_workflow_response, WorkflowResponse, WorkflowResult


class WorkflowProcessor:
    """Helper class for processing workflow responses with Pydantic models"""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
    
    def process_workflow_result(self, raw_result: dict) -> Tuple[bool, Dict]:
        """
        Process a raw workflow result and return detection status and data
        
        Args:
            raw_result: Raw workflow response data
            
        Returns:
            Tuple of (is_habit_detected, prediction_data)
        """
        try:
            # Parse using Pydantic models
            workflow_response = parse_workflow_response(raw_result)
            first_result = workflow_response.first_result
            
            # Extract key information
            prediction_data = {
                'top_class': first_result.top_class,
                'confidence': first_result.detection_confidence,
                'has_detections': first_result.has_detection_predictions,
                'detection_count': len(first_result.detection_predictions.predictions) if first_result.has_detection_predictions else 0,
                'inference_id': first_result.classification_predictions.inference_id,
                'processing_time': first_result.classification_predictions.time,
                'image_size': {
                    'width': first_result.classification_predictions.image.width,
                    'height': first_result.classification_predictions.image.height
                }
            }
            
            # Add detection details if available
            if first_result.has_detection_predictions:
                prediction_data['detections'] = [
                    {
                        'class': det.class_,
                        'confidence': det.confidence,
                        'bounding_box': {
                            'x': det.x,
                            'y': det.y,
                            'width': det.width,
                            'height': det.height
                        },
                        'detection_id': det.detection_id
                    }
                    for det in first_result.detection_predictions.predictions
                ]
            
            # Check if it's a habit detection above threshold
            is_habit_detected = (
                first_result.is_chomping_detected and 
                first_result.detection_confidence >= self.confidence_threshold
            )
            
            return is_habit_detected, prediction_data
            
        except ValidationError as e:
            self.logger.warning(f"Validation error processing workflow result: {e}")
            return False, {'error': 'validation_failed', 'details': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected error processing workflow result: {e}")
            return False, {'error': 'processing_failed', 'details': str(e)}
    
    def get_habit_summary(self, results: List[WorkflowResult]) -> Dict:
        """
        Generate a summary of multiple workflow results
        
        Args:
            results: List of WorkflowResult objects
            
        Returns:
            Dictionary containing summary statistics
        """
        if not results:
            return {'total_results': 0, 'habit_detected': False}
        
        habit_detections = [r for r in results if r.is_chomping_detected]
        high_confidence_detections = [
            r for r in results 
            if r.is_chomping_detected and r.detection_confidence >= self.confidence_threshold
        ]
        
        return {
            'total_results': len(results),
            'habit_detected': len(habit_detections) > 0,
            'habit_detection_count': len(habit_detections),
            'high_confidence_detections': len(high_confidence_detections),
            'max_confidence': max(r.detection_confidence for r in results),
            'min_confidence': min(r.detection_confidence for r in results),
            'avg_confidence': sum(r.detection_confidence for r in results) / len(results),
            'detection_rate': len(habit_detections) / len(results) if results else 0,
            'classes_detected': list(set(r.top_class for r in results))
        }
    
    def is_valid_workflow_response(self, raw_result: dict) -> bool:
        """
        Check if a raw result can be parsed as a valid workflow response
        
        Args:
            raw_result: Raw workflow response data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parse_workflow_response(raw_result)
            return True
        except (ValidationError, Exception):
            return False
    
    def extract_bounding_boxes(self, result: WorkflowResult) -> List[Dict]:
        """
        Extract bounding box information from a workflow result
        
        Args:
            result: WorkflowResult object
            
        Returns:
            List of bounding box dictionaries
        """
        if not result.has_detection_predictions:
            return []
        
        return [
            {
                'class': det.class_,
                'confidence': det.confidence,
                'x': det.x,
                'y': det.y,
                'width': det.width,
                'height': det.height,
                'detection_id': det.detection_id,
                'center_x': det.x + det.width / 2,
                'center_y': det.y + det.height / 2,
                'area': det.width * det.height
            }
            for det in result.detection_predictions.predictions
        ]
    
    def filter_results_by_confidence(self, results: List[WorkflowResult], 
                                   min_confidence: float = None) -> List[WorkflowResult]:
        """
        Filter workflow results by minimum confidence threshold
        
        Args:
            results: List of WorkflowResult objects
            min_confidence: Minimum confidence threshold (uses instance threshold if None)
            
        Returns:
            Filtered list of WorkflowResult objects
        """
        threshold = min_confidence if min_confidence is not None else self.confidence_threshold
        return [r for r in results if r.detection_confidence >= threshold]
    
    def get_detection_timeline(self, results: List[WorkflowResult]) -> List[Dict]:
        """
        Create a timeline of detections from workflow results
        
        Args:
            results: List of WorkflowResult objects
            
        Returns:
            List of timeline entries
        """
        timeline = []
        
        for i, result in enumerate(results):
            # Handle case where output_image is None (no detections)
            if result.output_image is not None:
                timestamp = result.output_image.video_metadata.frame_timestamp
                frame_number = result.output_image.video_metadata.frame_number
            else:
                # Use current time as fallback when no output_image is available
                timestamp = datetime.now()
                frame_number = i  # Use sequence number as fallback frame number
            
            timeline.append({
                'sequence': i,
                'timestamp': timestamp,
                'frame_number': frame_number,
                'class': result.top_class,
                'confidence': result.detection_confidence,
                'is_habit': result.is_chomping_detected,
                'has_detections': result.has_detection_predictions,
                'detection_count': len(result.detection_predictions.predictions) if result.has_detection_predictions else 0
            })
        
        return timeline


def create_mock_workflow_response(top_class: str = "chomping", 
                                confidence: float = 0.85,
                                include_detections: bool = True) -> dict:
    """
    Create a mock workflow response for testing
    
    Args:
        top_class: The classification result
        confidence: Confidence score
        include_detections: Whether to include detection predictions
        
    Returns:
        Mock workflow response dictionary
    """
    response = {
        "output_image": {
            "type": "base64",
            "value": "",
            "video_metadata": {
                "video_identifier": "test_image",
                "frame_number": 0,
                "frame_timestamp": "2025-01-13T21:40:15.775942",
                "fps": 30,
                "measured_fps": None,
                "comes_from_video_file": None
            }
        },
        "top_class": top_class,
        "classification_predictions": {
            "inference_id": "mock-inference-id",
            "time": 0.1,
            "image": {
                "width": 640,
                "height": 640
            },
            "predictions": [
                {
                    "class": top_class,
                    "class_id": 1 if top_class == "chomping" else 0,
                    "confidence": confidence
                }
            ],
            "top": top_class,
            "confidence": confidence,
            "prediction_type": "classification",
            "parent_id": "test_image",
            "root_parent_id": "test_image"
        }
    }
    
    if include_detections:
        response["detection_predictions"] = {
            "image": {
                "width": 640,
                "height": 640
            },
            "predictions": [
                {
                    "width": 200.0,
                    "height": 300.0,
                    "x": 320.0,
                    "y": 240.0,
                    "confidence": confidence,
                    "class_id": 1 if top_class == "chomping" else 0,
                    "class": top_class,
                    "detection_id": "mock-detection-id",
                    "parent_id": "test_image"
                }
            ]
        }
    else:
        response["detection_predictions"] = None
    
    return response  # Return as single dict since that's the actual format 