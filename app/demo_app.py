import os
import streamlit as st
import requests
from io import BytesIO
from datetime import datetime, date
from audio_recorder_streamlit import audio_recorder

# Page configuration
st.set_page_config(
    page_title="Insurance & PDF Search System",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Constants
API_BASE = "http://localhost:8000"

# Title and description
st.title("📄 Insurance & PDF Search System")
st.markdown("""
    This system provides comprehensive PDF search capabilities and insurance policy management.
    Upload documents, search through them, and manage your insurance policies all in one place.
""")

# Initialize session state
if "uploaded_pdf_name" not in st.session_state:
    st.session_state["uploaded_pdf_name"] = None
if "policies" not in st.session_state:
    st.session_state["policies"] = []
if "last_uploaded" not in st.session_state:
    st.session_state["last_uploaded"] = None

# --- Unified PDF Upload Section ---
st.markdown("### 📤 Document Upload")

upload_type = st.radio(
    "Select upload type:",
    ("Single PDF", "Multiple PDFs", "Insurance Policy"),
    horizontal=True
)

accept_multiple = upload_type != "Single PDF"

pdf_files = st.file_uploader(
    "Upload PDF(s)",
    type="pdf",
    accept_multiple_files=accept_multiple,
    key="unified_pdf_uploader"
)

if pdf_files:
    if not isinstance(pdf_files, list):
        pdf_files = [pdf_files]
    if st.button("Upload", key="upload_button"):
        for pdf in pdf_files:
            files = {"file": (pdf.name, pdf, "application/pdf")}
            if upload_type == "Insurance Policy":
                endpoint = f"{API_BASE}/upload/policy"
            else:
                endpoint = f"{API_BASE}/upload/pdf"
            resp = requests.post(endpoint, files=files)
            if resp.status_code == 200:
                st.markdown(f'<div class="success-box">Uploaded: {pdf.name}</div>', unsafe_allow_html=True)
                if upload_type == "Single PDF":
                    st.session_state["uploaded_pdf_name"] = pdf.name
                if upload_type == "Insurance Policy":
                    st.session_state["last_uploaded"] = pdf.name
            else:
                st.markdown(f'<div class="error-box">Failed: {pdf.name} - {resp.text}</div>', unsafe_allow_html=True)
        # Refresh policies after insurance upload
        if upload_type == "Insurance Policy":
            resp = requests.get(f"{API_BASE}/policies")
            if resp.ok:
                st.session_state["policies"] = resp.json()

# --- Search Section ---
st.markdown("### 🔍 Search")
search_type = st.radio(
    "Choose search type:",
    ["Text Search", "Voice Search"],
    horizontal=True
)

if search_type == "Text Search":
    question = st.text_input("Enter your question:")
    if question:
        if st.session_state.get("uploaded_pdf_name"):
            # Single PDF search
            resp = requests.post(
                f"{API_BASE}/ask/pdf/{st.session_state['uploaded_pdf_name']}",
                params={"question": question}
            )
        else:
            # Multiple PDF search
            resp = requests.post(f"{API_BASE}/ask/all", params={"question": question})
        
        if resp.ok:
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            st.write(resp.json())
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="error-box">Error: {resp.text}</div>', unsafe_allow_html=True)
else:
    st.markdown("#### Voice Search")
    st.write("Record your voice question:")
    audio_bytes = audio_recorder(key="voice_search")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        files = {"audio": ("recorded.wav", BytesIO(audio_bytes), "audio/wav")}
        resp = requests.post(f"{API_BASE}/voice/search/multiple", files=files)
        if resp.ok:
            st.markdown('<div class="feature-box">', unsafe_allow_html=True)
            st.write(resp.json())
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="error-box">Error: {resp.text}</div>', unsafe_allow_html=True)

# --- Insurance Policy Section ---
st.markdown("### 📋 Insurance Policy Management")

# Policy Due Date Checker
st.markdown("#### Policy Due Date Checker")

# Use columns with better width ratio for alignment
col_date, col_button = st.columns([2, 1])

with col_date:
    selected_date = st.date_input(
        "Select a date to check for policy due dates",
        value=date.today(),
        key="calendar_policy_due_date"
    )

reminder_clicked = False
with col_button:
    reminder_clicked = st.button("Check Reminders", key="check_reminders", use_container_width=True)

if reminder_clicked:
    policies = st.session_state.get("policies", [])
    if not policies:
        st.info("No policies found.")
    else:
        found_reminder = False
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        for policy in policies:
            try:
                due_date = datetime.fromisoformat(policy["due_date"]).date()
                days_left = (due_date - selected_date).days
                st.write(f"Policy: {policy['file_path']}, Due: {due_date}")
                if 0 <= days_left <= 7:
                    found_reminder = True
                    if days_left == 0:
                        st.markdown(f'<div class="error-box">Today is the due date for {policy["file_path"]}! Please pay your insurance policy now.</div>', unsafe_allow_html=True)
                    elif days_left == 1:
                        st.markdown(f'<div class="error-box">Only 1 day left to pay your insurance policy: {policy["file_path"]}!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="success-box">You have {days_left} days left to pay your insurance policy: {policy["file_path"]}.</div>', unsafe_allow_html=True)
                elif days_left < 0:
                    st.markdown(f'<div class="error-box">This policy due date has passed: {policy["file_path"]}.</div>', unsafe_allow_html=True)
            except Exception:
                st.warning(f"Could not parse due date for {policy['file_path']}")
        st.markdown('</div>', unsafe_allow_html=True)
        if not found_reminder:
            st.info("No reminders for any policy in the next 7 days.") 