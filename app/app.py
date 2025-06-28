import os
import streamlit as st
import requests
from io import BytesIO
from datetime import datetime, date
from audio_recorder_streamlit import audio_recorder

st.set_page_config(page_title="PDF Q&A Assistant", layout="wide")
st.title("PDF Q&A Assistant")

API_BASE = "http://localhost:8000"

# --- Tabs for features ---
tabs = st.tabs([
    "PDF Upload & Search",
    "Voice Search",
    "Insurance Policy Reminders"
])

# --- 1. Unified PDF Upload & Search ---
with tabs[0]:
    st.header("📚 PDF Upload & Search")
    st.write("Upload one or multiple PDFs and ask questions about them.")
    
    # PDF Upload Section
    st.subheader("📄 Upload PDFs")
    pdf_files = st.file_uploader(
        "Upload one or more PDF files", 
        type="pdf", 
        accept_multiple_files=True,
        key="pdf_uploader"
    )
    
    if pdf_files:
        # Upload all selected PDFs
        uploaded_files = []
        for pdf_file in pdf_files:
            files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
            resp = requests.post(f"{API_BASE}/upload/pdf", files=files)
            if resp.status_code == 200:
                uploaded_files.append(pdf_file.name)
                st.success(f"✅ Uploaded: {pdf_file.name}")
            else:
                st.error(f"❌ Failed to upload {pdf_file.name}: {resp.text}")
        
        if uploaded_files:
            st.info(f"📋 Successfully uploaded {len(uploaded_files)} PDF(s): {', '.join(uploaded_files)}")
    
    # Search Section
    st.subheader("🔍 Ask Questions")
    st.write("You can either type your question or record your voice question.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        text_query = st.text_input("Type your question:", key="pdf_text_query")
        if st.button("🔍 Search (Text)", key="pdf_text_btn") and text_query:
            with st.spinner("Searching through your documents..."):
                resp = requests.post(f"{API_BASE}/ask/all", params={"question": text_query})
                if resp.ok:
                    result = resp.json()
                    st.subheader("📝 Answer")
                    st.write(result.get("answer", "No answer found."))
                    
                    if result.get("source") and result.get("source") != "system":
                        st.info(f"📄 Source: {result.get('source')}")
                    
                    if result.get("confidence"):
                        st.info(f"🎯 Confidence: {result.get('confidence')}")
                else:
                    st.error(f"❌ Error: {resp.text}")
    
    with col2:
        st.write("Or record your voice question:")
        audio_bytes = audio_recorder(key="pdf_voice_query")
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if st.button("🎤 Search with Voice", key="pdf_voice_btn") and audio_bytes:
                with st.spinner("Processing your voice question..."):
                    files = {"audio": ("recorded.wav", BytesIO(audio_bytes), "audio/wav")}
                    resp = requests.post(f"{API_BASE}/voice/search/multiple", files=files)
                    if resp.ok:
                        result = resp.json()
                        st.subheader("🎤 Your Question")
                        st.write(f"*\"{result.get('transcription', 'Could not transcribe')}\"*")
                        
                        st.subheader("📝 Answer")
                        st.write(result.get("answer", "No answer found."))
                        
                        if result.get("source") and result.get("source") != "system":
                            st.info(f"📄 Source: {result.get('source')}")
                        
                        if result.get("confidence"):
                            st.info(f"🎯 Confidence: {result.get('confidence')}")
                    else:
                        st.error(f"❌ Error: {resp.text}")

# --- 2. Voice Search (Alternative Interface) ---
with tabs[1]:
    st.header("🎤 Voice Search")
    st.write("You can either type your question or record your voice question to search across all uploaded PDFs.")
    
    # Check if any PDFs are uploaded
    resp = requests.get(f"{API_BASE}/files/pdf")
    if resp.ok:
        files = resp.json().get("files", [])
        if files:
            st.success(f"📚 Found {len(files)} uploaded PDF(s): {', '.join(files)}")
        else:
            st.warning("⚠️ No PDFs uploaded yet. Please upload some PDFs first.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        text_query = st.text_input("Type your question:", key="voice_tab_text_query")
        if st.button("🔍 Search (Text)", key="voice_tab_text_btn") and text_query:
            with st.spinner("Searching through your documents..."):
                resp = requests.post(f"{API_BASE}/ask/all", params={"question": text_query})
                if resp.ok:
                    result = resp.json()
                    st.subheader("📝 Answer")
                    st.write(result.get("answer", "No answer found."))
                    
                    if result.get("source") and result.get("source") != "system":
                        st.info(f"📄 Source: {result.get('source')}")
                    
                    if result.get("confidence"):
                        st.info(f"🎯 Confidence: {result.get('confidence')}")
                else:
                    st.error(f"❌ Error: {resp.text}")
    
    with col2:
        st.write("Or record your voice question:")
        audio_bytes = audio_recorder(key="voice_tab_voice_query")
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if st.button("🎤 Search with Voice", key="voice_tab_voice_btn") and audio_bytes:
                with st.spinner("Processing your voice question..."):
                    files = {"audio": ("recorded.wav", BytesIO(audio_bytes), "audio/wav")}
                    resp = requests.post(f"{API_BASE}/voice/search/multiple", files=files)
                    if resp.ok:
                        result = resp.json()
                        st.subheader("🎤 Your Question")
                        st.write(f"*\"{result.get('transcription', 'Could not transcribe')}\"*")
                        
                        st.subheader("📝 Answer")
                        st.write(result.get("answer", "No answer found."))
                        
                        if result.get("source") and result.get("source") != "system":
                            st.info(f"📄 Source: {result.get('source')}")
                        
                        if result.get("confidence"):
                            st.info(f"🎯 Confidence: {result.get('confidence')}")
                    else:
                        st.error(f"❌ Error: {resp.text}")

# --- 3. Insurance Policy Due Date Reminder ---
with tabs[2]:
    st.header("📋 Insurance Policy Reminders")
    st.write("Upload insurance policies and get due date reminders.")
    
    if "policies" not in st.session_state:
        st.session_state["policies"] = []
    if "last_uploaded" not in st.session_state:
        st.session_state["last_uploaded"] = None

    # Policy Upload
    st.subheader("📄 Upload Insurance Policies")
    policy_files = st.file_uploader(
        "Upload insurance policy PDFs", 
        type="pdf", 
        accept_multiple_files=True, 
        key="policy_uploader"
    )
    
    if policy_files:
        for pdf_file in policy_files:
            files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
            resp = requests.post(f"{API_BASE}/upload/policy", files=files)
            if resp.status_code == 200:
                st.success(f"✅ Uploaded: {pdf_file.name}")
                st.session_state["last_uploaded"] = pdf_file.name
            else:
                st.error(f"❌ Failed: {pdf_file.name} - {resp.text}")
        
        # Refresh policies after upload
        resp = requests.get(f"{API_BASE}/policies")
        if resp.ok:
            st.session_state["policies"] = resp.json().get("policies", [])

    # Policy Management
    st.subheader("📅 Policy Management")
    selected_date = st.date_input(
        "Select a date to check for policy due dates",
        value=date.today(),
        key="calendar_policy_due_date"
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Show All Policies"):
            policies = st.session_state.get("policies", [])
            if not policies:
                st.info("No policies found.")
            else:
                for policy in policies:
                    try:
                        due_date = datetime.fromisoformat(policy["due_date"]).date()
                        st.write(f"📄 **{policy['file_path']}** - Due: {due_date}")
                    except Exception:
                        st.warning(f"Could not parse due date for {policy['file_path']}")

    with col2:
        if st.button("🔔 Check Reminders"):
            policies = st.session_state.get("policies", [])
            if not policies:
                st.info("No policies found.")
            else:
                found_reminder = False
                for policy in policies:
                    try:
                        due_date = datetime.fromisoformat(policy["due_date"]).date()
                        days_left = (due_date - selected_date).days
                        
                        if 0 <= days_left <= 7:
                            found_reminder = True
                            if days_left == 0:
                                st.error(f"🚨 **TODAY**: {policy['file_path']} is due today!")
                            elif days_left == 1:
                                st.warning(f"⚠️ **TOMORROW**: {policy['file_path']} is due tomorrow!")
                            else:
                                st.info(f"📅 **{days_left} days left**: {policy['file_path']}")
                        elif days_left < 0:
                            st.warning(f"⏰ **OVERDUE**: {policy['file_path']} is {abs(days_left)} days overdue!")
                            
                    except Exception:
                        st.warning(f"Could not parse due date for {policy['file_path']}")
                
                # Special info for last uploaded policy
                last_uploaded = st.session_state.get("last_uploaded")
                if last_uploaded:
                    match = [p for p in policies if last_uploaded in p["file_path"]]
                    if match:
                        due_date = datetime.fromisoformat(match[0]["due_date"]).date()
                        days_left = (due_date - selected_date).days
                        if not (0 <= days_left <= 7):
                            st.info(f"📄 Your latest upload ({last_uploaded}) is due on {due_date}")
                
                if not found_reminder:
                    st.success("✅ No urgent reminders for the next 7 days.")

# --- Sidebar with additional info ---
with st.sidebar:
    st.header("ℹ️ Information")
    st.write("**PDF Storage Location:**")
    st.code("C:\\Users\\rajes\\OneDrive\\Documents\\Personal\\practice_projects\\text_voice_chatbot\\pdfs")
    
    st.write("**Current Status:**")
    try:
        resp = requests.get(f"{API_BASE}/files/pdf")
        if resp.ok:
            files = resp.json().get("files", [])
            st.success(f"✅ Backend connected")
            st.write(f"📚 {len(files)} PDF(s) uploaded")
        else:
            st.error("❌ Backend not connected")
    except:
        st.error("❌ Backend not running")
        st.write("Please start the backend server first.")
    
    st.write("---")
    st.write("**Quick Actions:**")
    if st.button("🔄 Refresh Status"):
        st.rerun()
