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

# --- CSS / Animation (warm, professional) ---
st.markdown(
    """
    <style>
    :root{
      --bg:#FFF8F2;
      --card:#FFFFFF;
      --accent:#B35A1E; /* warm burnt orange */
      --muted:#6E6B68;
      --soft:#F2C57C;
      --accent-2:#2B5D4A; /* deep warm green */
      --glass: rgba(255,255,255,0.6);
    }
    html,body, .reportview-container, .main {
      background: linear-gradient(180deg, var(--bg) 0%, #FFFDF9 100%);
      color: #333;
    }
    .header {
      display:flex;
      align-items:center;
      gap:18px;
      animation: fadeInUp .7s ease both;
      padding-bottom: 8px;
    }
    .brand {
      width:72px;
      height:72px;
      border-radius:14px;
      background: linear-gradient(135deg, var(--accent-2), var(--accent));
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-weight:700;
      box-shadow: 0 6px 22px rgba(43,93,74,0.12);
    }
    .title { font-size:28px; font-weight:700; margin:0; color:#3c2f2a; }
    .subtitle { color:var(--muted); margin-top:4px; font-size:13px; }
    .panel {
      background: var(--card);
      border-radius:12px;
      padding:18px;
      box-shadow: 0 6px 20px rgba(62,62,60,0.06);
      animation: cardPop .6s ease both;
    }
    .file-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; }
    .upload-slot {
      border: 1px dashed rgba(60,60,60,0.08);
      height:120px;
      border-radius:10px;
      display:flex;
      flex-direction:column;
      align-items:center;
      justify-content:center;
      color:var(--muted);
      transition: all .18s ease;
      background: linear-gradient(180deg, rgba(242,197,124,0.03), rgba(255,255,255,0.02));
    }
    .upload-slot:hover { transform: translateY(-6px); box-shadow: 0 10px 30px rgba(163,90,34,0.06); }
    .action-btn {
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      color:white;
      border-radius:10px;
      padding:10px 18px;
      font-weight:600;
      border: none;
      cursor:pointer;
      box-shadow: 0 8px 24px rgba(163,90,34,0.12);
    }
    .action-btn:hover { transform: translateY(-3px); }
    .metric {
      padding:12px;
      border-radius:10px;
      background:linear-gradient(180deg, rgba(43,93,74,0.04), rgba(255,255,255,0.02));
      text-align:center;
      color:#2E2B27;
    }
    .small-note { font-size:12px; color:var(--muted); margin-top:6px; }
    .fadein { animation: fadeIn .8s ease both; }
    @keyframes fadeInUp {
      from { opacity:0; transform: translateY(12px); }
      to { opacity:1; transform: translateY(0); }
    }
    @keyframes cardPop {
      from { opacity:0; transform: scale(.995) translateY(8px); }
      to { opacity:1; transform: scale(1) translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity:0; } to { opacity:1; }
    }
    .typing {
      display:inline-block;
      border-right: 2px solid rgba(60,60,60,0.18);
      padding-right:8px;
      animation: blinkCaret .9s step-end infinite;
    }
    @keyframes blinkCaret {
      from, to { border-color: transparent; }
      50% { border-color: rgba(60,60,60,0.18); }
    }
    .hint { font-size:12px; color:var(--muted); }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
header_col1, header_col2 = st.columns([0.12, 0.88])
with header_col1:
    st.markdown('<div class="brand">TR</div>', unsafe_allow_html=True)
with header_col2:
    st.markdown(
        '<div class="header"><div><h1 class="title">Tender Reconciliation Dashboard</h1>'
        '<div class="subtitle">Warm, professional interface — fast, clear reconciliation</div></div></div>',
        unsafe_allow_html=True
    )

st.markdown("---")

# --- Sidebar (settings) ---
with st.sidebar:
    st.markdown("<div class='panel'><h4 style='margin:0 0 8px 0'>⚙️ Configuration</h4>", unsafe_allow_html=True)
    netting_threshold = st.slider("Netting Threshold (±)", 1.0, 100.0, 5.0, 0.5)
    approval_option = st.radio("Processing Mode", ["All Responses", "Auto-Approved Only"])
    approval_filter = 'auto_approved_only' if approval_option == "Auto-Approved Only" else 'all'
    st.markdown("<div class='small-note'>Adjust netting sensitivity to tune noise removal.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Upload area ---
st.markdown('<div class="panel fadein"><h3 style="margin:0 0 12px 0">📁 Upload Tender CSVs</h3>', unsafe_allow_html=True)

col_a, col_b = st.columns([2.6, 1])
with col_a:
    st.markdown('<div class="file-grid">', unsafe_allow_html=True)
    uploaded_files = {}
    for label in ['Cash', 'Card', 'UPI', 'Wallet']:
        key = label.lower()
        with st.container():
            st.markdown(f'<div class="upload-slot"><strong>{label}</strong><div class="small-note">Headers at row 6 · CSV</div></div>', unsafe_allow_html=True)
            file = st.file_uploader(f"Upload {label} CSV", type=['csv'], key=key, label_visibility="hidden")
            if file:
                uploaded_files[label] = file
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="panel"><h4 style="margin:0 0 8px 0">Requirements</h4>', unsafe_allow_html=True)
    st.markdown("""
        <div class="hint">
        • CSV format with headers on row 6<br>
        • Columns: Store ID, Store Response Entry, Auto Approved Date (optional)<br>
        • Non-zero responses only
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

# --- Process button ---
process_col1, process_col2 = st.columns([3,1])
with process_col1:
    if st.button("🚀 Process Reconciliation", key="process", help="Run reconciliation with current settings", args=None):
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

with process_col2:
    st.markdown('<div style="padding-top:6px"><button class="action-btn" onclick="window.scrollTo(0,document.body.scrollHeight)">📥 Help</button></div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- Results (styled) ---
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']

    st.markdown('<div class="panel fadein"><h3 style="margin:0 0 12px 0">📊 Processing Results</h3>', unsafe_allow_html=True)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{results.get("total_stores",0):,}</div><div class="small-note">Total Stores</div></div>', unsafe_allow_html=True)
    mcol2.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{results.get("exception_stores",0):,}</div><div class="small-note">Stores with Exceptions</div></div>', unsafe_allow_html=True)
    exc_rate = (results.get('exception_stores',0)/results.get('total_stores',1)*100) if results.get('total_stores',0)>0 else 0
    mcol3.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{exc_rate:.2f}%</div><div class="small-note">Exception Rate</div></div>', unsafe_allow_html=True)
    real_exceptions = len(results['summary']) if not results['summary'].empty else 0
    mcol4.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{real_exceptions:,}</div><div class="small-note">Real Exceptions</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    tabs = st.tabs(["Summary","Tender Performance","Classification","Netting Reference","Download"])
    # Summary
    with tabs[0]:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Store Summary (Real Exceptions)")
        if not results['summary'].empty:
            st.dataframe(results['summary'], use_container_width=True, height=400)
        else:
            st.info("No exceptions found after noise removal.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Tender Performance
    with tabs[1]:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Tender Performance Metrics")
        if not results['tender_performance'].empty:
            st.dataframe(results['tender_performance'], use_container_width=True)
            st.markdown("<div class='small-note'>Charts show high-level trends.</div>", unsafe_allow_html=True)
        else:
            st.info("No performance data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Classification
    with tabs[2]:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Exception Classification")
        if not results['classification'].empty:
            st.dataframe(results['classification'], use_container_width=True)
        else:
            st.info("No classification data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Netting Reference
    with tabs[3]:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Netting Items Removed (Noise)")
        if not results['netting_reference'].empty:
            st.dataframe(results['netting_reference'], use_container_width=True, height=300)
        else:
            st.info("No netting detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Download
    with tabs[4]:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Download Report")
        try:
            processor = TenderReconciliationProcessor(netting_threshold=netting_threshold, approval_filter=approval_filter)
            temp_excel_path = f"/tmp/Tender_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            processor.save_to_excel(results, temp_excel_path)
            with open(temp_excel_path, "rb") as f:
                data = f.read()
            st.download_button("📥 Download Excel Report", data=data, file_name=f"Tender_Reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Error generating Excel: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center; margin-top:28px; color: #7a716c; font-size:13px;">
    Tender Reconciliation Dashboard • Warm UX theme • Built for clarity
</div>
""", unsafe_allow_html=True)
