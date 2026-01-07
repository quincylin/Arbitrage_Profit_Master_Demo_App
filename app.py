import streamlit as st
import pandas as pd
import requests
import time

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Arbitrage Profit Master V9",
    page_icon="💰",
    layout="wide"
)

# --- CUSTOM CSS (Fixed Layout + Hover Zoom) ---
st.markdown("""
<style>
    /* Main container padding */
    .block-container { padding-top: 2rem; }
    
    /* CARD GRID LAYOUT - Clean & Aligned */
    .product-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        display: grid;
        grid-template-columns: 80px 3fr 1.5fr 2fr 1.5fr; /* Fixed columns */
        gap: 20px;
        align-items: start;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: box-shadow 0.2s;
    }
    .product-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* HOVER TO ZOOM IMAGE */
    .img-container {
        width: 80px;
        height: 80px;
        position: relative;
        overflow: visible; /* Allow image to pop out */
    }
    .product-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        border-radius: 6px;
        border: 1px solid #f1f5f9;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        background: white;
        cursor: zoom-in;
    }
    .img-container:hover .product-img {
        transform: scale(3); /* 3x Zoom */
        position: absolute;
        top: 0;
        left: 0;
        z-index: 100;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        border: 1px solid #cbd5e1;
    }

    /* TYPOGRAPHY */
    .title-text { font-weight: 700; color: #1e293b; font-size: 15px; line-height: 1.4; margin-bottom: 6px; }
    .badge { 
        background: #f1f5f9; color: #64748b; padding: 2px 6px; 
        border-radius: 4px; font-size: 11px; font-weight: 600; 
        border: 1px solid #e2e8f0; display: inline-block; margin-right: 4px;
    }
    .price-main { font-size: 18px; font-weight: 800; color: #0f172a; }
    .fee-badge { 
        font-size: 11px; color: #ef4444; background: #fef2f2; 
        padding: 2px 6px; border-radius: 4px; border: 1px solid #fee2e2; 
    }
    
    /* PROFIT COLORS */
    .profit-positive { color: #10b981; font-weight: 800; font-size: 18px; }
    .profit-negative { color: #ef4444; font-weight: 800; font-size: 18px; }
    
    /* LINKS */
    a { text-decoration: none; }
    a:hover { text-decoration: underline; }

</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    api_key = st.text_input(
        "Enter SerpApi API Key", 
        type="password",
        help="Get your key at serpapi.com. Required for live research."
    )
    
    # 2. Key Verification
    if api_key:
        if st.button("🔑 Verify Key"):
            try:
                # Test call with a cheap query
                test_url = "https://serpapi.com/search.json"
                test_params = {"engine": "google_shopping", "q": "test", "api_key": api_key, "num": 1}
                resp = requests.get(test_url, params=test_params)
                if resp.status_code == 200:
                    st.success("Key is Valid! ✅")
                elif resp.status_code == 401:
                    st.error("Invalid API Key ❌")
                else:
                    st.warning(f"Connection Issue: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    
    # 3. Filtering
    show_profitable_only = st.toggle("Show Profitable Only", value=False)
    
    st.divider()
    st.info("💡 **Note:** Uses SerpApi to scrape Google Shopping. 5% Buffer added to COGS.")

# --- HELPER FUNCTIONS ---

def search_cogs(query, api_key):
    """
    Searches Google Shopping via SerpApi to find the lowest store price.
    """
    if not api_key:
        return 0.0, []

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "num": 5 # Fetch top 5 results
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            shopping_results = data.get('shopping_results', [])
            
            valid_competitors = []
            excluded_stores = ['ebay', 'mercari', 'poshmark', 'amazon', 'etsy']
            
            for item in shopping_results:
                price = item.get('extracted_price', 0.0)
                if price == 0.0: continue
                
                store_name = item.get('source', 'Unknown Store')
                link = item.get('link', '#')
                
                # Exclusion Logic
                if not any(ex in store_name.lower() for ex in excluded_stores):
                    valid_competitors.append({
                        'store': store_name,
                        'price': price,
                        'link': link
                    })
            
            # Sort by price ascending
            valid_competitors.sort(key=lambda x: x['price'])
            
            if valid_competitors:
                lowest_price = valid_competitors[0]['price']
                return lowest_price, valid_competitors[:2] # Return lowest + top 2
            else:
                return 0.0, []
        else:
            return 0.0, []
    except:
        return 0.0, []

# --- MAIN APP ---
st.title("Arbitrage Profit Master <span style='color:#4f46e5'>V9</span>")
st.markdown("Live Research • Verification • Export Ready", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- DATA CLEANING ---
        # Normalize columns safely
        cols = df.columns
        price_col = next((c for c in cols if 'Buy Box' in c), 'Buy Box Price')
        fee_col = next((c for c in cols if 'Pick&Pack' in c or 'Fee' in c), 'FBA Fee')
        upc_col = next((c for c in cols if 'UPC' in c or 'Codes' in c), 'UPC')
        
        # Extract numeric values
        df['Buy Box Price'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
        df['FBA Fee'] = pd.to_numeric(df[fee_col], errors='coerce').fillna(0)
        
        # Image Handling
        if 'Image' in df.columns:
            df['Image_URL'] = df['Image'].apply(lambda x: str(x).split(';')[0] if pd.notnull(x) else "")
        else:
            df['Image_URL'] = ""

        # IDs
        df['ASIN'] = df['ASIN'].fillna('N/A')
        df['UPC'] = df[upc_col].astype(str).replace('nan', 'N/A')
        df['Title'] = df['Title'].fillna('Unknown Product')

        # --- RESEARCH UI ---
        if api_key:
            if "results_v9" not in st.session_state:
                st.session_state["results_v9"] = []

            if st.button("🚀 Start Live Research"):
                st.session_state["results_v9"] = [] # Reset
                progress = st.progress(0)
                status = st.empty()
                
                total = len(df)
                processed_data = []

                for i, row in df.iterrows():
                    status.text(f"Scanning {i+1}/{total}: {row['Title'][:40]}...")
                    
                    # 1. Search
                    query = row['UPC'] if row['UPC'] != 'N/A' else row['Title']
                    cogs, competitors = search_cogs(query, api_key)
                    
                    # 2. Calculate
                    buffer = cogs * 0.05
                    selling_price = row['Buy Box Price']
                    fees = row['FBA Fee']
                    # Estimate Ref fee if missing (15%)
                    ref_fee = selling_price * 0.15 
                    total_cost = cogs + buffer + fees + ref_fee
                    profit = selling_price - total_cost
                    
                    roi = (profit / cogs * 100) if cogs > 0 else 0
                    
                    # 3. Store
                    processed_data.append({
                        "Image": row['Image_URL'],
                        "Title": row['Title'],
                        "ASIN": row['ASIN'],
                        "UPC": row['UPC'],
                        "Buy Box": selling_price,
                        "FBA Fees": fees,
                        "COGS": cogs,
                        "Buffer (5%)": buffer,
                        "Net Profit": profit,
                        "ROI": roi,
                        "Competitors": competitors
                    })
                    
                    progress.progress((i + 1) / total)
                    time.sleep(0.2) # Rate limit safety
                
                st.session_state["results_v9"] = processed_data
                status.success("Analysis Complete!")
                st.rerun()

        # --- RESULTS DISPLAY ---
        if "results_v9" in st.session_state and st.session_state["results_v9"]:
            results = st.session_state["results_v9"]
            
            # Export CSV Logic
            export_df = pd.DataFrame(results)
            # Flatten competitors for CSV export
            export_df['Competitors'] = export_df['Competitors'].apply(lambda x: " | ".join([f"{c['store']}: ${c['price']}" for c in x]))
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.metric("Total Products", len(results))
            with col2:
                st.download_button(
                    label="📥 Download Analysis CSV",
                    data=export_df.to_csv(index=False),
                    file_name="arbitrage_analysis.csv",
                    mime="text/csv"
                )

            # --- CARD RENDER LOOP ---
            for p in results:
                # Filter Toggle
                if show_profitable_only and p['Net Profit'] <= 0:
                    continue

                # Styling classes
                profit_cls = "profit-positive" if p['Net Profit'] > 0 else "profit-negative"
                profit_sign = "+" if p['Net Profit'] > 0 else ""
                
                # Competitor HTML
                comp_html = ""
                if p['Competitors']:
                    for c in p['Competitors']:
                        comp_html += f"""
                        <div style="font-size:12px; display:flex; justify-content:space-between; margin-bottom:2px;">
                            <span style="color:#64748b;">{c['store']}</span>
                            <a href="{c['link']}" target="_blank" style="color:#2563eb; font-weight:bold;">${c['price']:.2f}</a>
                        </div>
                        """
                else:
                    comp_html = "<span style='color:#94a3b8; font-style:italic; font-size:12px;'>No Match Found</span>"

                # HTML Card
                st.markdown(f"""
                <div class="product-card">
                    <div class="img-container">
                        <img src="{p['Image']}" class="product-img">
                    </div>
                    
                    <div>
                        <div class="title-text">{p['Title']}</div>
                        <div>
                            <span class="badge">ASIN: {p['ASIN']}</span>
                            <span class="badge">UPC: {p['UPC']}</span>
                        </div>
                    </div>
                    
                    <div style="border-left:1px solid #f1f5f9; padding-left:12px;">
                        <div style="font-size:11px; color:#64748b;">Buy Box</div>
                        <div class="price-main">${p['Buy Box']:.2f}</div>
                        <div class="fee-badge">-${p['FBA Fees']:.2f} Fees</div>
                    </div>
                    
                    <div style="border-left:1px solid #f1f5f9; padding-left:12px;">
                        <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Lowest Found (COGS)</div>
                        {comp_html}
                        <div style="font-size:10px; color:#94a3b8; margin-top:4px;">
                            W/ 5% Buffer: <b>${p['COGS']*1.05:.2f}</b>
                        </div>
                    </div>
                    
                    <div style="border-left:1px solid #f1f5f9; padding-left:12px;">
                        <div style="font-size:11px; color:#64748b;">Net Profit</div>
                        <div class="{profit_cls}">{profit_sign}${p['Net Profit']:.2f}</div>
                        <div style="font-size:12px; font-weight:bold; color:#64748b;">ROI: {p['ROI']:.0f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        elif api_key:
            st.info("👆 Click 'Start Live Research' to scan the file.")
        else:
            st.warning("👈 Please enter your SerpApi Key in the sidebar.")

    except Exception as e:
        st.error(f"Error parsing file: {e}")
