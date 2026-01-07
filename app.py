import streamlit as st
import pandas as pd
import requests
import time

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Arbitrage Profit Master V16", page_icon="💰", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    
    /* Main Product Card Styling */
    .amz-card {
        background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 10px; margin-bottom: 10px; border-left: 4px solid #f59e0b; /* Orange for Amazon */
    }
    
    /* Result Card Styling */
    .match-card {
        background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
        padding: 10px; margin-bottom: 10px; border-left: 4px solid #22c55e; /* Green for Profit */
    }
    
    /* Typography */
    .big-price { font-size: 20px; font-weight: 800; color: #0f172a; }
    .small-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .profit-pos { color: #16a34a; font-weight: 800; font-size: 20px; }
    .profit-neg { color: #dc2626; font-weight: 800; font-size: 20px; }
    
    /* Buttons */
    .stButton button { width: 100%; border-radius: 4px; padding: 4px; font-size: 12px; }
    
    /* Images */
    .cand-img { border-radius: 4px; border: 1px solid #e2e8f0; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter SerpApi API Key", type="password")
    st.divider()
    show_profitable_only = st.toggle("Show Profitable Only", value=False)
    st.divider()
    if st.button("Reset / Clear All Data"):
        st.session_state["results_v16"] = []
        st.rerun()

# --- SEARCH FUNCTION (Returns Multiple Candidates) ---
def search_candidates(upc, title, api_key):
    if not api_key: return []
    
    # 1. Combined Search Query
    query = f"{upc} {title}" if upc and upc != 'N/A' else title
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key,
            "google_domain": "google.com",
            "gl": "us", "hl": "en", "num": 8 # Fetch top 8
        }
        
        response = requests.get(url, params=params)
        candidates = []
        excluded = ['ebay', 'mercari', 'poshmark', 'amazon', 'etsy']

        if response.status_code == 200:
            data = response.json()
            shopping_results = data.get('shopping_results', [])
            
            for item in shopping_results:
                price = item.get('extracted_price', 0.0)
                if price == 0.0: continue
                
                store = item.get('source', 'Unknown')
                if any(x in store.lower() for x in excluded): continue

                link = item.get('link')
                if link and link.startswith('/'): link = f"https://www.google.com{link}"
                
                # Get Image
                img = item.get('thumbnail', 'https://via.placeholder.com/150?text=No+Img')
                
                candidates.append({
                    'store': store,
                    'price': price,
                    'link': link,
                    'title': item.get('title', 'Unknown Title'),
                    'img': img
                })
        
        # Sort by price ascending initially
        candidates.sort(key=lambda x: x['price'])
        return candidates[:4] # Return Top 4 Candidates
        
    except: return []

# --- MAIN APP ---
st.title("Arbitrage Profit Master V16")
st.markdown("Select the correct image to calculate profit.")

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    # --- 1. LOAD DATA ---
    try:
        df = pd.read_csv(uploaded_file)
        
        # (Same column cleaning logic as before)
        cols = df.columns
        price_col = next((c for c in cols if 'Buy Box' in c), None)
        fee_col = next((c for c in cols if 'Pick&Pack' in c or 'Fee' in c), None)
        upc_col = next((c for c in cols if 'UPC' in c or 'Codes' in c), None)
        
        df['Buy Box Price'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0) if price_col else 0.0
        df['FBA Fee'] = pd.to_numeric(df[fee_col], errors='coerce').fillna(0) if fee_col else 0.0
        
        if 'Image' in df.columns:
            df['Image_URL'] = df['Image'].apply(lambda x: str(x).split(';')[0] if pd.notnull(x) else "")
        else: df['Image_URL'] = ""
            
        df['ASIN'] = df['ASIN'].fillna('N/A')
        df['UPC'] = df[upc_col].astype(str).replace('nan', 'N/A') if upc_col else 'N/A'
        df['Title'] = df['Title'].fillna('Unknown Product')

        # --- 2. INIT SESSION STATE ---
        if "results_v16" not in st.session_state:
            st.session_state["results_v16"] = []

        # --- 3. RUN RESEARCH (Once) ---
        if api_key and st.button("🚀 Start Live Research"):
            st.session_state["results_v16"] = []
            progress = st.progress(0)
            
            # Prepare data structure
            temp_results = []
            total = len(df)
            
            for i, row in df.iterrows():
                # Search
                candidates = search_candidates(row['UPC'], row['Title'], api_key)
                
                # Default to first candidate if available
                selected_idx = 0 if candidates else -1
                
                item_data = {
                    "id": i, # Unique ID for stream lit keys
                    "amz_img": row['Image_URL'],
                    "amz_title": row['Title'],
                    "amz_asin": row['ASIN'],
                    "amz_price": row['Buy Box Price'],
                    "amz_fees": row['FBA Fee'],
                    "candidates": candidates,
                    "selected_idx": selected_idx 
                }
                temp_results.append(item_data)
                progress.progress((i+1)/total)
                time.sleep(0.5)
            
            st.session_state["results_v16"] = temp_results
            st.rerun()

        # --- 4. DISPLAY & INTERACTION LOOP ---
        if st.session_state["results_v16"]:
            
            results = st.session_state["results_v16"]
            
            # Global Stats
            profitable_count = 0
            
            for item in results:
                # --- A. CALCULATION BASED ON SELECTION ---
                idx = item['selected_idx']
                
                if idx >= 0 and item['candidates']:
                    cand = item['candidates'][idx]
                    cogs = cand['price']
                    store = cand['store']
                    link = cand['link']
                    cand_img = cand['img']
                    
                    # Math
                    buffer = cogs * 0.05
                    ref_fee = item['amz_price'] * 0.15
                    total_cost = cogs + buffer + item['amz_fees'] + ref_fee
                    profit = item['amz_price'] - total_cost
                    roi = (profit / cogs * 100) if cogs > 0 else 0
                else:
                    # No candidate or no selection
                    cogs = 0; store = "None"; link="#"; cand_img=""; profit=0; roi=0
                
                if profit > 0: profitable_count += 1
                if show_profitable_only and profit <= 0: continue

                # --- B. UI LAYOUT ---
                st.markdown("---")
                
                # Top Container: 2 Columns (Amazon vs Match)
                c1, c2 = st.columns([1, 1])
                
                # LEFT: AMAZON (Static)
                with c1:
                    st.markdown(f"""
                    <div class="amz-card">
                        <div style="display:flex; gap:10px;">
                            <img src="{item['amz_img']}" style="height:80px; width:80px; object-fit:contain; background:white;">
                            <div>
                                <div class="small-label">Amazon Listing</div>
                                <div style="font-weight:bold; font-size:14px; line-height:1.2;">{item['amz_title']}</div>
                                <div style="margin-top:5px;">
                                    <span style="font-size:12px; color:#64748b;">ASIN: {item['amz_asin']}</span>
                                </div>
                                <div class="big-price" style="margin-top:5px;">${item['amz_price']:.2f}</div>
                                <div style="font-size:11px; color:#ef4444;">-${item['amz_fees']:.2f} FBA Fees</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # RIGHT: SELECTED MATCH (Dynamic)
                with c2:
                    if idx >= 0:
                        p_cls = "profit-pos" if profit > 0 else "profit-neg"
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="display:flex; gap:10px;">
                                <img src="{cand_img}" style="height:80px; width:80px; object-fit:contain; background:white;">
                                <div>
                                    <div class="small-label">Selected Match: {store}</div>
                                    <div class="big-price">${cogs:.2f} <a href="{link}" target="_blank" style="font-size:12px; text-decoration:none;">(View ↗)</a></div>
                                    <div style="font-size:11px; color:#64748b;">+${cogs*0.05:.2f} Buffer (5%)</div>
                                    <div style="margin-top:8px;">
                                        <div class="small-label">Net Profit</div>
                                        <div class="{p_cls}">${profit:.2f} <span style="font-size:14px; color:#333;">({roi:.0f}% ROI)</span></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ No match selected. Please select a candidate below.")

                # BOTTOM: CANDIDATE SELECTOR
                if item['candidates']:
                    st.caption("👇 **Select the correct product match from Google results:**")
                    
                    # Create 4 columns for candidates
                    cols = st.columns(4)
                    
                    for i, cand in enumerate(item['candidates']):
                        with cols[i]:
                            # Display Thumbnail
                            st.image(cand['img'], use_container_width=True)
                            
                            # Display Details
                            st.markdown(f"**${cand['price']:.2f}**")
                            st.caption(f"{cand['store'][:15]}...")
                            
                            # Selection Button
                            # If this button is clicked, we update the state and rerun
                            if st.button(f"Select #{i+1}", key=f"btn_{item['id']}_{i}"):
                                item['selected_idx'] = i
                                st.rerun() # Force UI update immediately
                else:
                    st.info("No candidates found via API.")

    except Exception as e:
        st.error(f"Error loading file: {e}")
