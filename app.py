# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import warnings
from tender_reconciliation_final_v8_updated import TenderReconciliationProcessor

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Tender Reconciliation Dashboard",
                   page_icon="📊",
                   layout="wide",
                   initial_sidebar_state="expanded")

# --- CSS / Theme (improved contrast for dark mode) ---
st.markdown("""
<style>
:root{
  --bg: #FFF8F2;
  --card: #FFFFFF;
  --text: #2e2b27;
  --muted: #6e6b68;
  --accent: #b35a1e;
  --accent-2: #2b5d4a;
}
@media (prefers-color-scheme: dark) {
  :root{
    --bg: #0f1416;
    --card: rgba(18,20,22,0.7);
    --text: #efeae6;
    --muted: #bfb8b2;
    --accent: #ff9a56;
    --accent-2: #49a07a;
  }
}
html, body, .reportview-container, .main {
  background: linear-gradient(180deg, var(--bg) 0%, #FFFDF9 100%) !important;
  color: var(--text) !important;
}
.panel { background: var(--card); border-radius:12px; padding:16px; box-shadow: 0 6px 24px rgba(0,0,0,0.06); color:var(--text); }
.brand { width:64px; height:64px; border-radius:12px; background: linear-gradient(135deg,var(--accent-2),var(--accent)); color:white; display:flex; align-items:center; justify-content:center; font-weight:700; }
.upload-slot { border-radius:10px; padding:12px; border:1px dashed rgba(0,0,0,0.06); text-align:center; color:var(--muted); background: rgba(255,255,255,0.02); min-height:110px;}
.small-note { font-size:12px; color:var(--muted); }
.action-btn { background: linear-gradient(90deg, var(--accent), var(--accent-2)); color:white; padding:10px 16px; border-radius:10px; font-weight:700; }
.panel * { color: var(--text) !important; }
.css-1kq8b8b, .css-1d391kg, .stText, label { color: var(--text) !important; }
.footer { text-align:center; color:var(--muted); margin-top:18px; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([0.12, 0.88])
with col1:
    st.markdown('<div class="brand">TR</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div style="padding-left:6px"><h1 style="margin:0">Tender Reconciliation Dashboard</h1><div class="small-note">Warm professional UI — visual tender performance below</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Sidebar settings
with st.sidebar:
    st.markdown('<div class="panel"><h4 style="margin:0 0 8px 0">⚙️ Configuration</h4>', unsafe_allow_html=True)
    netting_threshold = st.slider("Netting Threshold (±)", 1.0, 100.0, 5.0, 0.5)
    approval_option = st.radio("Processing Mode", ["All Responses", "Auto-Approved Only"])
    approval_filter = 'auto_approved_only' if approval_option == "Auto-Approved Only" else 'all'
    st.markdown('<div class="small-note">Adjust netting sensitivity to tune noise removal.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Upload area
st.markdown('<div class="panel"><h3 style="margin:0 0 12px 0">📁 Upload Tender CSVs</h3>', unsafe_allow_html=True)
col_a, col_b = st.columns([2.6, 1])
uploaded_files = {}

with col_a:
    for label in ['Cash', 'Card', 'UPI', 'Wallet']:
        key = label.lower()
        st.markdown(f'<div class="upload-slot"><strong>{label}</strong><div class="small-note">Headers at row 6 · CSV</div></div>', unsafe_allow_html=True)
        file = st.file_uploader(f"Upload {label} CSV", type=['csv'], key=key, label_visibility="hidden")
        if file:
            uploaded_files[label] = file

with col_b:
    st.markdown('<div class="panel"><h4 style="margin:0 0 8px 0">Requirements</h4>', unsafe_allow_html=True)
    st.markdown("""
        <div class="small-note">
        • CSV with headers on row 6<br>
        • Columns: Store ID, Store Response Entry, Auto Approved Date (optional)<br>
        • Non-zero responses only
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Process button
proc_col, help_col = st.columns([3,1])
with proc_col:
    do_process = st.button("🚀 Process Reconciliation", key="process")
with help_col:
    st.markdown('<div style="padding-top:6px"><button class="action-btn" onclick="window.scrollTo(0,document.body.scrollHeight)">📥 Help</button></div>', unsafe_allow_html=True)

if do_process:
    if len(uploaded_files) == 0:
        st.error("Please upload at least one CSV file.")
    else:
        with st.spinner("Processing files..."):
            try:
                temp_files = {}
                for tender_name, uploaded_file in uploaded_files.items():
                    tmp_path = f"/tmp/{tender_name}_{uploaded_file.name}"
                    with open(tmp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_files[tender_name] = tmp_path

                processor = TenderReconciliationProcessor(netting_threshold=netting_threshold,
                                                         approval_filter=approval_filter)
                results = processor.process_all_tenders(temp_files)

                if results is None:
                    st.error("Processing returned no results. Check input files.")
                else:
                    st.session_state['results'] = results
                    st.success("Processing complete!")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error during processing: {e}")

# Show results and tender performance visuals
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']

    st.markdown('<div class="panel"><h3 style="margin:0 0 12px 0">📊 Processing Results</h3>', unsafe_allow_html=True)

    # Metrics
    tcol1, tcol2, tcol3, tcol4 = st.columns(4)
    tcol1.metric("Total Stores", f"{results.get('total_stores',0):,}")
    tcol2.metric("Stores with Exceptions", f"{results.get('exception_stores',0):,}")
    exc_rate = (results.get('exception_stores',0)/results.get('total_stores',1)*100) if results.get('total_stores',0)>0 else 0
    tcol3.metric("Exception Rate", f"{exc_rate:.2f}%")
    real_exc = len(results['summary']) if not results['summary'].empty else 0
    tcol4.metric("Real Exceptions", f"{real_exc:,}")

    st.markdown("---")

    tabs = st.tabs(["Summary","Tender Performance (Visual)","Classification","Netting Reference","Download"])

    # Summary tab
    with tabs[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Store Summary (Real Exceptions)")
        if not results['summary'].empty:
            st.dataframe(results['summary'], use_container_width=True, height=420)
        else:
            st.info("No exceptions found after noise removal.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Tender Performance - visualized here (instead of writing sheet)
    with tabs[1]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tender Performance")
        tp = results.get('tender_performance', pd.DataFrame())
        if not tp.empty:
            # Clean and prepare for charts
            tp_chart = tp.copy()
            tp_chart['Exception_Rate_%'] = pd.to_numeric(tp_chart['Exception_Rate_%'], errors='coerce').fillna(0)
            tp_chart = tp_chart.sort_values('Tender')

            st.markdown("#### Exception Rate (%) by Tender")
            chart_data = tp_chart.set_index('Tender')['Exception_Rate_%']
            st.bar_chart(chart_data)

            st.markdown("#### Total vs Exceptional Entries")
            bar_df = tp_chart.set_index('Tender')[['Total_Entries', 'Exceptional_Entries']]
            st.bar_chart(bar_df)

            st.markdown("#### Items Removed by Netting")
            removed = tp_chart.set_index('Tender')['Items_Removed_by_Netting']
            st.bar_chart(removed)

            st.markdown("<div class='small-note'>Note: Tender performance visuals are shown here; the Excel report no longer includes a separate 'Tender_Performance' sheet.</div>", unsafe_allow_html=True)
        else:
            st.info("No tender performance data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Classification
    with tabs[2]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Exception Classification")
        if not results['classification'].empty:
            st.dataframe(results['classification'], use_container_width=True)
            st.markdown("#### Distribution by Classification")
            try:
                dist = results['classification'].set_index('Classification')['Store_Count']
                st.bar_chart(dist)
            except Exception:
                pass
        else:
            st.info("No classification data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Netting Reference
    with tabs[3]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Netting Items Removed (Noise)")
        if not results['netting_reference'].empty:
            st.dataframe(results['netting_reference'], use_container_width=True, height=300)
        else:
            st.info("No netting detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Download (Excel) - note User_Manual and Tender_Performance are omitted
    with tabs[4]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Download Report (Excel)")
        try:
            processor = TenderReconciliationProcessor(netting_threshold=netting_threshold, approval_filter=approval_filter)
            temp_excel_path = f"/tmp/Tender_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            ok = processor.save_to_excel(results, temp_excel_path)
            if ok:
                with open(temp_excel_path, "rb") as f:
                    data = f.read()
                st.download_button("📥 Download Excel Report", data=data, file_name=f"Tender_Reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("Failed to generate Excel report.")
        except Exception as e:
            st.error(f"Error generating Excel: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="footer">Tender Reconciliation Dashboard • Warm UX • Visual Tender Performance</div>', unsafe_allow_html=True)
