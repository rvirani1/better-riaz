"""
Simple utility functions for safely accessing workflow response values
"""

from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def is_chomping_detected(workflow_result: Dict[str, Any], confidence_threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Check if chomping was detected in the workflow result with confidence above threshold
    
    Args:
        workflow_result: Raw workflow response dictionary
        confidence_threshold: Minimum confidence threshold (default 0.5)
        
    Returns:
        Tuple of (is_chomping_detected, confidence_score)
    """
    try:
        # Check if we have classification predictions
        classification_predictions = workflow_result.get('classification_predictions', {})
        if not classification_predictions:
            logger.debug("No classification_predictions found in workflow result")
            return False, 0.0
        
        # Get the top class and confidence
        top_class = classification_predictions.get('top', '')
        confidence = classification_predictions.get('confidence', 0.0)
        
        # Check if it's chomping and above threshold
        is_chomping = top_class == 'chomping'
        above_threshold = confidence >= confidence_threshold
        
        logger.debug(f"Top class: {top_class}, Confidence: {confidence}, Threshold: {confidence_threshold}")
        
        return is_chomping and above_threshold, confidence
        
    except Exception as e:
        logger.error(f"Error checking chomping detection: {e}")
        return False, 0.0


def get_top_class(workflow_result: Dict[str, Any]) -> str:
    """
    Get the top classification class from the workflow result
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        Top classification class or empty string if not found
    """
    try:
        # Try top_class first (if available at root level)
        if 'top_class' in workflow_result:
            return workflow_result['top_class']
        
        # Fall back to classification_predictions.top
        classification_predictions = workflow_result.get('classification_predictions', {})
        return classification_predictions.get('top', '')
        
    except Exception as e:
        logger.error(f"Error getting top class: {e}")
        return ''


def get_confidence(workflow_result: Dict[str, Any]) -> float:
    """
    Get the confidence score from the workflow result
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        Confidence score or 0.0 if not found
    """
    try:
        classification_predictions = workflow_result.get('classification_predictions', {})
        return classification_predictions.get('confidence', 0.0)
        
    except Exception as e:
        logger.error(f"Error getting confidence: {e}")
        return 0.0


def get_processing_time(workflow_result: Dict[str, Any]) -> float:
    """
    Get the processing time from the workflow result
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        Processing time in seconds or 0.0 if not found
    """
    try:
        classification_predictions = workflow_result.get('classification_predictions', {})
        return classification_predictions.get('time', 0.0)
        
    except Exception as e:
        logger.error(f"Error getting processing time: {e}")
        return 0.0


def get_inference_id(workflow_result: Dict[str, Any]) -> str:
    """
    Get the inference ID from the workflow result
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        Inference ID or empty string if not found
    """
    try:
        classification_predictions = workflow_result.get('classification_predictions', {})
        return classification_predictions.get('inference_id', '')
        
    except Exception as e:
        logger.error(f"Error getting inference ID: {e}")
        return ''


def get_image_dimensions(workflow_result: Dict[str, Any]) -> Tuple[int, int]:
    """
    Get image dimensions from the workflow result
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        Tuple of (width, height) or (0, 0) if not found
    """
    try:
        classification_predictions = workflow_result.get('classification_predictions', {})
        image_info = classification_predictions.get('image', {})
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        return width, height
        
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        return 0, 0


def has_detection_predictions(workflow_result: Dict[str, Any]) -> bool:
    """
    Check if the workflow result has detection predictions
    
    Args:
        workflow_result: Raw workflow response dictionary
        
    Returns:
        True if detection predictions are present and not empty
    """
    try:
        detection_predictions = workflow_result.get('detection_predictions')
        if detection_predictions is None:
            return False
        
        # Handle both dictionary format and Detections object
        if isinstance(detection_predictions, dict):
            predictions = detection_predictions.get('predictions', [])
            return len(predictions) > 0
        
        # Handle Detections object (has xyxy attribute)
        if hasattr(detection_predictions, 'xyxy') and detection_predictions.xyxy is not None:
            return len(detection_predictions.xyxy) > 0
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking detection predictions: {e}")
        return False


def process_workflow_result(workflow_result: Dict[str, Any], confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Process a workflow result and extract key information
    
    Args:
        workflow_result: Raw workflow response dictionary
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        Dictionary with processed information
    """
    is_habit_detected, confidence = is_chomping_detected(workflow_result, confidence_threshold)
    
    return {
        'is_habit_detected': is_habit_detected,
        'top_class': get_top_class(workflow_result),
        'confidence': confidence,
        'above_threshold': confidence >= confidence_threshold,
        'has_detections': has_detection_predictions(workflow_result),
        'processing_time': get_processing_time(workflow_result),
        'inference_id': get_inference_id(workflow_result),
        'image_dimensions': get_image_dimensions(workflow_result),
        'raw_available': {
            'classification_predictions': 'classification_predictions' in workflow_result,
            'detection_predictions': 'detection_predictions' in workflow_result,
            'output_image': 'output_image' in workflow_result,
            'top_class': 'top_class' in workflow_result
        }
    } 