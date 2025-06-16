"""
Main entry point for the Product Price Insurance System.
"""

import asyncio
from .graph import create_insurance_graph

async def run_price_analysis(product_query: str):
    """
    Run price analysis for a given product.
    
    Args:
        product_query: Product name/description (e.g., "iPhone 16 256GB")
        
    Returns:
        Final analysis report
    """
    # Create the graph
    graph = create_insurance_graph()
    
    # Run the analysis
    result = await graph.ainvoke({
        "product_query": product_query,
        "search_results": {},
        "price_data": [],
        "final_report": "",
        "error": None,
        "confidence_score": None
    })
    
    return result

# Example usage
if __name__ == "__main__":
    async def main():
        result = await run_price_analysis("iPhone 16 256GB")
        print(result["final_report"])
        if result.get("error"):
            print(f"Error: {result['error']}")
    
    asyncio.run(main())