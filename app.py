import streamlit as st
import pandas as pd
import requests
import time

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Arbitrage Profit Master V11", page_icon="💰", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .product-card {
        background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-start;
    }
    .col-img { flex: 0 0 80px; }
    .col-details { flex: 2 1 250px; }
    .col-amazon { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-cogs { flex: 1 1 150px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    .col-profit { flex: 1 1 120px; border-left: 1px solid #f1f5f9; padding-left: 12px; }
    
    .img-container { width: 80px; height: 80px; position: relative; }
    .product-img {
        width: 100%; height: 100%; object-fit: contain; border-radius: 6px;
        border: 1px solid #f1f5f9; background: white; transition: transform 0.2s; cursor: zoom-in;
    }
    .img-container:hover .product-img {
        transform: scale(3.5); position: absolute; top: 0; left: 0; z-index: 999;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); border: 1px solid #cbd5e1;
    }

    .title-text { font-weight: 700; color: #1e293b; font-size: 14px; margin-bottom: 6px; }
    .badge { background: #f8fafc; color: #64748b; padding: 2px 5px; border-radius: 4px; font-size: 10px; border: 1px solid #e2e8f0; margin-right: 4px; }
    
    /* Price Links */
    .price-link { font-size: 16px; font-weight: 800; color: #0f172a; text-decoration: none; border-bottom: 1px dotted #cbd5e1; }
    .price-link:hover { color: #2563eb; border-bottom: 1px solid #2563eb; }
    
    .fee-badge { font-size: 10px; color: #ef4444; background: #fef2f2; padding: 1px 5px; border-radius: 3px; border: 1px solid #fee2e2; }
    .profit-pos { color: #10b981; font-weight: 800; font-size: 16px; }
    .profit-neg { color: #ef4444; font-weight: 800; font-size: 16px; }
    
    /* Competitor Links */
    .comp-link { font-weight:bold; font-size:11px; color:#2563eb; text-decoration:none; }
    .comp-link:hover { text-decoration:underline; }
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
                # Capture the deep link to the product
                link = item.get('link', '#')
                
                if not any(x in store.lower() for x in excluded):
                    valid.append({'store': store, 'price': price, 'link': link})
            
            valid.sort(key=lambda x: x['price'])
            return (valid[0]['price'], valid[:2]) if valid else (0.0, [])
        return 0.0, []
    except: return 0.0, []

# --- MAIN APP ---
st.title("Arbitrage Profit Master V11")
st.markdown("**Live Research Dashboard**")

uploaded_file = st.file_uploader("Upload Keepa Export CSV", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        cols = df.columns
        
        # Flexible column mapping
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
            if "results_v11" not in st.session_state:
                st.session_state["results_v11"] = []

            if st.button("🚀 Start Live Research"):
                st.session_state["results_v11"] = [] 
                progress = st.progress(0)
                status = st.empty()
                total = len(df)
                data_list = []

                for i, row in df.iterrows():
                    status.text(f"Scanning {i+1}/{total}: {row['Title'][:40]}...")
                    
                    query = row['UPC'] if row['UPC'] != 'N/A' else row['Title']
                    cogs, competitors = search_cogs(query, api_key)
                    
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
                        "Competitors": competitors
                    })
                    
                    progress.progress((i + 1) / total)
                    time.sleep(0.2)
                
                st.session_state["results_v11"] = data_list
                status.success("Done!")
                st.rerun()

        if "results_v11" in st.session_state and st.session_state["results_v11"]:
            results = st.session_state["results_v11"]
            
            # Export
            export_data = []
            for r in results:
                # Competitor Links included in CSV for reference
                comp_str = " | ".join([f"{c['store']}: ${c['price']:.2f} ({c['link']})" for c in r['Competitors']])
                export_data.append({
                    "Title": r['Title'], "ASIN": r['ASIN'], "UPC": r['UPC'],
                    "Buy Box": f"${r['Buy_Box_Raw']:.2f}", "COGS": f"${r['COGS_Raw']:.2f}",
                    "Buffer (5%)": f"${r['Buffer_Raw']:.2f}", "FBA Fees": f"${r['Fees_Raw']:.2f}",
                    "Ref Fees": f"${r['Ref_Fee_Raw']:.2f}", "Net Profit": f"${r['Profit_Raw']:.2f}",
                    "ROI": f"{r['ROI_Raw']:.2f}%", "Competitors": comp_str
                })
            
            col1, col2 = st.columns([1, 4])
            with col1: st.metric("Products", len(results))
            with col2: st.download_button("📥 Download CSV", pd.DataFrame(export_data).to_csv(index=False), "analysis.csv", "text/csv")

            for p in results:
                if show_profitable_only and p['Profit_Raw'] <= 0: continue
                p_cls = "profit-pos" if p['Profit_Raw'] > 0 else "profit-neg"
                p_sign = "+" if p['Profit_Raw'] > 0 else ""
                
                # Construct Amazon Link
                amz_url = f"https://www.amazon.com/dp/{p['ASIN']}"
                
                comp_html = ""
                if p['Competitors']:
                    for c in p['Competitors']:
                        # DEEP LINK: c['link'] comes directly from API's product page URL
                        comp_html += f"<div><span style='color:#64748b; font-size:11px;'>{c['store']}</span> <a href='{c['link']}' target='_blank' class='comp-link'>${c['price']:.2f} ↗</a></div>"
                else: comp_html = "<span style='color:#cbd5e1; font-size:11px;'>No Matches</span>"

                st.markdown(f"""
                <div class="product-card">
                    <div class="col-img"><div class="img-container"><img src="{p['Image']}" class="product-img"></div></div>
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
