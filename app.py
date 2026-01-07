import streamlit as st
import pandas as pd
import time
import io
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="Arbitrage Profit Master",
    page_icon="💰",
    layout="wide"
)

# --- Custom CSS for the "V8 Look" ---
# This CSS replicates the styling from your HTML prototype, including tooltips and image hover-zoom.
st.markdown("""
<style>
    /* General Styling */
    .stApp {
        background-color: #f8fafc; /* bg-slate-50 */
    }
    .main-container {
        border: 1px solid #e2e8f0; /* border-slate-200 */
        background-color: white;
        border-radius: 1.5rem; /* rounded-2xl */
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1); /* shadow-xl */
        overflow: hidden;
    }
    
    /* Custom Table Styling */
    .product-table-header {
        background-color: #f8fafc; /* bg-slate-50 */
        font-size: 0.75rem; /* text-xs */
        text-transform: uppercase;
        font-weight: 700;
        color: #64748b; /* text-slate-500 */
        letter-spacing: 0.05em;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #f1f5f9; /* divide-slate-100 */
    }
    .product-row {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #f1f5f9; /* divide-slate-50 */
        transition: background-color 0.2s ease-in-out;
    }
    .product-row:hover {
        background-color: #f8fafc; /* hover:bg-slate-50 */
    }
    .product-row:last-child {
        border-bottom: none;
    }
    .product-image-container {
        position: relative;
    }
    .product-image-thumb {
        width: 4rem; /* w-16 */
        height: 4rem; /* h-16 */
        object-fit: contain;
        background-color: white;
        padding: 0.25rem;
        border-radius: 0.375rem; /* rounded-md */
        border: 1px solid #e2e8f0; /* border-slate-200 */
    }
    .product-image-zoom {
        position: absolute;
        left: 100%;
        top: 0;
        width: 256px;
        height: 256px;
        object-fit: contain;
        background-color: white;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid #cbd5e1;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
        z-index: 99;
        display: none; /* Hidden by default */
        margin-left: 10px;
    }
    .product-image-container:hover .product-image-zoom {
        display: block; /* Show on hover */
    }
    
    /* Tooltip Styling */
    .tooltip {
      position: relative;
      display: inline-block;
      border-bottom: 1px dotted #94a3b8; /* border-slate-400 */
      cursor: help;
    }
    .tooltip .tooltiptext {
      visibility: hidden;
      width: 220px;
      background-color: #1e293b; /* bg-slate-800 */
      color: #fff;
      text-align: center;
      border-radius: 6px;
      padding: 5px;
      position: absolute;
      z-index: 1;
      bottom: 125%;
      left: 50%;
      margin-left: -110px;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
      visibility: visible;
      opacity: 1;
    }

    /* JavaScript-powered Copy Button */
    .copy-btn {
        background-color: white;
        border-left: 1px solid #e2e8f0;
        padding: 4px 6px;
        cursor: pointer;
    }
    .copy-btn:hover {
        background-color: #f1f5f9;
    }
    .copy-btn svg {
        width: 12px;
        height: 12px;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


# --- Mock API Service ---
# In a real app, this would use the 'google-search-results' library to call SerpApi.
# @st.cache_data is used to cache results to avoid redundant calls, just like the prototype.
@st.cache_data
def find_lowest_price(upc, api_key):
    """Mocks fetching the lowest price for a given UPC."""
    if not upc or not api_key:
        return 0, "Missing UPC or API Key."

    # Simulate network latency and potential failures
    time.sleep(0.5 + time.time() % 1)
    if time.time() % 10 < 1: # 10% failure rate
        return 0, "Product not found or API error."
    
    # Simulate a random price
    price = 20 + (hash(upc) % 80) + (time.time() % 5)
    return round(price, 2), None

# --- Data Processing Functions ---
def parse_keepa_csv(uploaded_file):
    """Parses the uploaded Keepa CSV file into a Pandas DataFrame."""
    try:
        df = pd.read_csv(uploaded_file)
        required_cols = ['Image', 'Title', 'ASIN', 'Product Codes: UPC', 'Buy Box Price', 'FBA Fees']
        # Validate required columns
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            st.error(f"Error: Your CSV is missing the following required columns: {', '.join(missing)}")
            return None
        # Clean up data - fill NaNs
        df['Product Codes: UPC'] = df['Product Codes: UPC'].fillna('')
        df = df.dropna(subset=['Buy Box Price', 'FBA Fees'])
        return df[required_cols]
    except Exception as e:
        st.error(f"An error occurred while parsing the CSV file: {e}")
        return None

def df_to_csv_download_link(df):
    """Generates a link to download the DataFrame as a CSV."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="arbitrage-analysis.csv">Download CSV File</a>'

# --- HTML Rendering Functions for the Custom Table ---
def render_product_row_html(row):
    """Generates the HTML for a single product row to match the prototype's style."""
    is_profitable = row['Net Profit'] > 0
    profit_color = "text-emerald-700 bg-emerald-100 border-emerald-200" if is_profitable else "text-slate-400 bg-slate-100 border-slate-200"
    roi_color = "text-emerald-600" if is_profitable else "text-slate-400"
    profit_sign = "+" if is_profitable else ""
    
    # Tooltip definitions
    total_cost_tooltip = "The sum of COGS and a 5% buffer fee for incidentals. This is your total 'all-in' cost."
    net_profit_tooltip = "Net Profit = (Amazon Price) - (FBA Fees) - (Total Cost)."
    roi_tooltip = "Return on Investment = (Net Profit / Total Cost) * 100."
    
    # JavaScript for copy-to-clipboard functionality
    copy_js = lambda text, idx: f"""
        navigator.clipboard.writeText('{text}').then(() => {{
            const el = document.getElementById('copy-icon-{idx}');
            el.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            setTimeout(() => {{
                el.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>';
            }}, 1500);
        }});
    """

    return f"""
    <div class="product-row" style="display: grid; grid-template-columns: 80px 2fr 1fr 1fr 1fr; align-items: start; gap: 1.5rem;">
        <!-- Image -->
        <div class="product-image-container">
            <img src="{row['Image']}" class="product-image-thumb" alt="{row['Title']}">
            <img src="{row['Image']}" class="product-image-zoom" alt="Zoomed {row['Title']}">
        </div>
        <!-- Product Details -->
        <div>
            <p style="font-weight: 700; color: #1e293b; line-height: 1.3; margin-bottom: 0.5rem;">{row['Title']}</p>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <div style="display: inline-flex; items-align: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 0.25rem; font-size: 10px; overflow: hidden;">
                    <span style="font-weight: 700; color: #475569; background-color: #f8fafc; padding: 2px 8px; border-right: 1px solid #e2e8f0;">ASIN</span>
                    <span style="font-family: monospace; color: #334155; padding: 2px 8px;">{row['ASIN']}</span>
                    <button class="copy-btn" title="Copy ASIN" onclick="{copy_js(row['ASIN'], f'{row.name}-asin')}"><span id="copy-icon-{row.name}-asin"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg></span></button>
                </div>
                <div style="display: inline-flex; items-align: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 0.25rem; font-size: 10px; overflow: hidden;">
                    <span style="font-weight: 700; color: #475569; background-color: #f8fafc; padding: 2px 8px; border-right: 1px solid #e2e8f0;">UPC</span>
                    <span style="font-family: monospace; color: #334155; padding: 2px 8px;">{row['Product Codes: UPC'] or 'N/A'}</span>
                    <button class="copy-btn" title="Copy UPC" onclick="{copy_js(row['Product Codes: UPC'], f'{row.name}-upc')}"><span id="copy-icon-{row.name}-upc"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg></span></button>
                </div>
            </div>
        </div>
        <!-- Amazon Metrics -->
        <div>
            <a href="https://www.amazon.com/dp/{row['ASIN']}" target="_blank" style="font-size: 1.125rem; font-weight: 900; color: #0f172a; text-decoration: none;">${row['Buy Box Price']:.2f}</a>
            <div style="font-size: 0.75rem; font-weight: 600; color: #ef4444; background-color: #fee2e2; display: inline-block; padding: 2px 6
