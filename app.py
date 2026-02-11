import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from tender_reconciliation_final_v8_updated import TenderReconciliationProcessor
import warnings

warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Tender Reconciliation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        color: #4472C4;
        text-align: center;
        margin-bottom: 1em;
    }
    .sub-header {
        font-size: 1.5em;
        color: #333;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    .info-box {
        background-color: #E7F3FF;
        padding: 1em;
        border-left: 4px solid #4472C4;
        border-radius: 5px;
        margin: 1em 0;
    }
    .success-box {
        background-color: #E6F7E6;
        padding: 1em;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1em 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1em;
        border-left: 4px solid #ff9800;
        border-radius: 5px;
        margin: 1em 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<div class="main-header">📊 TENDER RECONCILIATION DASHBOARD</div>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ CONFIGURATION")
    st.markdown("---")
    
    # Netting Threshold
    st.markdown("#### Netting Threshold")
    st.markdown("""
    <div class="info-box">
    The threshold determines when entries are considered 'noise' that can be removed.
    
    **Recommended values:**
    - ±1-5: Strict (remove almost all noise)
    - ±5-10: Moderate (balanced)
    - ±10-50: Lenient (keep most data)
    - ±50-100: Very lenient (minimal filtering)
    </div>
    """, unsafe_allow_html=True)
    
    netting_threshold = st.slider(
        "Select Netting Threshold (±)",
        min_value=1.0,
        max_value=100.0,
        value=5.0,
        step=0.5,
        help="Entries combining to less than this amount are removed as 'noise'"
    )
    
    # Approval Filter
    st.markdown("#### Approval Filter")
    st.markdown("""
    <div class="info-box">
    Choose how to process store responses:
    - **All Responses**: Process all entries regardless of approval status
    - **Auto-Approved Only**: Process only entries that are auto-approved
    </div>
    """, unsafe_allow_html=True)
    
    approval_option = st.radio(
        "Processing Mode:",
        ["All Responses", "Auto-Approved Only"],
        help="Select which entries to include in reconciliation"
    )
    
    approval_filter = 'auto_approved_only' if approval_option == "Auto-Approved Only" else 'all'
    
    st.markdown("---")
    st.markdown(f"**Selected Configuration:**")
    st.markdown(f"- 🎯 Netting Threshold: ±{netting_threshold}")
    st.markdown(f"- ✓ Processing Mode: {approval_option}")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📁 FILE UPLOAD")
    st.markdown("""
    <div class="info-box">
    Upload your 4 tender CSV files:
    - Cash Reconciliation
    - Card Reconciliation
    - UPI Reconciliation
    - Wallet Reconciliation
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📋 REQUIREMENTS")
    st.markdown("""
    <div class="info-box">
    **File Requirements:**
    ✓ CSV format
    ✓ Headers at row 6
    ✓ Columns: Store ID, Store Response Entry, Auto Approved Date
    ✓ Non-zero response values only
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# File uploads
st.markdown("### 📤 UPLOAD TENDER FILES")

col1, col2, col3, col4 = st.columns(4)

uploaded_files = {}

with col1:
    st.markdown("**Cash**")
    cash_file = st.file_uploader(
        "Upload Cash CSV",
        type=['csv'],
        key='cash',
        label_visibility="collapsed"
    )
    if cash_file:
        uploaded_files['Cash'] = cash_file

with col2:
    st.markdown("**Card**")
    card_file = st.file_uploader(
        "Upload Card CSV",
        type=['csv'],
        key='card',
        label_visibility="collapsed"
    )
    if card_file:
        uploaded_files['Card'] = card_file

with col3:
    st.markdown("**UPI**")
    upi_file = st.file_uploader(
        "Upload UPI CSV",
        type=['csv'],
        key='upi',
        label_visibility="collapsed"
    )
    if upi_file:
        uploaded_files['UPI'] = upi_file

with col4:
    st.markdown("**Wallet**")
    wallet_file = st.file_uploader(
        "Upload Wallet CSV",
        type=['csv'],
        key='wallet',
        label_visibility="collapsed"
    )
    if wallet_file:
        uploaded_files['Wallet'] = wallet_file

st.markdown("---")

# Processing section
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    process_button = st.button(
        "🚀 PROCESS RECONCILIATION",
        use_container_width=True,
        type="primary"
    )

if process_button:
    if len(uploaded_files) == 0:
        st.error("❌ Please upload at least one file to process")
    else:
        with st.spinner(f"Processing {len(uploaded_files)} file(s)..."):
            try:
                # Create temporary file paths
                temp_files = {}
                for tender_name, uploaded_file in uploaded_files.items():
                    temp_path = f"/tmp/{tender_name}_{uploaded_file.name}"
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    temp_files[tender_name] = temp_path
                
                # Initialize processor with selected threshold and approval filter
                processor = TenderReconciliationProcessor(
                    netting_threshold=netting_threshold,
                    approval_filter=approval_filter
                )
                
                # Process files
                results = processor.process_all_tenders(temp_files)
                
                if results is None:
                    st.error("❌ Processing failed. Please check your files.")
                else:
                    st.session_state.results = results
                    st.session_state.processing_complete = True
                    st.success("✅ Processing completed successfully!")
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")

# Display results
if st.session_state.processing_complete and st.session_state.results:
    results = st.session_state.results
    
    st.markdown("---")
    st.markdown("### 📊 PROCESSING RESULTS")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Stores",
            f"{results['total_stores']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Stores with Exceptions",
            f"{results['exception_stores']:,}",
            delta=None
        )
    
    with col3:
        exception_rate = (results['exception_stores'] / results['total_stores'] * 100) if results['total_stores'] > 0 else 0
        st.metric(
            "Exception Rate",
            f"{exception_rate:.2f}%",
            delta=None
        )
    
    with col4:
        real_exceptions = len(results['summary']) if not results['summary'].empty else 0
        st.metric(
            "Real Exceptions",
            f"{real_exceptions:,}",
            delta=f"-{results['exception_stores'] - real_exceptions if results['exception_stores'] > real_exceptions else 0:,} (noise)"
        )
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Summary",
        "📊 Tender Performance",
        "🎯 Classification",
        "🔍 Netting Reference",
        "📥 Download Report"
    ])
    
    with tab1:
        st.markdown("### Store Summary (Real Exceptions)")
        if not results['summary'].empty:
            st.dataframe(
                results['summary'],
                use_container_width=True,
                height=400
            )
            st.markdown(f"**Total Rows:** {len(results['summary']):,}")
        else:
            st.info("ℹ️ No exceptions found after noise removal")
    
    with tab2:
        st.markdown("### Tender Performance Metrics")
        if not results['tender_performance'].empty:
            # Display metrics
            st.dataframe(
                results['tender_performance'],
                use_container_width=True
            )
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Exception Rate by Tender")
                chart_data = results['tender_performance'][['Tender', 'Exception_Rate_%']].set_index('Tender')
                st.bar_chart(chart_data)
            
            with col2:
                st.markdown("#### Total vs Exceptional Entries")
                chart_data = results['tender_performance'][['Tender', 'Total_Entries', 'Exceptional_Entries']].set_index('Tender')
                st.bar_chart(chart_data)
        else:
            st.info("ℹ️ No performance data available")
    
    with tab3:
        st.markdown("### Exception Classification")
        if not results['classification'].empty:
            st.dataframe(
                results['classification'],
                use_container_width=True
            )
            
            # Pie chart
            st.markdown("#### Distribution by Classification")
            chart_data = results['classification'].set_index('Classification')['Store_Count']
            st.pie_chart(chart_data)
        else:
            st.info("ℹ️ No classification data available")
    
    with tab4:
        st.markdown("### Netting Items Removed (Noise)")
        if not results['netting_reference'].empty:
            st.dataframe(
                results['netting_reference'],
                use_container_width=True,
                height=400
            )
            st.markdown(f"**Total Pairs Removed:** {len(results['netting_reference']):,}")
        else:
            st.info("ℹ️ No netting detected")
    
    with tab5:
        st.markdown("### 📥 DOWNLOAD RESULTS")
        st.markdown("""
        <div class="success-box">
        Click the button below to download the complete reconciliation report in Excel format with:
        - Formatted sheets with Palatino Linotype font
        - SUBTOTAL functions for numeric columns
        - Professional styling and charts
        - All detailed exception data
        </div>
        """, unsafe_allow_html=True)
        
        # Generate Excel file
        try:
            output = io.BytesIO()
            processor = TenderReconciliationProcessor(nesting_threshold=netting_threshold)
            
            # Create temporary Excel file
            temp_excel_path = f"/tmp/Tender_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            processor.save_to_excel(results, temp_excel_path)
            
            # Read and provide download
            with open(temp_excel_path, 'rb') as f:
                excel_data = f.read()
            
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_data,
                file_name=f"Tender_Reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success("✅ Excel file is ready for download!")
            
        except Exception as e:
            st.error(f"❌ Error generating Excel file: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 2em;">
    <p>Tender Reconciliation Dashboard v13.2 | Streamlit Edition</p>
    <p>For support, contact the development team</p>
</div>
""", unsafe_allow_html=True)
