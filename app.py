import streamlit as st
import pandas as pd
import requests
import time

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Arbitrage Profit Master V8",
    page_icon="💰",
    layout="wide"
)

# --- CUSTOM CSS FOR "V8" LOOK ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stTextInput > label { font-weight: bold; }
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #0f172a; }
    .metric-label { font-size: 14px; color: #64748b; }
    .profit-positive { color: #10b981; font-weight: bold; }
    .profit-negative { color: #ef4444; font-weight: bold; }
    .img-thumbnail { border-radius: 8px; border: 1px solid #ddd; padding: 4px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    api_key = st.text_input(
        "Enter ScrapingDog API Key", 
        type="password",
        help="Get your free key at scrapingdog.com to enable live research."
    )
    
    st.divider()
    
    # 2. Filtering
    show_profitable_only = st.toggle("Show Profitable Only", value=False)
    
    st.divider()
    st.info("💡 **Note:** This app uses ScrapingDog (or SerpApi) to perform live Google Shopping searches for COGS data.")

# --- MAIN HEADER ---
st.title("Arbitrage Profit Master <span style='color:#4f46e5'>V8</span>")
st.markdown("Live Data Mode • **Upload CSV to Start**", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def search_cogs(query, api_key):
    """
    Searches Google Shopping via ScrapingDog API to find the lowest store price.
    """
    if not api_key:
        return None, []

    # ScrapingDog Google Shopping Endpoint
    url = "https://api.scrapingdog.com/google_shopping"
    params = {
        "api_key": api_key,
        "query": query,
        "country": "us"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            shopping_results = data.get('shopping_results', [])
            
            # Filter reputable stores if needed, or just take the lowest valid price
            # For simplicity, we take the top result that isn't eBay/Mercari
            valid_competitors = []
            
            excluded_stores = ['ebay', 'mercari', 'poshmark', 'amazon']
            
            for item in shopping_results:
                price_str = item.get('price', '$0').replace('$', '').replace(',', '')
                try:
                    price = float(price_str)
                except:
                    continue
                
                store_name = item.get('merchant', {}).get('name', 'Unknown Store')
                link = item.get('link', '#')
                
                # Basic exclusion check
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
                return lowest_price, valid_competitors[:2] # Return lowest + top 2 matches
            else:
                return 0.0, []
        else:
            return 0.0, []
    except Exception as e:
        return 0.0, []

# --- MAIN LOGIC ---

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    # Load Data
    try:
        df = pd.read_csv(uploaded_file)
        
        # Basic Column cleaning (handle "Keepa" weird column names)
        # We assume standard columns exist based on your V8 prototype
        # If columns are missing, we fill them safely.
        
        # 1. Clean Prices
        if 'Buy Box 🚚: Current' in df.columns:
            df['Buy Box Price'] = pd.to_numeric(df['Buy Box 🚚: Current'], errors='coerce').fillna(0)
        else:
            df['Buy Box Price'] = 0.0
            
        if 'FBA Pick&Pack Fee' in df.columns:
            df['FBA Fee'] = pd.to_numeric(df['FBA Pick&Pack Fee'], errors='coerce').fillna(0)
        else:
            df['FBA Fee'] = 0.0
            
        # 2. Image Handling
        if 'Image' in df.columns:
            # Take first image if multiple are separated by ;
            df['Image_URL'] = df['Image'].apply(lambda x: str(x).split(';')[0] if pd.notnull(x) else "")
        else:
            df['Image_URL'] = ""

        # 3. Identifiers
        df['ASIN'] = df['ASIN'].fillna('N/A')
        df['UPC'] = df['Product Codes: UPC'].astype(str).replace('nan', 'N/A')
        df['Title'] = df['Title'].fillna('Unknown Product')
        
        # --- RESEARCH PHASE ---
        if api_key:
            if "cogs_data" not in st.session_state:
                st.session_state["cogs_data"] = {}
            
            # Process Button
            if st.button("🚀 Start Live Research"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results_list = []
                
                total_rows = len(df)
                for index, row in df.iterrows():
                    asin = row['ASIN']
                    
                    # Check cache first to save API credits
                    if asin in st.session_state["cogs_data"]:
                        cogs, competitors = st.session_state["cogs_data"][asin]
                    else:
                        # Perform Search
                        query = row['UPC'] if row['UPC'] != 'N/A' else row['Title']
                        status_text.text(f"Searching: {row['Title'][:30]}...")
                        cogs, competitors = search_cogs(query, api_key)
                        
                        # Save to cache
                        st.session_state["cogs_data"][asin] = (cogs, competitors)
                        # Sleep briefly to be nice to API
                        time.sleep(0.5) 
                    
                    # Store Result
                    results_list.append({
                        "ASIN": asin,
                        "COGS": cogs,
                        "Competitors": competitors
                    })
                    
                    progress_bar.progress((index + 1) / total_rows)
                
                status_text.success("Research Complete!")
                st.rerun()

        # --- CALCULATION & DISPLAY ---
        
        # Prepare final display data
        final_rows = []
        
        for index, row in df.iterrows():
            asin = row['ASIN']
            
            # Get Research Data (if available)
            cogs = 0.0
            competitors = []
            
            if "cogs_data" in st.session_state and asin in st.session_state["cogs_data"]:
                cogs, competitors = st.session_state["cogs_data"][asin]
            
            # 5% Buffer Calculation
            buffer_fee = cogs * 0.05
            
            # Profit Calc
            selling_price = row['Buy Box Price']
            fba_fee = row['FBA Fee']
            # We assume Referral Fee is ~15% if not in CSV, or 0. 
            # Ideally add referral fee column if it exists.
            ref_fee = 0 # Placeholder if column missing
            
            net_profit = selling_price - fba_fee - ref_fee - cogs - buffer_fee
            
            # ROI Calc
            roi = 0
            if cogs > 0:
                roi = (net_profit / cogs) * 100
                
            # Filter Logic
            if show_profitable_only and net_profit <= 0:
                continue
                
            final_rows.append({
                "image": row['Image_URL'],
                "title": row['Title'],
                "asin": asin,
                "upc": row['UPC'],
                "price": selling_price,
                "fees": fba_fee,
                "cogs": cogs,
                "competitors": competitors,
                "profit": net_profit,
                "roi": roi
            })
            
        # --- RENDER TABLE (Custom HTML for V8 Look) ---
        
        st.write(f"**Results:** {len(final_rows)} products found.")
        
        for p in final_rows:
            # Color logic
            profit_class = "profit-positive" if p['profit'] > 0 else "profit-negative"
            profit_sign = "+" if p['profit'] > 0 else ""
            
            # Competitor HTML string
            comp_html = ""
            if p['competitors']:
                for c in p['competitors']:
                    comp_html += f"""
                    <div style="font-size:12px; margin-bottom:4px; display:flex; justify-content:space-between;">
                        <span style="color:#64748b;">{c['store']}</span>
                        <a href="{c['link']}" target="_blank" style="color:#2563eb; font-weight:bold; text-decoration:none;">${c['price']:.2f} ↗</a>
                    </div>
                    """
            else:
                comp_html = "<span style='color:#94a3b8; font-style:italic; font-size:12px;'>No data found</span>"

            # 5% fee note
            cogs_note = f"<div style='font-size:10px; color:#94a3b8; margin-top:4px;'>Cost w/ 5% fee: <b>${p['cogs']*1.05:.2f}</b></div>" if p['cogs'] > 0 else ""

            # Card HTML
            card_html = f"""
            <div style="background:white; border:1px solid #e2e8f0; border-radius:12px; padding:16px; margin-bottom:16px; display:flex; gap:16px; align-items:start; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                <div style="width:80px; flex-shrink:0;">
                    <img src="{p['image']}" style="width:100%; object-fit:contain; border-radius:6px; border:1px solid #f1f5f9; padding:4px;">
                </div>
                
                <div style="flex-grow:1; width: 30%;">
                    <div style="font-weight:700; color:#1e293b; margin-bottom:4px; line-height:1.4;">{p['title']}</div>
                    <div style="display:flex; gap:8px; flex-wrap:wrap;">
                        <span style="background:#f1f5f9; color:#64748b; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; border:1px solid #e2e8f0;">ASIN: {p['asin']}</span>
                        <span style="background:#f1f5f9; color:#64748b; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; border:1px solid #e2e8f0;">UPC: {p['upc']}</span>
                    </div>
                </div>
                
                <div style="width:15%; border-left:1px solid #f1f5f9; padding-left:16px;">
                    <div style="font-size:12px; color:#64748b; margin-bottom:2px;">Amazon Price</div>
                    <div style="font-size:18px; font-weight:800; color:#0f172a;">${p['price']:.2f}</div>
                    <div style="font-size:11px; color:#ef4444; background:#fef2f2; display:inline-block; padding:2px 6px; border-radius:4px; margin-top:4px; border:1px solid #fee2e2;">-${p['fees']:.2f} Fees</div>
                </div>
                
                <div style="width:20%; border-left:1px solid #f1f5f9; padding-left:16px;">
                    <div style="font-size:12px; color:#64748b; margin-bottom:6px;">Lowest Found (COGS)</div>
                    {comp_html}
                    {cogs_note}
                </div>
                
                <div style="width:15%; border-left:1px solid #f1f5f9; padding-left:16px;">
                     <div style="font-size:12px; color:#64748b; margin-bottom:2px;">Net Profit</div>
                     <div class="{profit_class}" style="font-size:18px;">{profit_sign}${p['profit']:.2f}</div>
                     <div style="font-size:12px; font-weight:bold; color:#64748b; margin-top:4px;">ROI: {p['roi']:.1f}%</div>
                </div>
            </div>
            """
            
            st.markdown(card_html, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error processing CSV: {e}")
else:
    st.info("👋 Upload your CSV file to begin analysis.")
