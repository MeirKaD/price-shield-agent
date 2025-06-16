"""
Simple state definition for the Product Price Insurance System.
Following the pattern shown - keep it simple with TypedDict.
"""

from typing import TypedDict, List, Optional, Dict

class InsuranceState(TypedDict):
    """Simple state for product price insurance workflow."""
    # Input
    product_query: str
    
    # Node outputs
    search_results: Dict[str, str]  # platform -> URL
    price_data: List[Dict[str, any]]  # extracted prices
    final_report: str
    
    # Optional fields
    error: Optional[str]
    confidence_score: Optional[float]