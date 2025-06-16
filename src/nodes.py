"""
Node implementations for the Product Price Insurance System.
Simple approach with 3 main nodes using LLMs for intelligence.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from langgraph.prebuilt import create_react_agent
from .state import InsuranceState
from dotenv import load_dotenv
import statistics
from typing import Optional
from pydantic import BaseModel, Field 


class ProductURLs(BaseModel):
    """Structured output for extracted product URLs."""
    amazon: Optional[str] = Field(None, description="Amazon product page URL")
    walmart: Optional[str] = Field(None, description="Walmart product page URL") 
    bestbuy: Optional[str] = Field(None, description="Best Buy product page URL")

class ExtractedPrice(BaseModel):
    """Structured output for extracted price information."""
    price: Optional[float] = Field(None, description="Product price as a number (no currency symbols)")
    title: str = Field("", description="Product name/title")
    availability: str = Field("Unknown", description="Availability status (in stock, out of stock, etc.)")

load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

async def search_products(state: InsuranceState) -> InsuranceState:
    """
    Node 1: Search for product URLs on major platforms
    Uses LLM + MCP tools to find product pages
    """
    product_query = state["product_query"]
    
    try:
        # Configure MCP client for Bright Data
        browserai_config = {
            "mcpServers": {
                "BrightData": {
                    "command": "npx",
                    "args": ["@brightdata/mcp"],
                    "env": {
                        "API_TOKEN": os.getenv("BRIGHT_DATA_API_TOKEN"),
                        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE", "unblocker")
                    }
                }
            }
        }
        
        client = MCPClient.from_dict(browserai_config)
        adapter = LangChainAdapter()
        tools = await adapter.create_tools(client)
        
        # Create search agent
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt="""You are a product search specialist. Find product pages on major retail platforms.
            
            Your goal: Find direct product pages for the given product on:
            - Amazon
            - Walmart  
            - Best Buy
            
            Return the actual product page URLs, not search result pages.
            Focus on finding exact matches for the product."""
        )
        
        # Execute search
        search_prompt = f"""
        Find product pages for: {product_query}
        
        Search on these platforms and return direct product page URLs:
        1. Amazon - find the specific product page
        2. Walmart - find the specific product page  
        3. Best Buy - find the specific product page
        
        For each platform, provide the direct URL to the product page (not search results).
        """
        
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": search_prompt}]
        })
        
        structured_llm = llm.with_structured_output(ProductURLs)
        url_response = await structured_llm.ainvoke(
            f"Extract product URLs from these search results. Only include direct product page URLs, not search results:\n\n{result['messages'][-1].content}"
        )

        urls = {k: v for k, v in url_response.dict().items() if v is not None}
        
        return {
            **state,
            "search_results": urls
        }
        
    except Exception as e:
        return {
            **state,
            "search_results": {},
            "error": f"Product search failed: {str(e)}"
        }

async def extract_prices(state: InsuranceState) -> InsuranceState:
    """
    Node 2: Extract prices from found product URLs
    Uses MCP tools + LLM to extract price information
    """
    search_results = state.get("search_results", {})
    
    if not search_results:
        return {
            **state,
            "price_data": [],
            "error": "No product URLs found to extract prices from"
        }
    
    price_data = []
    
    try:
        # Configure MCP client
        browserai_config = {
            "mcpServers": {
                "BrightData": {
                    "command": "npx",
                    "args": ["@brightdata/mcp"],
                    "env": {
                        "API_TOKEN": os.getenv("BRIGHT_DATA_API_TOKEN"),
                        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE", "unblocker")
                    }
                }
            }
        }
        
        client = MCPClient.from_dict(browserai_config)
        adapter = LangChainAdapter()
        tools = await adapter.create_tools(client)
        
        # Create price extraction agent
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt="""You are a price extraction specialist. Extract accurate price information from product pages.
            
            For each URL provided:
            1. Use the relevant tool to fetch the product page
            2. Find the current price
            3. Extract the product title
            4. Note availability status
            IMPORTANT:
            For Amazon - use web_data_amazon_product tool
            For Walmart - use web_data_walmart_product tool
            For Best Buy - use web_data_bestbuy_products tool

            Be precise with price extraction - look for the main selling price, not MSRP or crossed-out prices."""
        )
        
        for platform, url in search_results.items():
            try:
                extraction_prompt = f"""
                Extract price information from this product page: {url}
                
                Find and return:
                1. Current price (as a number)
                2. Product title
                3. Availability status
                
                Platform: {platform}
                URL: {url}
                """
                
                result = await agent.ainvoke({
                    "messages": [{"role": "user", "content": extraction_prompt}]
                })
                
                # Use LLM to structure the extracted data
                structured_llm = llm.with_structured_output(ExtractedPrice)
                structured_data = await structured_llm.ainvoke(
                    f"Extract price, title, and availability from this product page data for {platform}:\n\n{result['messages'][-1].content}"
                )

                price_data.append({
                    "platform": platform,
                    "price": structured_data.price,
                    "title": structured_data.title,
                    "url": url,
                    "availability": structured_data.availability
                })
                
            except Exception as e:
                price_data.append({
                    "platform": platform,
                    "price": None,
                    "title": "",
                    "url": url,
                    "availability": "Error extracting",
                    "error": str(e)
                })
        
        return {
            **state,
            "price_data": price_data
        }
        
    except Exception as e:
        return {
            **state,
            "price_data": [],
            "error": f"Price extraction failed: {str(e)}"
        }

async def generate_report(state: InsuranceState) -> InsuranceState:
    """
    Node 3: Generate final price analysis report
    Uses simple calculations + LLM for formatting
    """
    price_data = state.get("price_data", [])
    product_query = state["product_query"]
    
    valid_prices = [item["price"] for item in price_data if item.get("price") is not None]
    
    if not valid_prices:
        return {
            **state,
            "final_report": f"❌ No prices found for {product_query}",
            "confidence_score": 0.0
        }
    
    median_price = statistics.median(valid_prices)
    average_price = statistics.mean(valid_prices)
    min_price = min(valid_prices)
    max_price = max(valid_prices)
    
    platforms_found = len(valid_prices)
    confidence_score = min(10.0, (platforms_found / 3.0) * 8.0 + 2.0)
    
    report_prompt = ChatPromptTemplate.from_messages([
        ("system", """Create a clean, professional price analysis report.
        
        Format with emojis and clear sections:
        - Product name as header
        - Price summary with median, average, range
        - Platform breakdown with individual prices
        - Confidence score and summary
        
        Make it easy to read and actionable."""),
        ("user", """Create a price analysis report:
        
        Product: {product}
        Median Price: ${median:.2f}
        Average Price: ${average:.2f}
        Price Range: ${min:.2f} - ${max:.2f}
        Confidence Score: {confidence:.1f}/10
        
        Platform Data:
        {platform_data}
        """)
    ])
    
    # Format platform data for the prompt
    platform_text = ""
    for item in price_data:
        if item.get("price"):
            platform_text += f"• {item['platform'].title()}: ${item['price']:.2f} - {item.get('title', 'N/A')}\n"
        else:
            platform_text += f"• {item['platform'].title()}: No price found\n"
    
    report_chain = report_prompt | llm
    report_response = await report_chain.ainvoke({
        "product": product_query,
        "median": median_price,
        "average": average_price,
        "min": min_price,
        "max": max_price,
        "confidence": confidence_score,
        "platform_data": platform_text
    })
    
    return {
        **state,
        "final_report": report_response.content,
        "confidence_score": confidence_score
    }