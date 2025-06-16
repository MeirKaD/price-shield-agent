# test_nodes.py
"""
Simple tester for individual nodes in the insurance POC.
Start with testing the first node (search_products).
"""

import asyncio
import os
from dotenv import load_dotenv
from src.state import InsuranceState
from src.nodes import search_products, extract_prices, generate_report

load_dotenv()

async def test_search_products():
    """Test the search_products node in isolation."""
    
    print("🧪 Testing Product Search Node")
    print("=" * 50)
    
    # Test cases
    test_products = [
        "iPhone 16 256GB",
        "MacBook Air M2", 
        "Samsung Galaxy S24"
    ]
    
    for product in test_products:
        print(f"\n📱 Testing product: {product}")
        print("-" * 30)
        
        # Create initial state
        initial_state: InsuranceState = {
            "product_query": product,
            "search_results": {},
            "price_data": [],
            "final_report": "",
            "error": None,
            "confidence_score": None
        }
        
        try:
            # Run the search_products node
            result = await search_products(initial_state)
            
            # Display results
            print(f"✅ Search completed")
            print(f"Product Query: {result['product_query']}")
            print(f"URLs Found: {len(result.get('search_results', {}))}")
            
            for platform, url in result.get('search_results', {}).items():
                print(f"  • {platform.title()}: {url}")
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
            
        except Exception as e:
            print(f"💥 Test failed: {str(e)}")
        
        print()

async def test_extract_prices():
    """Test the extract_prices node using known URLs."""
    
    print("🧪 Testing Price Extraction Node")
    print("=" * 50)
    
    # Use the URLs from your successful test
    test_state: InsuranceState = {
        "product_query": "LG 55\" TV",
        "search_results": {
            "amazon": "https://www.amazon.com/LG-55-Inch-Processor-AI-Powered-OLED55C4PUA/dp/B0CVRDK4P6",
            "walmart": "https://www.walmart.com/ip/LG-55-4K-UHD-Smart-TV-2160p-webOS-55UQ7070ZUE/332111459",
            "bestbuy": "https://www.bestbuy.com/site/lg-55-class-b4-series-oled-4k-uhd-smart-webos-tv-2024/6578057.p?skuId=6578057"
        },
        "price_data": [],
        "final_report": "",
        "error": None,
        "confidence_score": None
    }
    
    print(f"📱 Extracting prices for: {test_state['product_query']}")
    print(f"🔗 From {len(test_state['search_results'])} URLs")
    print()
    
    try:
        result = await extract_prices(test_state)
        
        print("✅ Price extraction completed")
        print(f"📊 Prices found: {len(result.get('price_data', []))}")
        print()
        
        for item in result.get('price_data', []):
            platform = item.get('platform', 'Unknown').title()
            price = item.get('price')
            title = item.get('title', 'N/A')
            availability = item.get('availability', 'Unknown')
            
            print(f"🏪 {platform}:")
            print(f"   💰 Price: ${price:.2f}" if price else "   💰 Price: Not found")
            print(f"   📦 Title: {title}")
            print(f"   ✅ Status: {availability}")
            
            if item.get('error'):
                print(f"   ❌ Error: {item['error']}")
            print()
        
        if result.get('error'):
            print(f"❌ Overall Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"💥 Test failed: {str(e)}")
        return None

async def test_generate_report():
    """Test the generate_report node using mock price data."""
    
    print("🧪 Testing Report Generation Node")
    print("=" * 50)
    
    # Mock price data (simulate successful price extraction)
    test_state: InsuranceState = {
        "product_query": "LG 55\" TV",
        "search_results": {},
        "price_data": [
            {
                "platform": "amazon",
                "price": 1299.99,
                "title": "LG 55\" OLED C4 Series 4K TV",
                "url": "https://amazon.com/...",
                "availability": "In Stock"
            },
            {
                "platform": "walmart", 
                "price": 1199.99,
                "title": "LG 55\" 4K UHD Smart TV",
                "url": "https://walmart.com/...",
                "availability": "In Stock"
            },
            {
                "platform": "bestbuy",
                "price": 1349.99,
                "title": "LG 55\" B4 Series OLED TV",
                "url": "https://bestbuy.com/...", 
                "availability": "Available"
            }
        ],
        "final_report": "",
        "error": None,
        "confidence_score": None
    }
    
    print(f"📱 Generating report for: {test_state['product_query']}")
    print(f"📊 Using {len(test_state['price_data'])} price points")
    print()
    
    try:
        result = await generate_report(test_state)
        
        print("✅ Report generation completed")
        print(f"🎯 Confidence Score: {result.get('confidence_score', 0):.1f}/10")
        print()
        print("📋 Generated Report:")
        print("=" * 50)
        print(result.get('final_report', 'No report generated'))
        print("=" * 50)
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"💥 Test failed: {str(e)}")
        return None

