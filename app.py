import streamlit as st
import pandas as pd
import requests
import time

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Arbitrage Profit Master V10",
    page_icon="💰",
    layout="wide"
)

# --- CUSTOM CSS (Fixed Layout using Flexbox) ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    
    /* CARD CONTAINER */
    .product-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        display: flex;
        flex-wrap: wrap; /* Allows stacking on small screens */
        gap: 15px;
        align-items: flex-start;
    }
    
    /* COLUMNS */
    .col-img { flex: 0 0 80px; }
    .col-details { flex: 2 1 250px; } /* Grows, min width 250px */
    .col-amazon { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-cogs { flex: 1 1 150px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-profit { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }

    /* IMAGE ZOOM */
    .img-container { width: 80px; height: 80px; position: relative; }
    .product-img {
        width: 100%; height: 100%; object-fit: contain;
        border-radius: 6px; border: 1px solid #f1f5f9;
        transition: transform 0.2s ease; background: white; cursor: zoom-in;
    }
    .img-container:hover .product-img {
        transform: scale(3.5); position: absolute; top: 0; left: 0; z-index: 999;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); border: 1px solid #cbd5e1;
    }

    /* TEXT STYLES */
    .title-text { font-weight: 700; color: #1e293b; font-size: 14px; line-height: 1.3; margin-bottom: 6px; }
    .badge { background: #f8fafc; color: #64748b; padding: 2px 5px; border-radius: 4px; font-size: 10px; border: 1px solid #e2e8f0; margin-right: 4px; }
    .price-main { font-size: 16px; font-weight: 800; color: #0f172a; }
    .fee-badge { font-size: 10px; color: #ef4444; background: #fef2f2; padding: 1px 5px; border-radius: 3px; border: 1px solid #fee2e2; }
    .profit-pos { color: #10b981; font-weight: 800; font-size: 16px; }
    .profit-neg { color: #ef4444; font-weight: 800; font-size: 16px; }
    
    a { text-decoration: none; color: #2563eb; }
    a:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter SerpApi API Key", type="password")
    
    if api_key:
        if st.button("🔑 Verify Key"):
            try:
                # Quick test
                resp = requests.get("https://serpapi.com/search.json", params={"engine": "google_shopping", "q": "test", "api_key": api_key, "num": 1})
                if resp.status_code == 200:
                    st.success("Valid Key! ✅")
                else:
                    st.error(f"Invalid Key ({resp.status_code})")
            except:
                st.error("Connection Failed")

    st.divider()
    show_profitable_only = st.toggle("Show Profitable Only", value=False)
    st.divider()
    st.caption("Data Source: Google Shopping via SerpApi")

# --- HELPER FUNCTIONS ---
def search_cogs(query, api_key):
    if not api_key: return 0.0, []
    try:
        url = "https://serpapi.com/search.json"
        params = {"engine": "google_shopping", "q": query, "api_key": api_key, "google_domain": "google.com", "gl": "us", "hl": "en", "num": 5}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('shopping_results', [])
            valid = []
            excluded = ['ebay', 'mercari', 'poshmark', 'amazon', 'etsy']
            
            for item in results:
                price = item.get('extracted_price', 0.0)
                if price == 0.0: continue
                store = item.get('source', 'Unknown')
                link = item.get('link', '#')
                
                if not any(x in store.lower() for x in excluded):
                    valid.append({'store': store, 'price': price, 'link': link})
            
            valid.sort(key=lambda x: x['price'])
            return (valid[0]['price'], valid[:2]) if valid else (0.0, [])
        return 0.0, []
    except:
        return 0.0, []

# --- MAIN APP ---
st.title("Arbitrage Profit Master V10")
st.markdown("**Live Research Dashboard**")

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- CLEANING ---
        cols = df.columns
        # Flexible column finding
        price_col = next((c for c in cols if 'Buy Box' in c), None)
        fee_col = next((c for c in cols if 'Pick&Pack' in c or 'Fee' in c), None)
        upc_col = next((c for c in cols if 'UPC' in c or 'Codes' in c), None)

        # Default to 0 if columns missing
        df['Buy Box Price'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0) if price_col else 0.0
        df['FBA Fee'] = pd.to_numeric(df[fee_col], errors='coerce').fillna(0) if fee_col else 0.0
        
        if 'Image' in df.columns:
            df['Image_URL'] = df['Image'].apply(lambda x: str(x).split(';')[0] if pd.notnull(x) else "")
        else:
            df['Image_URL'] = ""
            
        df['ASIN'] = df['ASIN'].fillna('N/A')
        df['UPC'] = df[upc_col].astype(str).replace('nan', 'N/A') if upc_col else 'N/A'
        df['Title'] = df['Title'].fillna('Unknown Product')

        # --- RESEARCH LOGIC ---
        if api_key:
            if "results_v10" not in st.session_state:
                st.session_state["results_v10"] = []

            if st.button("🚀 Start Live Research"):
                st.session_state["results_v10"] = [] 
                progress = st.progress(0)
                status = st.empty()
                total = len(df)
                data_list = []

                for i, row in df.iterrows():
                    status.text(f"Scanning {i+1}/{total}: {row['Title'][:40]}...")
                    
                    # 1. API Call
                    query = row['UPC'] if row['UPC'] != 'N/A' else row['Title']
                    cogs, competitors = search_cogs(query, api_key)
                    
                    # 2. CALCULATION
                    sell_price = row['Buy Box Price']
                    fba_fee = row['FBA Fee']
                    
                    # Estimate Referral Fee (15% of selling price) if not in CSV
                    # (Standard Amazon practice)
                    ref_fee = sell_price * 0.15
                    
                    # 5% Buffer on COGS
                    buffer = cogs * 0.05
                    
                    # Total Cost
                    total_expenses = cogs + buffer + fba_fee + ref_fee
                    
                    # Net Profit
                    profit = sell_price - total_expenses
                    
                    # ROI
                    roi = (profit / cogs * 100) if cogs > 0 else 0.0

                    data_list.append({
                        "Image": row['Image_URL'],
                        "Title": row['Title'],
                        "ASIN": row['ASIN'],
                        "UPC": row['UPC'],
                        "Buy_Box_Raw": sell_price,
                        "Fees_Raw": f
