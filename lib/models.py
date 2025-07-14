"""
Simple utility functions for safely accessing workflow response values
"""

from typing import Dict, Any, Tuple
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
