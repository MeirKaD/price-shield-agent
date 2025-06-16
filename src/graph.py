"""
Graph builder for the Product Price Insurance System.
Simple 3-node workflow following the pattern shown.
"""

from langgraph.graph import StateGraph
from .state import InsuranceState
from .nodes import search_products, extract_prices, generate_report

def create_insurance_graph():
    """Create and compile the insurance price analysis graph."""
    
    workflow = StateGraph(InsuranceState)
    
    workflow.add_node("search_products", search_products)
    workflow.add_node("extract_prices", extract_prices)
    workflow.add_node("generate_report", generate_report)
    
    workflow.add_edge("search_products", "extract_prices")
    workflow.add_edge("extract_prices", "generate_report")
    
    workflow.set_entry_point("search_products")
    workflow.set_finish_point("generate_report")
    
    return workflow.compile()