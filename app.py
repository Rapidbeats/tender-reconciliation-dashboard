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

# --- CSS / Theme: Accessible warm palette with dark-mode overrides ---
st.markdown(
    """
    <style>
    /* Base variables (light mode) */
    :root{
      --bg: #FFF8F2;
      --page-bg: linear-gradient(180deg,#FFF8F2 0%, #FFFDF9 100%);
      --card: #FFFFFF;
      --text: #2e2b27;
      --muted: #6e6b68;
      --accent: #b35a1e;    /* warm burnt orange */
      --accent-2: #2b5d4a;  /* deep warm green */
      --soft: #f2c57c;
      --panel-glass: rgba(255,255,255,0.85);
    }

    /* Dark-mode overrides */
    @media (prefers-color-scheme: dark) {
      :root{
        --bg: #0f1416;
        --page-bg: linear-gradient(180deg,#0f1416 0%, #0b0d0e 100%);
        --card: rgba(18,20,22,0.7);
        --text: #efeae6;      /* high-contrast text */
        --muted: #bfb8b2;     /* lighter muted text */
        --accent: #ff9a56;    /* brighter warm accent for dark */
        --accent-2: #49a07a;
        --soft: #f3c57e;
        --panel-glass: rgba(255,255,255,0.03);
      }
    }

    html, body, .reportview-container, .main {
      background: var(--page-bg) !important;
      color: var(--text) !important;
    }

    /* Header */
    .header {
      display:flex;
      align-items:center;
      gap:18px;
      padding: 6px 0 12px 0;
      margin-bottom: 6px;
    }
    .brand {
      width:68px;
      height:68px;
      border-radius:12px;
      background: linear-gradient(135deg, var(--accent-2), var(--accent));
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-weight:700;
      box-shadow: 0 8px 30px rgba(43,93,74,0.12);
      font-family: 'Inter', sans-serif;
    }
    .title { font-size:30px; font-weight:700; margin:0; color:var(--text); }
    .subtitle { color:var(--muted); margin-top:3px; font-size:13px; }

    /* Panels & cards */
    .panel {
      background: var(--card);
      border-radius:12px;
      padding:18px;
      box-shadow: 0 8px 30px rgba(11,12,13,0.06);
      color: var(--text);
    }
    @media (prefers-color-scheme: dark) {
      .panel { box-shadow: 0 6px 24px rgba(0,0,0,0.6); }
    }

    /* Upload slots */
    .file-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; }
    .upload-slot {
      border: 1px dashed rgba(110,107,104,0.08);
      height:120px;
      border-radius:10px;
      display:flex;
      flex-direction:column;
      align-items:center;
      justify-content:center;
      color:var(--muted);
      transition: all .18s ease;
      background: linear-gradient(180deg, rgba(242,197,124,0.03), rgba(255,255,255,0.02));
      font-weight:600;
    }
    @media (prefers-color-scheme: dark) {
      .upload-slot {
        background: linear-gradient(180deg, rgba(255,154,86,0.02), rgba(255,255,255,0.02));
        border: 1px dashed rgba(255,255,255,0.06);
        color: var(--muted);
      }
    }
    .upload-slot:hover { transform: translateY(-6px); box-shadow: 0 12px 36px rgba(0,0,0,0.25); }

    /* Buttons */
    .action-btn {
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      color:white;
      border-radius:10px;
      padding:10px 18px;
      font-weight:700;
      border: none;
      cursor:pointer;
      box-shadow: 0 10px 30px rgba(163,90,34,0.12);
    }
    .action-btn:hover { transform: translateY(-3px); opacity:0.98; }

    /* Metrics */
    .metric {
      padding:12px;
      border-radius:10px;
      background: linear-gradient(180deg, rgba(43,93,74,0.03), rgba(255,255,255,0.02));
      text-align:center;
      color:var(--text);
    }
    @media (prefers-color-scheme: dark) {
      .metric { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); }
    }

    .small-note { font-size:12px; color:var(--muted); margin-top:6px; }

    /* Animations */
    .fadein { animation: fadeIn .7s ease both; }
    @keyframes fadeIn { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }

    /* Accessibility tweaks for streamlit text areas inside our panels */
    .panel * { color: var(--text) !important; }
    .upload-slot, .panel .small-note, .panel a { color: var(--muted) !important; }

    /* Ensure Streamlit uploader text is visible in dark mode */
    .css-1kq8b8b, .css-1d391kg, .stText, label {
      color: var(--text) !important;
    }

    /* Footer */
    .footer { text-align:center; color:var(--muted); margin-top:18px; font-size:13px; }

    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
hdr_col1, hdr_col2 = st.columns([0.12, 0.88])
with hdr_col1:
    st.markdown('<div class="brand">TR</div>', unsafe_allow_html=True)
with hdr_col2:
    st.markdown(
        '<div class="header"><div><h1 class="title">Tender Reconciliation Dashboard</h1>'
        '<div class="subtitle">Warm, professional interface — fast, clear reconciliation</div></div></div>',
        unsafe_allow_html=True
    )

st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="panel"><h4 style="margin:0 0 8px 0">⚙️ Configuration</h4>', unsafe_allow_html=True)
    netting_threshold = st.slider("Netting Threshold (±)", 1.0, 100.0, 5.0, 0.5)
    approval_option = st.radio("Processing Mode", ["All Responses", "Auto-Approved Only"])
    approval_filter = 'auto_approved_only' if approval_option == "Auto-Approved Only" else 'all'
    st.markdown('<div class="small-note">Adjust netting sensitivity to tune noise removal.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Upload area ---
st.markdown('<div class="panel fadein"><h3 style="margin:0 0 12px 0">📁 Upload Tender CSVs</h3>', unsafe_allow_html=True)

col_a, col_b = st.columns([2.6, 1])
uploaded_files = {}
with col_a:
    st.markdown('<div class="file-grid">', unsafe_allow_html=True)
    for label in ['Cash', 'Card', 'UPI', 'Wallet']:
        key = label.lower()
        st.markdown(f'<div class="upload-slot"><strong>{label}</strong><div class="small-note">Headers at row 6 · CSV</div></div>', unsafe_allow_html=True)
        file = st.file_uploader(f"Upload {label} CSV", type=['csv'], key=key, label_visibility="hidden")
        if file:
            uploaded_files[label] = file
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="panel"><h4 style="margin:0 0 8px 0">Requirements</h4>', unsafe_allow_html=True)
    st.markdown("""
        <div class="small-note">
        • CSV format with headers on row 6<br>
        • Columns: Store ID, Store Response Entry, Auto Approved Date (optional)<br>
        • Non-zero responses only
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Process button ---
proc_col, help_col = st.columns([3,1])
with proc_col:
    if st.button("🚀 Process Reconciliation", key="process"):
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

with help_col:
    st.markdown('<div style="padding-top:6px"><button class="action-btn" onclick="window.scrollTo(0,document.body.scrollHeight)">📥 Help</button></div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- Results ---
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    st.markdown('<div class="panel fadein"><h3 style="margin:0 0 12px 0">📊 Processing Results</h3>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{results.get("total_stores",0):,}</div><div class="small-note">Total Stores</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{results.get("exception_stores",0):,}</div><div class="small-note">Stores with Exceptions</div></div>', unsafe_allow_html=True)
    exc_rate = (results.get('exception_stores',0)/results.get('total_stores',1)*100) if results.get('total_stores',0)>0 else 0
    c3.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{exc_rate:.2f}%</div><div class="small-note">Exception Rate</div></div>', unsafe_allow_html=True)
    real_exceptions = len(results['summary']) if not results['summary'].empty else 0
    c4.markdown(f'<div class="metric"><div style="font-size:18px; font-weight:700">{real_exceptions:,}</div><div class="small-note">Real Exceptions</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    tabs = st.tabs(["Summary","Tender Performance","Classification","Netting Reference","Download"])

    with tabs[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Store Summary (Real Exceptions)")
        if not results['summary'].empty:
            st.dataframe(results['summary'], use_container_width=True, height=420)
        else:
            st.info("No exceptions found after noise removal.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Tender Performance Metrics")
        if not results['tender_performance'].empty:
            st.dataframe(results['tender_performance'], use_container_width=True)
        else:
            st.info("No performance data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Exception Classification")
        if not results['classification'].empty:
            st.dataframe(results['classification'], use_container_width=True)
        else:
            st.info("No classification data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Netting Items Removed (Noise)")
        if not results['netting_reference'].empty:
            st.dataframe(results['netting_reference'], use_container_width=True, height=300)
        else:
            st.info("No netting detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
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

st.markdown('<div class="footer">Tender Reconciliation Dashboard • Warm UX theme • Built for clarity</div>', unsafe_allow_html=True)