async def test_full_pipeline():
    """Test search + extract pipeline together."""
    
    product = input("Enter product name for full pipeline test: ").strip()
    if not product:
        product = "iPhone 16 256GB"  # Default
    
    print(f"\n🔄 Running full pipeline for: {product}")
    print("=" * 50)
    
    # Step 1: Search
    print("🔍 Step 1: Searching for product URLs...")
    initial_state: InsuranceState = {
        "product_query": product,
        "search_results": {},
        "price_data": [],
        "final_report": "",
        "error": None,
        "confidence_score": None
    }
    
    try:
        search_result = await search_products(initial_state)
        
        print(f"   ✅ Found {len(search_result.get('search_results', {}))} URLs")
        
        if not search_result.get('search_results'):
            print("   ❌ No URLs found, stopping pipeline")
            return None
        
        # Step 2: Extract prices
        print("\n💰 Step 2: Extracting prices...")
        price_result = await extract_prices(search_result)
        # Step 3: Generate report
        print("\n📋 Step 3: Generating report...")
        final_result = await generate_report(price_result)
        
        print(f"   ✅ Report generated with confidence: {final_result.get('confidence_score', 0):.1f}/10")
        valid_prices = [item for item in price_result.get('price_data', []) if item.get('price')]
        print(f"   ✅ Extracted {len(valid_prices)} valid prices")
        
        # Show results
        print("\n📋 Final Report:")
        print("=" * 60)
        print(final_result.get('final_report', 'No report generated'))
        print("=" * 60)
        
        return final_result
        
    except Exception as e:
        print(f"💥 Pipeline failed: {str(e)}")
        return None
async def test_single_product():
    """Test a single product search only."""
    
    product = input("Enter product name to search: ").strip()
    if not product:
        product = "iPhone 16 256GB"  # Default
    
    print(f"\n🔍 Searching for: {product}")
    
    initial_state: InsuranceState = {
        "product_query": product,
        "search_results": {},
        "price_data": [],
        "final_report": "",
        "error": None,
        "confidence_score": None
    }
    
    try:
        result = await search_products(initial_state)
        
        print("\n📊 Results:")
        print(f"Product: {result['product_query']}")
        print(f"URLs Found: {len(result.get('search_results', {}))}")
        
        for platform, url in result.get('search_results', {}).items():
            print(f"\n🏪 {platform.title()}:")
            print(f"   {url}")
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"\n💥 Test failed: {str(e)}")
        return None

def check_environment():
    """Check if required environment variables are set."""
    
    print("🔧 Environment Check")
    print("=" * 30)
    
    required_vars = [
        "BRIGHT_DATA_API_TOKEN",
        "GOOGLE_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please set them in your .env file")
        return False
    
    print("\n✅ All environment variables are set!")
    return True

async def main():
    """Main test runner."""
    
    print("🚀 Product Price Insurance - Node Tester")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        return
    
    while True:
        print("\nChoose test option:")
        print("1. Test predefined products (search only)")
        print("2. Test single product search")
        print("3. Test price extraction (LG TV URLs)")
        print("4. Test report generation (mock data)")
        print("5. Test full pipeline (search + extract + report)")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            await test_search_products()
        elif choice == "2":
            await test_single_product()
        elif choice == "3":
            await test_extract_prices()
        elif choice == "4":
            await test_generate_report()
        elif choice == "5":
            await test_full_pipeline()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    asyncio.run(main())