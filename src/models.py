"""
Simple Pydantic models - only what we actually need.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class ProductPrice(BaseModel):
    """Simple product price result."""
    platform: str
    price: Optional[float] = None
    title: str = ""
    url: str = ""
    
class PriceSearchResult(BaseModel):
    """Simple search result for a product."""
    query: str
    platform: str
    search_url: str = ""
    product_url: str = ""
