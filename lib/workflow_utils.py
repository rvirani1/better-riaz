"""
Utility functions for working with workflow responses
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from .models import is_chomping_detected, get_top_class, get_confidence, process_workflow_result, has_detection_predictions


class WorkflowProcessor:
    """Helper class for processing workflow responses"""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
    
    def process_workflow_result(self, raw_result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a raw workflow result and return detection status and data
        
        Args:
            raw_result: Raw workflow response data
            
        Returns:
            Tuple of (is_habit_detected, prediction_data)
        """
        try:
            # Use the simple utility functions
            is_habit_detected, confidence = is_chomping_detected(raw_result, self.confidence_threshold)
            prediction_data = process_workflow_result(raw_result, self.confidence_threshold)
            
            self.logger.debug(f"Processed workflow result: habit_detected={is_habit_detected}, confidence={confidence}")
            return is_habit_detected, prediction_data
            
        except Exception as e:
            self.logger.error(f"Error processing workflow result: {e}")
            return False, {'error': 'processing_failed', 'details': str(e)}
    
    def is_valid_workflow_response(self, raw_result: Dict[str, Any]) -> bool:
        """
        Check if a raw result appears to be a valid workflow response
        
        Args:
            raw_result: Raw workflow response data
            
        Returns:
            True if it looks valid, False otherwise
        """
        try:
            # Check for basic required fields
            if not isinstance(raw_result, dict):
                return False
            
            # Check for classification predictions
            classification_predictions = raw_result.get('classification_predictions', {})
            if not isinstance(classification_predictions, dict):
                return False
            
            # Check for required fields in classification predictions
            required_fields = ['top', 'confidence']
            for field in required_fields:
                if field not in classification_predictions:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating workflow response: {e}")
            return False
    
    def get_habit_summary(self, raw_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of multiple workflow results
        
        Args:
            raw_results: List of raw workflow result dictionaries
            
        Returns:
            Dictionary containing summary statistics
        """
        if not raw_results:
            return {'total_results': 0, 'habit_detected': False}
        
        habit_detections = []
        high_confidence_detections = []
        confidences = []
        classes = []
        
        for result in raw_results:
            try:
                is_habit, confidence = is_chomping_detected(result, self.confidence_threshold)
                top_class = get_top_class(result)
                
                confidences.append(confidence)
                classes.append(top_class)
                
                if is_habit:
                    habit_detections.append(result)
                    
                if confidence >= self.confidence_threshold:
                    high_confidence_detections.append(result)
                    
            except Exception as e:
                self.logger.warning(f"Error processing result in summary: {e}")
                continue
        
        return {
            'total_results': len(raw_results),
            'habit_detected': len(habit_detections) > 0,
            'habit_detection_count': len(habit_detections),
            'high_confidence_detections': len(high_confidence_detections),
            'max_confidence': max(confidences) if confidences else 0.0,
            'min_confidence': min(confidences) if confidences else 0.0,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0.0,
            'detection_rate': len(habit_detections) / len(raw_results) if raw_results else 0.0,
            'classes_detected': list(set(classes))
        }
    
    def filter_results_by_confidence(self, raw_results: List[Dict[str, Any]], 
                                   min_confidence: float = None) -> List[Dict[str, Any]]:
        """
        Filter workflow results by minimum confidence threshold
        
        Args:
            raw_results: List of raw workflow result dictionaries
            min_confidence: Minimum confidence threshold (uses instance threshold if None)
            
        Returns:
            Filtered list of raw workflow result dictionaries
        """
        threshold = min_confidence if min_confidence is not None else self.confidence_threshold
        filtered_results = []
        
        for result in raw_results:
            try:
                confidence = get_confidence(result)
                if confidence >= threshold:
                    filtered_results.append(result)
            except Exception as e:
                self.logger.warning(f"Error filtering result: {e}")
                continue
        
        return filtered_results


def create_mock_workflow_response(top_class: str = "chomping", 
                                confidence: float = 0.85,
                                include_detections: bool = True) -> Dict[str, Any]:
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
    
    return response 