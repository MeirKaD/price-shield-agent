# app.py
"""
Streamlit interface for the Product Price Insurance System.
Provides a chat-like interface with step-by-step results display.
"""

import streamlit as st
import asyncio
from datetime import datetime
from src.graph import create_insurance_graph
from src.state import InsuranceState
from typing import TypedDict, List, Optional, Dict
from src.nodes import search_products, extract_prices, generate_report

# Configure Streamlit page
st.set_page_config(
    page_title="🛡️ Product Price Insurance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .step-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .url-card {
        background-color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .price-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

def display_urls_step(search_results: Dict[str, str]):
    """Display the URL extraction step results."""
    st.markdown("### 🔍 Step 1: Product URLs Found")
    
    if not search_results:
        st.markdown('<div class="error-box">❌ No product URLs found</div>', unsafe_allow_html=True)
        return
    
    st.markdown(f'<div class="success-box">✅ Found {len(search_results)} product URLs</div>', unsafe_allow_html=True)
    
    for platform, url in search_results.items():
        platform_emoji = {"amazon": "🛒", "walmart": "🏪", "bestbuy": "🔵"}.get(platform, "🏬")
        
        st.markdown(f"""
        <div class="url-card">
            <strong>{platform_emoji} {platform.title()}</strong><br>
            <a href="{url}" target="_blank">{url}</a>
        </div>
        """, unsafe_allow_html=True)

def display_prices_step(price_data: List[Dict]):
    """Display the price extraction step results."""
    st.markdown("### 💰 Step 2: Price Data Extracted")
    
    if not price_data:
        st.markdown('<div class="error-box">❌ No price data extracted</div>', unsafe_allow_html=True)
        return
    
    valid_prices = [item for item in price_data if item.get('price')]
    st.markdown(f'<div class="success-box">✅ Extracted {len(valid_prices)} valid prices from {len(price_data)} platforms</div>', unsafe_allow_html=True)
    
    for item in price_data:
        platform = item.get('platform', 'Unknown')
        price = item.get('price')
        title = item.get('title', 'N/A')
        availability = item.get('availability', 'Unknown')
        
        platform_emoji = {"amazon": "🛒", "walmart": "🏪", "bestbuy": "🔵"}.get(platform, "🏬")
        
        if price:
            price_display = f"<strong>💰 ${price:.2f}</strong>"
            card_style = "price-card"
        else:
            price_display = "<strong>❌ Price not found</strong>"
            card_style = "price-card"
        
        st.markdown(f"""
        <div class="{card_style}">
            <strong>{platform_emoji} {platform.title()}</strong><br>
            {price_display}<br>
            <small>📦 {title}</small><br>
            <small>✅ {availability}</small>
        </div>
        """, unsafe_allow_html=True)

def display_final_report(final_report: str, confidence_score: float):
    """Display the final analysis report."""
    st.markdown("### 📋 Step 3: Final Analysis Report")
    
    # Confidence indicator
    if confidence_score >= 8:
        confidence_color = "🟢"
        confidence_text = "High Confidence"
    elif confidence_score >= 6:
        confidence_color = "🟡"
        confidence_text = "Medium Confidence"
    else:
        confidence_color = "🔴"
        confidence_text = "Low Confidence"
    
    st.markdown(f"""
    <div class="success-box">
        {confidence_color} <strong>{confidence_text}</strong> - Confidence Score: {confidence_score:.1f}/10
    </div>
    """, unsafe_allow_html=True)
    
    # Display the formatted report
    st.markdown("#### 📊 Price Analysis")
    st.markdown(final_report)

async def run_analysis_with_progress(product_query: str, progress_callback=None):
    """Run analysis with step-by-step progress reporting."""
    graph = create_insurance_graph()
    
    initial_state: InsuranceState = {
        "product_query": product_query,
        "search_results": {},
        "price_data": [],
        "final_report": "",
        "error": None,
        "confidence_score": None
    }
    
    # Step 1: Search for URLs
    if progress_callback:
        progress_callback("search", "🔍 Searching for product URLs...", 33)
    
    from src.nodes import search_products
    search_result = await search_products(initial_state)
    
    if progress_callback:
        progress_callback("search_complete", search_result.get("search_results", {}), 33)
    
    if search_result.get("error") or not search_result.get("search_results"):
        return search_result
    
    # Step 2: Extract prices
    if progress_callback:
        progress_callback("extract", "💰 Extracting prices from found URLs...", 66)
    
    from src.nodes import extract_prices
    price_result = await extract_prices(search_result)
    
    if progress_callback:
        progress_callback("extract_complete", price_result.get("price_data", []), 66)
    
    if price_result.get("error"):
        return price_result
    
    # Step 3: Generate report
    if progress_callback:
        progress_callback("report", "📋 Generating final analysis report...", 100)
    
    from src.nodes import generate_report
    final_result = await generate_report(price_result)
    
    if progress_callback:
        progress_callback("complete", final_result, 100)
    
    return final_result

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🛡️ Product Price Insurance System</div>', unsafe_allow_html=True)
    st.markdown("Find and compare prices across major retailers with AI-powered analysis")
    
    # Sidebar with instructions
    with st.sidebar:
        st.markdown("### 📝 How it works")
        st.markdown("""
        1. **🔍 Search**: Find product pages on Amazon, Walmart, and Best Buy
        2. **💰 Extract**: Get current prices and product details
        3. **📊 Analyze**: Generate comprehensive price analysis report
        """)
        
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Be specific with product names
        - Include brand, model, and key specs
        - Examples: "iPhone 16 256GB", "Samsung 55 inch 4K TV"
        """)
    
    # Main chat interface
    st.markdown("### 💬 Product Analysis Chat")
    
    # Display chat history
    if st.session_state.chat_history:
        for entry in st.session_state.chat_history:
            # User message
            with st.chat_message("user"):
                st.write(entry["query"])
            
            # Assistant response with detailed breakdown
            with st.chat_message("assistant"):
                if entry.get("error"):
                    st.markdown(f'<div class="error-box">❌ {entry["error"]}</div>', unsafe_allow_html=True)
                else:
                    # Show step-by-step results
                    if entry.get("search_results"):
                        display_urls_step(entry["search_results"])
                    
                    if entry.get("price_data"):
                        display_prices_step(entry["price_data"])
                    
                    if entry.get("final_report"):
                        display_final_report(entry["final_report"], entry.get("confidence_score", 0))
    
    # Chat input
    # Chat input
    if prompt := st.chat_input("Enter a product name to analyze (e.g., 'iPhone 16 256GB')"):
        # Add user message to chat
        with st.chat_message("user"):
            st.write(prompt)
        
        # Show assistant response with real-time progress
        with st.chat_message("assistant"):
            # Create containers for dynamic updates
            progress_container = st.container()
            results_container = st.container()
            
            # Progress tracking
            progress_bar = None
            status_text = None
            urls_displayed = False
            prices_displayed = False
            
            def progress_callback(stage, data, progress_value):
                nonlocal progress_bar, status_text, urls_displayed, prices_displayed
                
                with progress_container:
                    if progress_bar is None:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    progress_bar.progress(progress_value)
                    
                    if stage == "search":
                        status_text.text(data)
                    elif stage == "search_complete":
                        status_text.text("✅ URLs found! Moving to price extraction...")
                        # Show URLs immediately
                        with results_container:
                            if not urls_displayed:
                                display_urls_step(data)
                                urls_displayed = True
                    elif stage == "extract":
                        status_text.text(data)
                    elif stage == "extract_complete":
                        status_text.text("✅ Prices extracted! Generating report...")
                        # Show prices immediately
                        with results_container:
                            if not prices_displayed:
                                display_prices_step(data)
                                prices_displayed = True
                    elif stage == "report":
                        status_text.text(data)
                    elif stage == "complete":
                        status_text.text("✅ Analysis complete!")
                        # Show final report
                        with results_container:
                            if data.get("final_report"):
                                display_final_report(data["final_report"], data.get("confidence_score", 0))
            
            try:
                # Run the analysis with progress callbacks
                result = asyncio.run(run_analysis_with_progress(prompt, progress_callback))
                
                # Clear progress indicators after completion
                progress_container.empty()
                
                # Handle errors
                if result.get("error"):
                    st.markdown(f'<div class="error-box">❌ {result["error"]}</div>', unsafe_allow_html=True)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": prompt,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    **result
                })
            
            except Exception as e:
                # Clear progress indicators
                progress_container.empty()
                
                error_msg = f"Analysis failed: {str(e)}"
                st.markdown(f'<div class="error-box">❌ {error_msg}</div>', unsafe_allow_html=True)
                
                # Add error to chat history
                st.session_state.chat_history.append({
                    "query": prompt,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": error_msg
                })
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()