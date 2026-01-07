import streamlit as st
import pandas as pd
import requests
import time
from difflib import SequenceMatcher

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Arbitrage Profit Master V15", page_icon="💰", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .product-card {
        background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-start;
    }
    
    /* IMAGES */
    .img-wrapper { display: flex; gap: 8px; flex: 0 0 170px; }
    .img-box { width: 80px; text-align: center; }
    .img-label { font-size: 9px; color: #64748b; margin-bottom: 2px; text-transform: uppercase; font-weight: bold; }
    .product-img {
        width: 80px; height: 80px; object-fit: contain; border-radius: 6px;
        border: 1px solid #f1f5f9; background: white; cursor: zoom-in;
    }
    .product-img:hover { transform: scale(3.5); position: relative; z-index: 999; border: 1px solid #94a3b8; }

    /* LAYOUT COLUMNS */
    .col-details { flex: 2 1 250px; }
    .col-amazon { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-cogs { flex: 1 1 150px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-profit { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    
    .title-text { font-weight: 700; color: #1e293b; font-size: 14px; margin-bottom: 6px; }
    .badge { background: #f8fafc; color: #64748b; padding: 2px 5px; border-radius: 4px; font-size: 10px; border: 1px solid #e2e8f0; margin-right: 4px; }
    
    .price-link { font-size: 16px; font-weight: 800; color: #0f172a; text-decoration: none; border-bottom: 1px dotted #cbd5e1; }
    .price-link:hover { color: #2563eb; border-bottom: 1px solid #2563eb; }
    
    .profit-pos { color: #10b981; font-weight: 800; font-size: 16px; }
    .profit-neg { color: #ef4444; font-weight: 800; font-size: 16px; }
    
    .comp-link { font-weight:bold; font-size:11px; color:#2563eb; text-decoration:none; }
    .compare-btn {
        display: block; margin-top: 8px; font-size: 11px; 
        color: #4f46e5; background: #eef2ff; padding: 4px 8px; 
        border-radius: 4px; text-align: center; font-weight: 600;
        border: 1px solid #c7d2fe; transition: all 0.2s; text-decoration: none;
    }
    .compare-btn:hover { background: #4f46e5; color: white; }
    
    /* Mismatch Warning */
    .mismatch-flag { color: #d97706; font-size: 10px; font-weight: bold; display: flex; align-items: center; gap: 4px; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter SerpApi API Key", type="password")
    
    if api_key:
        if st.button("🔑 Verify Key"):
            try:
                resp = requests.get("https://serpapi.com/search.json", params={"engine": "google_shopping", "q": "test", "api_key": api_key, "num": 1})
                if resp.status_code == 200: st.success("Valid Key! ✅")
                else: st.error(f"Invalid Key ({resp.status_code})")
            except: st.error("Connection Failed")

    st.divider()
    show_profitable_only = st.toggle("Show Profitable Only", value=False)

# --- HELPER FUNCTIONS ---

def similar(a, b):
    """Check text similarity (0.0 to 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_cogs(upc, title, api_key):
    if not api_key: return 0.0, [], "#", ""
    
    # --- STRATEGY V15: Combined Query ---
    # We combine UPC and Title to force Google to find pages containing BOTH.
    # This significantly reduces "random product" matches.
    if upc and upc != 'N/A':
        search_query = f"{upc} {title}"
    else:
        search_query = title
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": api_key,
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "num": 10 
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            valid = []
            excluded = ['ebay', 'mercari', 'poshmark', 'amazon', 'etsy']

            compare_link = data.get('search_metadata', {}).get('google_shopping_url', '#')
            shopping_results = data.get('shopping_results', [])
            
            for item in shopping_results:
                price = item.get('extracted_price', 0.0)
                if price == 0.0: continue
                
                store = item.get('source', 'Unknown')
                link = item.get('link') 
                
                # Capture the found image for visual verification
                found_img = item.get('thumbnail', '')

                if any(x in store.lower() for x in excluded): continue
                    
                if link and link.startswith('/'): link = f"https://www.google.com{link}"
                
                valid.append({
                    'store': store, 
                    'price': price, 
                    'link': link, 
                    'title': item.get('title', ''),
                    'img': found_img
                })
            
            valid.sort(key=lambda x: x['price'])
            
            if valid:
                top_match = valid[0]
                return (top_match['price'], valid[:2], compare_link, top_match['img'])
            
        return 0.0, [], "#", ""
    except Exception as e:
        return 0.0, [], "#", ""

# --- MAIN APP ---
st.title("Arbitrage Profit Master V15")
st.markdown("**Live Research • Combined Search • Visual Match**")

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
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

        if api_key:
            if "results_v15" not in st.session_state:
                st.session_state["results_v15"] = []

            if st.button("🚀 Start Live Research"):
                st.session_state["results_v15"] = [] 
                progress = st.progress(0)
                status = st.empty()
                total = len(df)
                data_list = []

                for i, row in df.iterrows():
                    status.text(f"Scanning {i+1}/{total}: {row['Title'][:40]}...")
                    
                    upc_val = row['UPC']
                    title_val = row['Title']
                    
                    # Call V15 Search
                    cogs, competitors, comp_link, found_img = search_cogs(upc_val, title_val, api_key)
                    
                    sell_price = row['Buy Box Price']
                    fba_fee = row['FBA Fee']
                    ref_fee = sell_price * 0.15 
                    buffer = cogs * 0.05
                    total_expenses = cogs + buffer + fba_fee + ref_fee
                    profit = sell_price - total_expenses
                    roi = (profit / cogs * 100) if cogs > 0 else 0.0

                    data_list.append({
                        "Image": row['Image_URL'],
                        "Title": row['Title'],
                        "ASIN": row['ASIN'],
                        "UPC": row['UPC'],
                        "Buy_Box_Raw": sell_price,
                        "Fees_Raw": fba_fee,
                        "Ref_Fee_Raw": ref_fee,
                        "COGS_Raw": cogs,
                        "Buffer_Raw": buffer,
                        "Profit_Raw": profit,
                        "ROI_Raw": roi,
                        "Competitors": competitors,
                        "Compare_Link": comp_link,
                        "Found_Image": found_img # New Image
                    })
                    
                    progress.progress((i + 1) / total)
                    time.sleep(0.5) 
                
                st.session_state["results_v15"] = data_list
                status.success("Done!")
                st.rerun()

        if "results_v15" in st.session_state and st.session_state["results_v15"]:
            results = st.session_state["results_v15"]
            
            export_data = []
            for r in results:
                comp_str = " | ".join([f"{c['store']}: ${c['price']:.2f}" for c in r['Competitors']])
                export_data.append({
                    "Title": r['Title'], "ASIN": r['ASIN'], "UPC": r['UPC'],
                    "Buy Box": f"${r['Buy_Box_Raw']:.2f}", "COGS": f"${r['COGS_Raw']:.2f}",
                    "Buffer (5%)": f"${r['Buffer_Raw']:.2f}", "FBA Fees": f"${r['Fees_Raw']:.2f}",
                    "Net Profit": f"${r['Profit_Raw']:.2f}", "ROI": f"{r['ROI_Raw']:.2f}%", 
                    "Compare Link": r['Compare_Link'], "Competitors": comp_str
                })
            
            col1, col2 = st.columns([1, 4])
            with col1: st.metric("Products", len(results))
            with col2: st.download_button("📥 Download CSV", pd.DataFrame(export_data).to_csv(index=False), "analysis.csv", "text/csv")

            for p in results:
                if show_profitable_only and p['Profit_Raw'] <= 0: continue
                p_cls = "profit-pos" if p['Profit_Raw'] > 0 else "profit-neg"
                p_sign = "+" if p['Profit_Raw'] > 0 else ""
                amz_url = f"https://www.amazon.com/dp/{p['ASIN']}"
                
                # --- VISUAL VERIFICATION LOGIC ---
                # Default "Placeholder" if no image found
                found_img_src = p['Found_Image'] if p['Found_Image'] else "https://via.placeholder.com/80?text=No+Img"
                
                comp_html = ""
                if p['Competitors']:
                    for c in p['Competitors']:
                        target_link = c['link'] if c['link'] else "#"
                        comp_html += f"<div><span style='color:#64748b; font-size:11px;'>{c['store']}</span> <a href='{target_link}' target='_blank' class='comp-link'>${c['price']:.2f} ↗</a></div>"
                else: comp_html = "<span style='color:#cbd5e1; font-size:11px;'>No Matches</span>"

                compare_btn_html = ""
                if p['Compare_Link'] and p['Compare_Link'] != "#":
                     compare_btn_html = f"""<a href="{p['Compare_Link']}" target="_blank" class="compare-btn">🔎 Compare All</a>"""

                st.markdown(f"""
                <div class="product-card">
                    <div class="img-wrapper">
                        <div class="img-box">
                            <div class="img-label">AMAZON</div>
                            <img src="{p['Image']}" class="product-img">
                        </div>
                        <div class="img-box">
                            <div class="img-label">FOUND</div>
                            <img src="{found_img_src}" class="product-img">
                        </div>
                    </div>
                    
                    <div class="col-details">
                        <div class="title-text"><a href="{amz_url}" target="_blank" style="color:#1e293b; text-decoration:none;">{p['Title']}</a></div>
                        <div><span class="badge">ASIN: {p['ASIN']}</span><span class="badge">UPC: {p['UPC']}</span></div>
                    </div>
                    <div class="col-amazon">
                        <div style="font-size:10px; color:#64748b;">Buy Box</div>
                        <a href="{amz_url}" target="_blank" class="price-link">${p['Buy_Box_Raw']:.2f}</a>
                        <div class="fee-badge">-${p['Fees_Raw']:.2f} FBA</div>
                    </div>
                    <div class="col-cogs">
                        <div style="font-size:10px; color:#64748b;">Lowest COGS</div>
                        {comp_html}
                        {compare_btn_html}
                        <div style="font-size:9px; color:#94a3b8; margin-top:3px;">+${p['Buffer_Raw']:.2f} (5% fee)</div>
                    </div>
                    <div class="col-profit">
                        <div style="font-size:10px; color:#64748b;">Net Profit</div>
                        <div class="{p_cls}">{p_sign}${p['Profit_Raw']:.2f}</div>
                        <div style="font-size:11px; font-weight:bold; color:#64748b;">ROI: {p['ROI_Raw']:.2f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        elif api_key: st.info("Ready. Click 'Start Live Research' to begin.")
        else: st.warning("Please enter your API Key in the sidebar.")

    except Exception as e: st.error(f"Error: {e}")
