import streamlit as st
import requests
import json
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Contract Buddy",
    page_icon="📄",
    layout="wide"
)

# Configuration
API_BASE_URL = st.sidebar.text_input(
    "API URL",
    value="http://localhost:8000",
    help="Base URL of the FastAPI server"
)

# Initialize session state
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None
if "rag_data" not in st.session_state:
    st.session_state.rag_data = None

# Title
st.title("📄 :blue[Contract Buddy]")
st.markdown("Your friend in dealing with everything legal")

# Main layout
left, right = st.columns([0.4, 0.6])

with left:
    st.header("📤 Upload & Extract")
    
    # File uploader
    file = st.file_uploader(
        "Select PDF File",
        type=["pdf"],
        help="Upload a PDF contract file"
    )
    if file:
        st.session_state.pdf_file = file.getvalue()
    
    # Upload button
    if st.button("Upload File", type="primary", use_container_width=True):
        if file is not None:
            files = {"file": (file.name, file.getvalue(), file.type)}
            
            with st.spinner("Uploading file..."):
                try:
                    response = requests.post(
                        url=f"{API_BASE_URL}/ingest",
                        files=files,
                        timeout=120
                    )
                    
                    if response.status_code == 201:
                        result = response.json()
                        st.session_state.uploaded_filename = result.get("filename")
                        st.success(f"✅ File uploaded successfully!")
                        st.info(f"**File:** {result.get('filename')}\n**Size:** {result.get('size', 0) / 1024:.2f} KB")
                    else:
                        error_data = response.json() if response.headers.get("content-type") == "application/json" else {"detail": response.text}
                        st.error(f"❌ Error: {response.status_code}")
                        st.error(error_data.get("detail", "Unknown error occurred"))
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the FastAPI server.")
                    st.info("💡 Make sure the server is running on " + API_BASE_URL)
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The file might be too large.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
        else:
            st.warning("⚠️ Please select a file first")
    
    # Extract button
    if st.button("Extract Data", type="primary", use_container_width=True):
        if st.session_state.uploaded_filename:
            filename = st.session_state.uploaded_filename
        else:
            filename = None
        
        with st.spinner("Extracting data from contract... This may take a moment."):
            try:
                params = {"filename": filename} if filename else {}
                response = requests.get(
                    url=f"{API_BASE_URL}/extract",
                    params=params,
                    timeout=120  # Longer timeout for extraction
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        st.session_state.extracted_data = result.get("data", {})
                        st.success("✅ Data extracted successfully!")
                    else:
                        st.error("❌ Extraction failed")
                        st.json(result)
                else:
                    error_data = response.json() if response.headers.get("content-type") == "application/json" else {"detail": response.text}
                    st.error(f"❌ Error: {response.status_code}")
                    st.error(error_data.get("detail", "Unknown error occurred"))
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the FastAPI server.")
                st.info("💡 Make sure the server is running on " + API_BASE_URL)
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. The extraction process is taking longer than expected.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
    else:
        if not st.session_state.uploaded_filename:
            st.info("💡 Upload a file first, then click 'Extract Data'")

with right:
    st.header("📊 Extracted Data")

    # Display data in organized sections
    tabs = st.tabs(["Overview", "Ask", "Terms & Conditions", "Audit"])

    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        
        with tabs[0]:
            st.subheader("Contract Overview")
            col1, col2 = st.columns(2)
            
            with col1:
                if data.get("parties"):
                    st.markdown("**Parties:**")
                    for party in data.get("parties", []):
                        st.markdown(f"- {party}")
                
                if data.get("effective_date"):
                    st.markdown(f"**Effective Date:** {data.get('effective_date')}")
                
                if data.get("term"):
                    st.markdown(f"**Term:** {data.get('term')}")
            
            with col2:
                if data.get("governing_law"):
                    st.markdown(f"**Governing Law:** {data.get('governing_law')}")
                
                if data.get("signatories"):
                    st.markdown("**Signatories:**")
                    for signatory in data.get("signatories", []):
                        st.markdown(f"- {signatory}")
        
        with tabs[2]:
            st.subheader("Contract Terms & Conditions")
            
            fields = [
                ("Payment Terms", "payment_terms"),
                ("Termination", "termination"),
                ("Auto Renewal", "auto_renewal"),
                ("Confidentiality", "confidentiality"),
                ("Governing Law", "governing_law"),
                ("Indemnity", "indemnity"),
                ("Liability Cap", "liability_cap"),
            ]
            col1, col2 = st.columns(2)
            count = 0
            for label, key in fields:
                if data.get(key):
                    if count<4:
                        with col1:
                            st.expander(label).write(data.get(key))
                    else:
                        with col2:
                            st.expander(label).write(data.get(key))
                count+=1

    else:
        with tabs[0]:
            st.info("Upload a file and extract data to see results")
        with tabs[2]:
            st.info("Upload a file and extract data to see results")         
        
    with tabs[1]:
        st.subheader("Query")

        query = st.chat_input("Type your query")
        response_box = st.container(border=True, height=200)
        if query:
            with st.spinner("Generating Output..."):
                params = {"query": query}
                response = requests.get(f"{API_BASE_URL}/rag", params=params)
                if response.status_code == 200:
                    st.session_state.rag_data = response.json()
                
            with response_box:
                if not st.session_state.rag_data:
                    st.warning("No RAG context available. Please try again.")
                else:
                    payload = {"query": query, "rag_data": st.session_state.rag_data}
                    response = requests.post(
                        f"{API_BASE_URL}/ask",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    if response.status_code == 200:
                        result = response.json()
                        output = result.get("output", "")
                        if output:
                            st.write(output.get("content", ""))
                    else:
                        st.error(f"Ask endpoint failed: {response.status_code}")
                        with st.expander("Error details"):
                            st.write(response.text)
        
        with st.expander("RAG Output"):
            if query:
                st.write(st.session_state.rag_data)
            else:
                st.info("Ask Something!")

        
    with tabs[3]:
        # text_container = st.container(border=True, height=250)
        if st.button("Audit", type="primary", width=150):
            if st.session_state.uploaded_filename:
                filename = st.session_state.uploaded_filename
            else:
                filename = None
            
            with st.spinner("Auditting the document..."):
                try:
                    params = {"filename": filename} if filename else {}
                    response = requests.get(
                        url=f"{API_BASE_URL}/audit",
                        params=params,
                        timeout=120 
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.session_state.audit_data = result.get("data", {})
                            st.success("✅ Data auditted successfully!")

                            data = st.session_state.audit_data
                            for i, risk in enumerate(data.get("risks", [])):
                                with st.expander(f"Risk {i+1}"):
                                    st.write(f"- Finding: {risk.get('finding', '')}")
                                    st.write(f"- Severity: {risk.get('severity', '')}")
                                    st.write(f"- Evidence: {risk.get('evidence', '')}")
                        else:
                            st.error("❌ Audit failed")
                            st.json(result)
                    else:
                        error_data = response.json() if response.headers.get("content-type") == "application/json" else {"detail": response.text}
                        st.error(f"❌ Error: {response.status_code}")
                        st.error(error_data.get("detail", "Unknown error occurred"))
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the FastAPI server.")
                    st.info("💡 Make sure the server is running on " + API_BASE_URL)
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The extraction process is taking longer than expected.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
        else:
            if not st.session_state.uploaded_filename:
                st.info("💡 Upload a file, then click 'Audit'")



# Footer
st.divider()
st.caption("💡 **Tip:** Make sure the FastAPI server is running before uploading files.")


