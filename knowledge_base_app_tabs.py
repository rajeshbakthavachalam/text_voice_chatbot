from dotenv import load_dotenv
load_dotenv()

import os
import openai
import threading
import streamlit as st
from background_indexer import start_background_indexing

# Start the background indexer as a daemon thread (only once per session)
def run_background_indexer_once():
    if "background_indexer_started" not in st.session_state:
        t = threading.Thread(target=start_background_indexing, args=("pdfs",), daemon=True)
        t.start()
        st.session_state["background_indexer_started"] = True

run_background_indexer_once()

# --- AI Suggestion Function ---
def get_suggested_questions_local(context, answer, n=3):
    """Generate n follow-up questions using intelligent local logic based on context and answer."""
    try:
        # Convert to lowercase for better matching
        context_lower = context.lower().strip()
        answer_lower = answer.lower().strip()
        
        # Clean and normalize the context
        context_words = [word.strip('.,?!') for word in context_lower.split() if len(word.strip('.,?!')) > 2]
        
        # Extract key topics and entities from the question
        topics = extract_topics_from_question(context_lower, context_words)
        
        # Extract important terms from the answer
        answer_terms = extract_important_terms(answer_lower)
        
        # Generate contextually relevant questions
        suggestions = generate_contextual_questions(context_lower, topics, answer_terms)
        
        # Filter and rank suggestions
        ranked_suggestions = rank_suggestions(suggestions, context_lower, answer_lower)
        
        # Return top n suggestions
        return ranked_suggestions[:n]
        
    except Exception as e:
        # Fallback questions if anything goes wrong
        return [
            "What are the next steps in this process?",
            "What documents or information do I need?",
            "How long does this typically take?"
        ]

def extract_topics_from_question(question, words):
    """Extract meaningful topics from the question."""
    topics = []
    
    # Common insurance and business terms
    insurance_terms = [
        'policy', 'coverage', 'claim', 'benefit', 'premium', 'deductible',
        'copay', 'network', 'provider', 'enrollment', 'eligibility',
        'renewal', 'cancellation', 'exclusion', 'limitation', 'rider',
        'insurance', 'medical', 'health', 'hospital', 'treatment'
    ]
    
    # Process-related terms
    process_terms = [
        'application', 'submission', 'approval', 'rejection', 'review',
        'processing', 'verification', 'documentation', 'requirements',
        'deadline', 'timeline', 'procedure', 'steps', 'guidelines',
        'process', 'procedure', 'method', 'way', 'approach'
    ]
    
    # Financial terms
    financial_terms = [
        'cost', 'price', 'amount', 'payment', 'billing', 'invoice',
        'discount', 'savings', 'refund', 'deduction', 'credit',
        'money', 'fee', 'charge', 'expense', 'budget'
    ]
    
    # Time-related terms
    time_terms = [
        'time', 'duration', 'period', 'deadline', 'schedule',
        'when', 'how long', 'timeline', 'processing time'
    ]
    
    # Find insurance-related topics
    for term in insurance_terms:
        if term in question:
            topics.append(term)
    
    # Find process-related topics
    for term in process_terms:
        if term in question:
            topics.append(term)
    
    # Find financial topics
    for term in financial_terms:
        if term in question:
            topics.append(term)
    
    # Find time-related topics
    for term in time_terms:
        if term in question:
            topics.append(term)
    
    # Extract specific entities (capitalized words that might be important)
    entities = []
    for word in words:
        if (word[0].isupper() and len(word) > 3 and 
            word.lower() not in ['what', 'when', 'where', 'which', 'whose', 'how', 'why', 'this', 'that', 'these', 'those']):
            entities.append(word)
    
    if entities:
        topics.extend(entities[:2])  # Limit to 2 entities
    
    return list(set(topics))  # Remove duplicates

def extract_important_terms(answer):
    """Extract important terms from the answer."""
    terms = []
    
    # Split answer into sentences and words
    sentences = answer.split('.')
    
    # Common important terms to look for
    important_keywords = [
        'policy', 'coverage', 'claim', 'benefit', 'premium', 'deductible',
        'copay', 'network', 'provider', 'enrollment', 'eligibility',
        'application', 'submission', 'approval', 'rejection', 'review',
        'processing', 'verification', 'documentation', 'requirements',
        'deadline', 'timeline', 'procedure', 'steps', 'guidelines',
        'cost', 'price', 'amount', 'payment', 'billing', 'invoice',
        'discount', 'savings', 'refund', 'deduction', 'credit'
    ]
    
    for sentence in sentences:
        words = sentence.split()
        for word in words:
            # Clean the word
            clean_word = word.strip('.,!?;:()[]{}"\'').lower()
            
            # Look for important terms
            if (len(clean_word) > 4 and  # Longer words are often more specific
                clean_word in important_keywords and
                clean_word not in terms):
                terms.append(clean_word)
    
    # If no important keywords found, look for longer technical terms
    if not terms:
        for sentence in sentences:
            words = sentence.split()
            for word in words:
                clean_word = word.strip('.,!?;:()[]{}"\'').lower()
                if (len(clean_word) > 6 and 
                    clean_word not in ['policy', 'coverage', 'claim', 'benefit', 'process', 'document', 'information', 'required'] and
                    not clean_word.isdigit() and
                    clean_word not in terms):
                    terms.append(clean_word)
    
    return terms[:5]  # Return unique terms, limit to 5

def generate_contextual_questions(question, topics, answer_terms):
    """Generate contextually relevant questions based on topics and answer terms."""
    suggestions = []
    
    # Question type detection
    question_type = detect_question_type(question)
    
    # Generate questions based on question type and topics
    if question_type == 'what':
        suggestions.extend(generate_what_questions(topics, answer_terms))
    elif question_type == 'how':
        suggestions.extend(generate_how_questions(topics, answer_terms))
    elif question_type == 'when':
        suggestions.extend(generate_when_questions(topics, answer_terms))
    elif question_type == 'where':
        suggestions.extend(generate_where_questions(topics, answer_terms))
    elif question_type == 'why':
        suggestions.extend(generate_why_questions(topics, answer_terms))
    elif question_type == 'who':
        suggestions.extend(generate_who_questions(topics, answer_terms))
    else:
        # Generic questions for any type
        suggestions.extend(generate_generic_questions(topics, answer_terms))
    
    return suggestions

def detect_question_type(question):
    """Detect the type of question being asked."""
    question_starters = {
        'what': ['what', 'which'],
        'how': ['how'],
        'when': ['when'],
        'where': ['where'],
        'why': ['why'],
        'who': ['who', 'whom']
    }
    
    for q_type, starters in question_starters.items():
        for starter in starters:
            if question.startswith(starter):
                return q_type
    
    return 'generic'

def generate_what_questions(topics, answer_terms):
    """Generate 'what' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['policy', 'coverage', 'claim']:
            questions.extend([
                f"What are the key features of this {topic}?",
                f"What documents are required for {topic} processing?",
                f"What are the limitations of this {topic}?",
                f"What happens if my {topic} is denied?",
                f"What information do I need to provide for my {topic}?"
            ])
        elif topic in ['benefit', 'premium', 'deductible']:
            questions.extend([
                f"What factors affect my {topic} amount?",
                f"What are the {topic} calculation methods?",
                f"What changes can affect my {topic}?",
                f"What is included in my {topic} coverage?"
            ])
        elif topic in ['application', 'submission', 'approval']:
            questions.extend([
                f"What is the {topic} process?",
                f"What documents do I need for {topic}?",
                f"What are the {topic} requirements?",
                f"What happens after I submit my {topic}?"
            ])
        elif topic in ['eligibility', 'enrollment']:
            questions.extend([
                f"What are the eligibility criteria for this {topic}?",
                f"What documents prove my {topic}?",
                f"What happens if I don't meet the {topic} requirements?"
            ])
    
    # Add questions based on answer terms (only if they're meaningful)
    for term in answer_terms[:2]:
        if term not in topics and len(term) > 4:
            questions.append(f"What is {term} and how does it affect my coverage?")
    
    return questions

def generate_how_questions(topics, answer_terms):
    """Generate 'how' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['claim', 'application', 'submission']:
            questions.extend([
                f"How do I submit a {topic}?",
                f"How long does {topic} processing take?",
                f"How can I track my {topic} status?",
                f"How do I appeal a {topic} decision?",
                f"How do I know if my {topic} was received?"
            ])
        elif topic in ['coverage', 'policy']:
            questions.extend([
                f"How does this {topic} protect me?",
                f"How can I maximize my {topic} benefits?",
                f"How do I know if something is covered?",
                f"How do I update my {topic} information?"
            ])
        elif topic in ['eligibility', 'enrollment']:
            questions.extend([
                f"How do I check my {topic} status?",
                f"How do I enroll in this {topic}?",
                f"How can I maintain my {topic}?"
            ])
    
    return questions

def generate_when_questions(topics, answer_terms):
    """Generate 'when' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['deadline', 'timeline', 'processing']:
            questions.extend([
                f"When is the deadline for this {topic}?",
                f"When should I start the {topic} process?",
                f"When will I receive a response?",
                f"When do I need to submit my {topic}?"
            ])
        elif topic in ['renewal', 'expiration']:
            questions.extend([
                f"When does my {topic} expire?",
                f"When should I renew my {topic}?",
                f"When do changes take effect?",
                f"When will my {topic} be processed?"
            ])
        elif topic in ['claim', 'application']:
            questions.extend([
                f"When should I submit my {topic}?",
                f"When will my {topic} be reviewed?",
                f"When can I expect a decision on my {topic}?"
            ])
    
    return questions

def generate_where_questions(topics, answer_terms):
    """Generate 'where' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['submission', 'application']:
            questions.extend([
                f"Where can I submit my {topic}?",
                f"Where can I find {topic} forms?",
                f"Where can I get help with my {topic}?",
                f"Where do I send my {topic} documents?"
            ])
        elif topic in ['provider', 'network']:
            questions.extend([
                f"Where can I find in-network {topic}s?",
                f"Where is the nearest {topic} location?",
                f"Where can I get covered services?"
            ])
        elif topic in ['information', 'details']:
            questions.extend([
                f"Where can I find more information about this?",
                f"Where are the policy details located?",
                f"Where can I access my account information?"
            ])
    
    return questions

def generate_why_questions(topics, answer_terms):
    """Generate 'why' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['denial', 'rejection']:
            questions.extend([
                f"Why was my {topic} denied?",
                f"Why might a {topic} be rejected?",
                f"Why do I need to provide additional information?",
                f"Why was my {topic} not approved?"
            ])
        elif topic in ['requirement', 'documentation']:
            questions.extend([
                f"Why is this {topic} necessary?",
                f"Why do I need to provide this information?",
                f"Why are these documents required?"
            ])
        elif topic in ['coverage', 'benefit']:
            questions.extend([
                f"Why is this {topic} important?",
                f"Why should I have this {topic}?",
                f"Why does this {topic} matter?"
            ])
    
    return questions

def generate_who_questions(topics, answer_terms):
    """Generate 'who' questions based on topics."""
    questions = []
    
    for topic in topics:
        if topic in ['contact', 'support', 'help']:
            questions.extend([
                f"Who should I contact for {topic}?",
                f"Who can help me with this process?",
                f"Who is responsible for processing my request?",
                f"Who can I call for assistance?"
            ])
        elif topic in ['provider', 'specialist']:
            questions.extend([
                f"Who are the qualified {topic}s?",
                f"Who can provide this service?",
                f"Who should I see for treatment?"
            ])
        elif topic in ['approval', 'decision']:
            questions.extend([
                f"Who makes the final decision?",
                f"Who reviews my application?",
                f"Who should I contact about my case?"
            ])
    
    return questions

def generate_generic_questions(topics, answer_terms):
    """Generate generic follow-up questions."""
    questions = []
    
    # Process-related questions
    questions.extend([
        "What are the next steps in this process?",
        "How long does this typically take?",
        "What documents do I need to prepare?",
        "Are there any important deadlines I should know?",
        "What happens if something goes wrong?",
        "How can I track the progress?",
        "What are the costs involved?",
        "Are there any restrictions or limitations?",
        "What should I do if I have questions?",
        "How do I get started with this process?"
    ])
    
    # Topic-specific questions
    for topic in topics:
        if topic in ['policy', 'coverage']:
            questions.extend([
                f"What are the key benefits of this {topic}?",
                f"How can I maximize my {topic} benefits?",
                f"What are the limitations of this {topic}?",
                f"How do I know what's covered under my {topic}?"
            ])
        elif topic in ['claim', 'application']:
            questions.extend([
                f"What is the {topic} process?",
                f"How do I submit a {topic}?",
                f"What documents are needed for {topic}?",
                f"How do I check the status of my {topic}?"
            ])
        elif topic in ['eligibility', 'enrollment']:
            questions.extend([
                f"What are the eligibility requirements?",
                f"How do I check if I'm eligible?",
                f"What happens if I'm not eligible?",
                f"How do I enroll in this program?"
            ])
    
    return questions

def rank_suggestions(suggestions, original_question, answer):
    """Rank suggestions by relevance to the original question and answer."""
    ranked = []
    
    for suggestion in suggestions:
        score = 0
        
        # Score based on question similarity (avoid too similar questions)
        if suggestion.lower() != original_question.lower():
            score += 10
        
        # Score based on topic relevance
        original_words = set(original_question.lower().split())
        suggestion_words = set(suggestion.lower().split())
        common_words = original_words.intersection(suggestion_words)
        
        # Good overlap but not too much
        if 1 <= len(common_words) <= 3:
            score += 5
        elif len(common_words) > 3:
            score -= 2  # Penalize too similar questions
        
        # Score based on answer relevance
        answer_words = set(answer.lower().split())
        suggestion_answer_overlap = suggestion_words.intersection(answer_words)
        if len(suggestion_answer_overlap) > 0:
            score += 3
        
        # Prefer questions that start with different question words
        question_words = ['what', 'how', 'when', 'where', 'why', 'who']
        original_starter = next((word for word in question_words if original_question.lower().startswith(word)), None)
        suggestion_starter = next((word for word in question_words if suggestion.lower().startswith(word)), None)
        
        if original_starter != suggestion_starter:
            score += 2
        
        # Bonus for questions that seem more actionable
        action_words = ['how', 'what', 'when', 'where']
        if any(word in suggestion.lower() for word in action_words):
            score += 1
        
        # Penalize very generic questions
        generic_phrases = ['what is', 'how does', 'when is', 'where is']
        if any(phrase in suggestion.lower() for phrase in generic_phrases):
            score -= 1
        
        ranked.append((suggestion, score))
    
    # Sort by score (highest first) and return just the questions
    ranked.sort(key=lambda x: x[1], reverse=True)
    return [question for question, score in ranked]

# --- Query normalization function ---
def normalize_query(query):
    query = query.lower()
    query = query.replace('summarise', 'summarize')
    query = query.replace('this documents', 'these documents')
    query = query.replace('document', 'documents')  # handle singular/plural
    # Add more normalization rules as needed
    return query

import requests
from io import BytesIO
from datetime import datetime, date
from audio_recorder_streamlit import audio_recorder
from knowledge_base_manager import KnowledgeBaseManager
import time
import pdfplumber
import re
import pandas as pd

# Initialize session state variables
if 'last_bill_pdf_name' not in st.session_state:
    st.session_state['last_bill_pdf_name'] = None
if 'bill_items' not in st.session_state:
    st.session_state['bill_items'] = None
if 'eligibility_results' not in st.session_state:
    st.session_state['eligibility_results'] = None
if 'total_eligible' not in st.session_state:
    st.session_state['total_eligible'] = 0.0
if 'eligibility_checked' not in st.session_state:
    st.session_state['eligibility_checked'] = False
if 'eligibility_cache' not in st.session_state:
    st.session_state['eligibility_cache'] = {}

# Page configuration
st.set_page_config(
    page_title="PDF Knowledge Base Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize knowledge base manager
@st.cache_resource
def get_knowledge_base():
    return KnowledgeBaseManager()

kb_manager = get_knowledge_base()

# Sidebar for knowledge base management
with st.sidebar:
    st.header("📚 Knowledge Base Management")
    status = kb_manager.get_knowledge_base_status()
    st.subheader("📊 Status")
    st.metric("Total Documents", status["total_documents"])
    st.metric("Indexed Documents", status["indexed_documents"])
    if status["pending_documents_list"]:
        st.warning(f"⚠️ {len(status['pending_documents_list'])} documents need indexing")
    
    st.subheader("📋 Supported File Types")
    supported_types = status.get("supported_extensions", [])
    if supported_types:
        for ext in supported_types:
            st.write(f"• {ext.upper()}")
    
    st.subheader("🔧 Index Management")
    if st.button("🔄 Index All Documents", type="primary"):
        with st.spinner("Indexing documents..."):
            results = kb_manager.index_all_documents()
        success_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - success_count
        
        if success_count > 0:
            st.success(f"✅ Successfully indexed {success_count}/{len(results)} documents")
            if failed_count > 0:
                st.warning(f"⚠️ {failed_count} document(s) failed to index")
        else:
            st.error("❌ No documents were successfully indexed")
            
        with st.expander("📋 Detailed Indexing Results"):
            for file_name, success in results.items():
                if success:
                    st.write(f"✅ {file_name} - Indexed successfully")
                else:
                    st.write(f"❌ {file_name} - Failed to index")
    
    if st.button("🔄 Auto-Index New Files"):
        with st.spinner("Checking for new files..."):
            results = kb_manager.auto_index_new_files()
        if results:
            success_count = sum(1 for success in results.values() if success)
            st.success(f"✅ Auto-indexed {success_count} new document(s)")
        else:
            st.info("ℹ️ No new files found to index")
    
    if st.button("🗑️ Rebuild Index"):
        if st.button("⚠️ Confirm Rebuild", type="secondary"):
            with st.spinner("Rebuilding index..."):
                results = kb_manager.rebuild_index()
            success_count = sum(1 for success in results.values() if success)
            st.success(f"✅ Index rebuilt successfully! {success_count} documents re-indexed")
            st.info("🔄 All existing collections have been cleared and recreated")
    
    if status["indexed_documents_list"]:
        st.subheader("📖 Indexed Documents")
        for file_name in status["indexed_documents_list"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                file_info = kb_manager.get_document_info(file_name)
                file_type = file_info.get("file_type", "unknown").upper()
                st.write(f"📄 {file_name} ({file_type})")
            with col2:
                if st.button("🗑️", key=f"remove_{file_name}"):
                    if kb_manager.remove_document(file_name):
                        st.success(f"✅ Successfully removed '{file_name}' from knowledge base")
                        st.info("🗂️ Collection deleted and index updated")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to remove '{file_name}'. Please try again.")

# Main content
st.title("📚 Document Knowledge Base Q&A")
st.markdown("Ask questions about your indexed documents using text or voice!")

# Check if we have indexed documents
if not status["indexed_documents_list"]:
    st.warning("⚠️ No documents are indexed yet. Please index some documents using the sidebar.")
    st.info("💡 Place your document files (PDF, DOCX, CSV, TXT, RAR, ZIP) in the documents directory and click 'Index All Documents' in the sidebar.")
    st.stop()

indexed_documents = status["indexed_documents_list"]

# Tabs for different search modes
tabs = st.tabs([
    "🔍 Queries",  # Changed from "PDF Search" to "Queries"
    "🎤 Voice Search",
    "🏥 Hospital Bill Eligibility Check",
    "📊 Knowledge Base Info",
    "📈 Evaluation Metrics"
])

# Unified PDF Search (formerly Multi-PDF Search)
with tabs[0]:
    st.header("🔍 Queries")
    st.info(f"🔍 Searching across {len(indexed_documents)} indexed documents")
    
    # --- Regeneration state management ---
    if 'multi_pdf_regenerated' not in st.session_state:
        st.session_state['multi_pdf_regenerated'] = False
    if 'multi_pdf_regen_result' not in st.session_state:
        st.session_state['multi_pdf_regen_result'] = None
    if 'multi_pdf_last_question' not in st.session_state:
        st.session_state['multi_pdf_last_question'] = None
    if 'multi_pdf_regeneration_count' not in st.session_state:
        st.session_state['multi_pdf_regeneration_count'] = 0
    if 'multi_pdf_current_question' not in st.session_state:
        st.session_state['multi_pdf_current_question'] = ""
    if 'multi_pdf_suggestion_trigger' not in st.session_state:
        st.session_state['multi_pdf_suggestion_trigger'] = None
    if 'multi_pdf_input_key' not in st.session_state:
        st.session_state['multi_pdf_input_key'] = 0

    # Handle AI suggestions
    if st.session_state['multi_pdf_suggestion_trigger']:
        st.session_state['multi_pdf_current_question'] = st.session_state['multi_pdf_suggestion_trigger']
        st.session_state['multi_pdf_suggestion_trigger'] = None
        st.session_state['multi_pdf_input_key'] += 1  # Force text input refresh
        # Reset regeneration state when a new question is asked
        st.session_state['multi_pdf_regenerated'] = False
        st.session_state['multi_pdf_regen_result'] = None
        st.session_state['multi_pdf_regeneration_count'] = 0
    
    # Get the current question (either from input or suggestion)
    question = st.text_input(
        "Ask a question about your documents:", 
        value=st.session_state['multi_pdf_current_question'],
        key=f"multi_pdf_question_input_{st.session_state['multi_pdf_input_key']}"
    )
    
    # Update current question if user types something new
    if question and question != st.session_state['multi_pdf_current_question']:
        st.session_state['multi_pdf_current_question'] = question

    # Reset regeneration state if a new question is asked (including AI suggestions)
    if question and question != st.session_state['multi_pdf_last_question']:
        st.session_state['multi_pdf_regenerated'] = False
        st.session_state['multi_pdf_regen_result'] = None
        st.session_state['multi_pdf_last_question'] = question
        st.session_state['multi_pdf_regeneration_count'] = 0

    if question:
        norm_question = normalize_query(question)
        
        # If answer was regenerated, show only regenerated answer/feedback
        if st.session_state['multi_pdf_regenerated'] and st.session_state['multi_pdf_regen_result']:
            result = st.session_state['multi_pdf_regen_result']
            st.success("✅ New answer generated!")
            st.subheader("🔄 Regenerated Answer")
            st.write(result["answer"])
            # --- AI Suggestions ---
            suggested_questions = get_suggested_questions_local(question, result["answer"])
            if suggested_questions:
                st.markdown("#### You can also ask:")
                for i, q in enumerate(suggested_questions):
                    if st.button(q, key=f"suggested_q_multi_regen_{i}_{st.session_state['multi_pdf_input_key']}"):
                        st.session_state['multi_pdf_suggestion_trigger'] = q
                        st.experimental_rerun()
            col1, col2 = st.columns(2)
            with col1:
                sources = []
                if "sources" in result:
                    sources = result["sources"]
                elif "details" in result and "sources" in result["details"]:
                    sources = result["details"]["sources"]
                if sources:
                    st.markdown("**Reference File(s):**")
                    unique_file_names = list(dict.fromkeys([os.path.basename(pdf) for pdf in sources]))
                    if unique_file_names:
                        st.write(f"📄 {unique_file_names[0]}")
                else:
                    file_type = result.get("file_type", "pdf")
                    file_name = result.get("file_name", "Unknown")
                    st.metric("Source", f"{file_name} ({file_type})")
            if "details" in result:
                with st.expander("📋 Search Details"):
                    details = result["details"]
                    if "sources" in details:
                        st.write("**Sources used:**")
                        for source in details["sources"]:
                            st.write(f"• {source}")
                    if "total_sources_checked" in details:
                        st.write(f"**Total sources checked:** {details['total_sources_checked']}")
            if "indexed_pdfs" in result:
                with st.expander("📚 Indexed PDFs"):
                    for pdf in result["indexed_pdfs"]:
                        st.write(f"• {pdf}")
            st.markdown("---")
            st.subheader("💬 Feedback on regenerated answer")
            regen_feedback_col1, regen_feedback_col2 = st.columns([1, 2])
            with regen_feedback_col1:
                regen_feedback = st.radio("Was this regenerated answer helpful?", ("👍 Yes", "👎 No"), key="multi_pdf_regen_feedback")
            with regen_feedback_col2:
                regen_comment = st.text_area("Additional comments (optional):", key="multi_pdf_regen_comment")
            if st.button("Submit Feedback", key="multi_pdf_regen_submit_feedback"):
                import csv
                from datetime import datetime
                regen_feedback_data = {
                    "timestamp": datetime.now().isoformat(),
                    "tab": "multi_pdf_regenerated",
                    "question": question,
                    "answer": result["answer"],
                    "feedback": regen_feedback,
                    "comment": regen_comment
                }
                feedback_file = "feedback_log.csv"
                try:
                    with open(feedback_file, "a", newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=regen_feedback_data.keys())
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow(regen_feedback_data)
                    st.success("✅ Thank you for your feedback on the regenerated answer!")
                    st.info("🔄 This helps us improve our regeneration algorithm.")
                except Exception as e:
                    st.error(f"❌ Could not save feedback: {e}")
                # Allow further regeneration if still not satisfied
                if regen_feedback == "👎 No":
                    st.session_state['multi_pdf_regeneration_count'] += 1
                    if st.session_state['multi_pdf_regeneration_count'] < 3:  # Limit to 3 regenerations
                        with st.spinner("Trying to generate an even better answer..."):
                            # Use different search parameters for variety
                            regenerated_result = kb_manager.search_all_documents(norm_question + " (provide more detailed answer)")
                        st.session_state['multi_pdf_regen_result'] = regenerated_result
                        st.experimental_rerun()
                    else:
                        st.warning("⚠️ Maximum regeneration attempts reached. Please try rephrasing your question.")
        else:
            # Show original answer and feedback
            with st.spinner("🔍 Searching across all documents..."):
                result = kb_manager.search_all_documents(norm_question)
            if "error" in result and result["error"]:
                st.error(result["error"])
            else:
                st.success(f"✅ Found answer across {len(indexed_documents)} indexed documents")
                st.subheader("📝 Answer")
                st.write(result["answer"])
                # --- AI Suggestions ---
                suggested_questions = get_suggested_questions_local(question, result["answer"])
                if suggested_questions:
                    st.markdown("#### You can also ask:")
                    for i, q in enumerate(suggested_questions):
                        if st.button(q, key=f"suggested_q_multi_{i}_{st.session_state['multi_pdf_input_key']}"):
                            st.session_state['multi_pdf_suggestion_trigger'] = q
                            st.experimental_rerun()
                col1, col2 = st.columns(2)
                with col1:
                    sources = []
                    if "sources" in result:
                        sources = result["sources"]
                    elif "details" in result and "sources" in result["details"]:
                        sources = result["details"]["sources"]
                    if sources:
                        st.markdown("**Reference File(s):**")
                        unique_file_names = list(dict.fromkeys([os.path.basename(pdf) for pdf in sources]))
                        if unique_file_names:
                            st.write(f"📄 {unique_file_names[0]}")
                    else:
                        file_type = result.get("file_type", "pdf")
                        file_name = result.get("file_name", "Unknown")
                        st.metric("Source", f"{file_name} ({file_type})")
                if "details" in result:
                    with st.expander("📋 Search Details"):
                        details = result["details"]
                        if "sources" in details:
                            st.write("**Sources used:**")
                            for source in details["sources"]:
                                st.write(f"• {source}")
                        if "total_sources_checked" in details:
                            st.write(f"**Total sources checked:** {details['total_sources_checked']}")
                if "indexed_pdfs" in result:
                    with st.expander("📚 Indexed PDFs"):
                        for pdf in result["indexed_pdfs"]:
                            st.write(f"• {pdf}")
                st.markdown("---")
                st.subheader("💬 Feedback on this answer")
                feedback_col1, feedback_col2 = st.columns([1, 2])
                with feedback_col1:
                    feedback = st.radio("Was this answer helpful?", ("👍 Yes", "👎 No"), key="multi_pdf_feedback")
                with feedback_col2:
                    comment = st.text_area("Additional comments (optional):", key="multi_pdf_comment")
                if st.button("Submit Feedback", key="multi_pdf_submit_feedback"):
                    import csv
                    from datetime import datetime
                    feedback_data = {
                        "timestamp": datetime.now().isoformat(),
                        "tab": "multi_pdf",
                        "question": question,
                        "answer": result["answer"],
                        "feedback": feedback,
                        "comment": comment
                    }
                    feedback_file = "feedback_log.csv"
                    try:
                        with open(feedback_file, "a", newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=feedback_data.keys())
                            if f.tell() == 0:
                                writer.writeheader()
                            writer.writerow(feedback_data)
                        st.success("✅ Thank you for your feedback! Your response has been recorded.")
                        st.info("📊 This feedback helps us improve our document search accuracy.")
                    except Exception as e:
                        st.error(f"❌ Could not save feedback: {e}")
                    # Regenerate answer if thumbs down
                    if feedback == "👎 No":
                        st.session_state['multi_pdf_regeneration_count'] += 1
                        with st.spinner("Trying to generate a better answer..."):
                            # Use different search parameters to get a different answer
                            regenerated_result = kb_manager.search_all_documents(norm_question + " (provide alternative perspective)")
                        st.session_state['multi_pdf_regenerated'] = True
                        st.session_state['multi_pdf_regen_result'] = regenerated_result
                        st.experimental_rerun()

# Tab 2: Voice Search
with tabs[1]:
    st.header("🎤 Voice Search")

    # Restore last mode and PDF if set by suggestion
    if 'voice_mode_last' in st.session_state:
        st.session_state['voice_mode_radio'] = st.session_state.pop('voice_mode_last')
    if 'voice_pdf_last' in st.session_state:
        st.session_state['voice_pdf_select'] = st.session_state.pop('voice_pdf_last')

    voice_mode = st.radio(
        "Choose voice search mode:",
        ["Single Document", "All Documents"],
        horizontal=True,
        key="voice_mode_radio"
    )
    if voice_mode == "Single Document":
        selected_document = st.selectbox(
            "Choose a document for voice search:",
            indexed_documents,
            key="voice_pdf_select"
        )
        st.info(f"🎤 Speak your question about: {selected_document}")
    else:
        selected_document = None
        st.info(f"🎤 Speak your question to search across {len(indexed_documents)} documents")
    st.write("🎙️ Record your voice question:")

    # --- Handle AI-suggested question trigger ---
    # (AI suggestions removed for Voice Search)
    if 'voice_search_question' in st.session_state and st.session_state['voice_search_question']:
        transcription = st.session_state.pop('voice_search_question')
        norm_transcription = normalize_query(transcription)
        if st.session_state['voice_mode_radio'] == "Single Document":
            result = kb_manager.search_single_document(st.session_state['voice_pdf_select'], norm_transcription)
        else:
            result = kb_manager.search_all_documents(norm_transcription)
        st.success("✅ (AI Suggestion) Processed suggested question as voice input!")
        st.info(f"🎤 Transcribed: '{transcription}'")
        st.subheader("📝 Answer")
        st.write(result.get("answer", "No answer found."))
        # Show reference PDFs if available
        col1, col2 = st.columns(2)
        with col1:
            sources = []
            if "sources" in result:
                sources = result["sources"]
            elif "details" in result and "sources" in result["details"]:
                sources = result["details"]["sources"]
            if sources:
                st.markdown("**Reference Document(s):**")
                for pdf in sources:
                    st.write(f"📄 {pdf}")
            else:
                st.metric("Source", result.get("source", "Unknown"))
        st.stop()

    audio_bytes = audio_recorder(key="voice_search")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("🔍 Process Voice Question", type="primary", key="voice_search_btn"):
            with st.spinner("🎤 Processing voice and searching knowledge base..."):
                files = {"audio": ("recorded.wav", BytesIO(audio_bytes), "audio/wav")}
                if st.session_state['voice_mode_radio'] == "Single Document":
                    resp = requests.post(f"http://localhost:8000/ask/document/{st.session_state['voice_pdf_select']}/voice", files=files)
                else:
                    resp = requests.post(f"http://localhost:8000/voice/search/multiple", files=files)
                if resp.ok:
                    result = resp.json()
                    transcription = result.get("transcription", "[No transcription]")
                    norm_transcription = normalize_query(transcription)
                    if st.session_state['voice_mode_radio'] == "Single Document":
                        result = kb_manager.search_single_document(st.session_state['voice_pdf_select'], norm_transcription)
                    else:
                        result = kb_manager.search_all_documents(norm_transcription)
                    st.success("✅ Voice transcription completed successfully!")
                    st.info(f"🎤 Transcribed: '{transcription}'")
                    st.subheader("📝 Answer")
                    st.write(result.get("answer", "No answer found."))
                    # Show reference PDFs if available
                    col1, col2 = st.columns(2)
                    with col1:
                        sources = []
                        if "sources" in result:
                            sources = result["sources"]
                        elif "details" in result and "sources" in result["details"]:
                            sources = result["details"]["sources"]
                        if sources:
                            st.markdown("**Reference Document(s):**")
                            for pdf in sources:
                                st.write(f"📄 {pdf}")
                        else:
                            st.metric("Source", result.get("source", "Unknown"))

# Tab 3: Hospital Bill Eligibility Check
with tabs[2]:
    st.header("🏥 Hospital Bill Eligibility Check")
    bill_pdf = st.file_uploader("Upload hospital bill (PDF)", type="pdf", key="hospital_bill_eligibility_uploader")
    if bill_pdf and (bill_pdf.name != st.session_state['last_bill_pdf_name']):
        st.session_state['bill_items'] = None
        st.session_state['eligibility_results'] = None
        st.session_state['total_eligible'] = 0.0
        st.session_state['eligibility_checked'] = False
        st.session_state['eligibility_cache'] = {}
        st.session_state['last_bill_pdf_name'] = bill_pdf.name
        with st.spinner("Extracting items from hospital bill..."):
            items = []
            try:
                with pdfplumber.open(bill_pdf) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                if row and len(row) >= 2:
                                    item = str(row[0]).strip()
                                    amount = None
                                    for cell in row[1:]:
                                        if cell and re.search(r"\d", str(cell)):
                                            amt = re.sub(r"[^\d.]+", "", str(cell))
                                            try:
                                                amount = float(amt)
                                                break
                                            except:
                                                continue
                                    if item and amount is not None:
                                        items.append({"item": item, "amount": amount})
            except Exception as e:
                st.error(f"❌ Error extracting items: {e}")
                items = []
            st.session_state['bill_items'] = items
            if items:
                st.success(f"✅ Successfully extracted {len(items)} items from the hospital bill")
                st.info("📋 Bill items have been processed and are ready for eligibility check")
            else:
                st.warning("⚠️ No items could be extracted from the uploaded bill")

    items = st.session_state['bill_items']
    if bill_pdf and items and not st.session_state['eligibility_checked']:
        with st.spinner("Checking eligibility for each item..."):
            results = []
            total_eligible = 0.0
            for entry in items:
                item_name = entry["item"]
                amount = entry["amount"]
                
                # Check cache first
                if item_name in st.session_state['eligibility_cache']:
                    eligible = st.session_state['eligibility_cache'][item_name]
                else:
                    # Make the query more deterministic and strict
                    query = f"Is '{item_name}' payable under my insurance policy? Answer with ONLY 'Yes' or 'No'. Do not provide any explanation."
                    result = kb_manager.search_all_documents(normalize_query(query))
                    answer = result.get("answer", "No").lower().strip()
                    
                    # Very strict eligibility check - only accept exact "yes" or "no"
                    eligible = answer == "yes"
                    
                    # Cache the result
                    st.session_state['eligibility_cache'][item_name] = eligible
                
                if eligible:
                    total_eligible += amount
                
                results.append({
                    "Item": item_name,
                    "Amount": amount,
                    "Eligible": "✅ Yes" if eligible else "❌ No",
                    "Reason": "Eligible for coverage" if eligible else "Not covered under policy"
                })
            
            st.session_state['eligibility_results'] = results
            st.session_state['total_eligible'] = total_eligible
            st.session_state['eligibility_checked'] = True
            st.success(f"✅ Eligibility check completed for {len(items)} items")
            st.info(f"💰 Total eligible amount: ₹{total_eligible:,.2f}")

    results = st.session_state['eligibility_results']
    total_eligible = st.session_state['total_eligible']
    
    if bill_pdf:
        if not items:
            st.warning("⚠️ No itemized charges found in the uploaded PDF. Please upload a clear, itemized bill.")
            st.info("💡 Make sure the bill contains a table with item names and amounts.")
        else:
            st.success(f"✅ Found {len(items)} items in the bill.")
            st.markdown("### Eligibility Results")
            st.dataframe(results, use_container_width=True)
            st.markdown(f"**Total Eligible Amount:** ₹{total_eligible:,.2f}")

# Tab 4: Knowledge Base Info
with tabs[3]:
    st.header("📊 Knowledge Base Information")
    if st.button("🔄 Refresh Status"):
        st.rerun()
    st.subheader("📈 Current Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documents", status["total_documents"])
    with col2:
        st.metric("Indexed Documents", status["indexed_documents"])
    with col3:
        st.metric("Pending", len(status["pending_documents_list"]))
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Indexed Documents")
        if status["indexed_documents_list"]:
            for pdf in status["indexed_documents_list"]:
                st.write(f"✅ {pdf}")
        else:
            st.write("No documents indexed yet")
    with col2:
        st.subheader("⏳ Pending Documents")
        if status["pending_documents_list"]:
            for pdf in status["pending_documents_list"]:
                st.write(f"⏳ {pdf}")
        else:
            st.write("All documents are indexed")
    st.subheader("🔧 Technical Details")
    st.write(f"**Database Location:** {kb_manager.db_directory}")
    st.write(f"**Document Directory:** {kb_manager.documents_directory}")
    st.write(f"**Index File:** {kb_manager.index_file}")

# Tab 5: Evaluation Metrics
with tabs[4]:
    st.header("📈 Evaluation Metrics")
    st.markdown("Evaluate the performance of your knowledge base system with comprehensive metrics.")
    
    # Initialize session state for evaluation
    if 'evaluation_results' not in st.session_state:
        st.session_state['evaluation_results'] = None
    if 'test_queries' not in st.session_state:
        st.session_state['test_queries'] = []
    if 'evaluation_history' not in st.session_state:
        st.session_state['evaluation_history'] = kb_manager.get_evaluation_history()
    
    # Sidebar for evaluation controls
    with st.sidebar:
        st.header("🔧 Evaluation Controls")
        
        # Load sample test queries
        if st.button("📋 Load Sample Queries"):
            st.session_state['test_queries'] = kb_manager.create_sample_test_queries()
            st.success("✅ Sample test queries loaded successfully!")
            st.info("🧪 You can now run evaluation or modify these queries as needed.")
        
        # Load evaluation history
        if st.session_state['evaluation_history']:
            st.subheader("📚 Previous Evaluations")
            selected_history = st.selectbox(
                "Choose evaluation to load:",
                st.session_state['evaluation_history'],
                key="history_select"
            )
            if st.button("📥 Load Selected Evaluation"):
                loaded_results = kb_manager.load_evaluation_results(selected_history)
                if loaded_results:
                    st.session_state['evaluation_results'] = loaded_results
                    st.success(f"✅ Successfully loaded evaluation: {selected_history}")
                    st.info("📊 Previous evaluation results are now displayed below.")
                else:
                    st.error("❌ Failed to load evaluation results. File may be corrupted.")
    
    # Main evaluation interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🧪 Test Query Management")
        
        # Add new test query
        with st.expander("➕ Add New Test Query", expanded=False):
            query = st.text_input("Query:", key="new_query")
            expected_answer = st.text_area("Expected Answer:", key="new_expected_answer")
            expected_sources = st.text_input("Expected Sources (comma-separated):", key="new_expected_sources")
            document_name = st.selectbox("Document Name (for single document search):", 
                                  [""] + indexed_documents, key="new_document_name")
            
            if st.button("Add Test Query"):
                if query and expected_answer:
                    new_test = {
                        'query': query,
                        'expected_answer': expected_answer,
                        'expected_sources': [s.strip() for s in expected_sources.split(',') if s.strip()],
                        'document_name': document_name if document_name else None
                    }
                    st.session_state['test_queries'].append(new_test)
                    st.success("✅ Test query added successfully!")
                    st.info("📝 You can now run evaluation with this new query.")
                    st.rerun()
                else:
                    st.error("❌ Please provide both a query and expected answer.")
        
        # Display current test queries
        if st.session_state['test_queries']:
            st.subheader(f"📝 Test Queries ({len(st.session_state['test_queries'])})")
            
            for i, test_query in enumerate(st.session_state['test_queries']):
                with st.expander(f"Query {i+1}: {test_query['query'][:50]}..."):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Query:** {test_query['query']}")
                        st.write(f"**Expected Answer:** {test_query['expected_answer']}")
                        if test_query['expected_sources']:
                            st.write(f"**Expected Sources:** {', '.join(test_query['expected_sources'])}")
                        if test_query.get('document_name'):
                            st.write(f"**Document:** {test_query['document_name']}")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_query_{i}"):
                            st.session_state['test_queries'].pop(i)
                            st.success("✅ Test query removed successfully!")
                            st.rerun()
        else:
            st.info("📋 No test queries defined. Add some queries to start evaluation.")
    
    with col2:
        st.subheader("🚀 Run Evaluation")
        
        if st.session_state['test_queries']:
            if st.button("▶️ Run Evaluation", type="primary"):
                with st.spinner("Running evaluation..."):
                    results = kb_manager.evaluate_search_performance(st.session_state['test_queries'])
                    st.session_state['evaluation_results'] = results
                    
                    # Save results
                    filename = kb_manager.save_evaluation_results(results)
                    if filename:
                        st.session_state['evaluation_history'] = kb_manager.get_evaluation_history()
                        st.success(f"✅ Evaluation completed successfully!")
                        st.info(f"💾 Results saved to: {filename}")
                        st.info(f"📊 Evaluated {results['summary']['total_queries']} queries with detailed metrics.")
                    else:
                        st.error("❌ Failed to save evaluation results.")
        else:
            st.warning("⚠️ Add test queries first to run evaluation.")
            st.info("💡 Use the 'Load Sample Queries' button or add custom queries.")
    
    # Display evaluation results
    if st.session_state['evaluation_results']:
        results = st.session_state['evaluation_results']
        summary = results['summary']
        
        st.markdown("---")
        st.subheader("📊 Evaluation Results")
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", summary['total_queries'])
        with col2:
            st.metric("Single Document Queries", summary['single_document_queries'])
        with col3:
            st.metric("Multi Document Queries", summary['multi_document_queries'])
        with col4:
            st.metric("Evaluation Time", results['evaluation_timestamp'][:19])
        
        # Performance metrics
        st.subheader("🎯 Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Answer Relevance", f"{summary['answer_relevance_mean']:.3f}", 
                     f"±{summary['answer_relevance_std']:.3f}")
        with col2:
            st.metric("Keyword Coverage", f"{summary['keyword_coverage_mean']:.3f}", 
                     f"±{summary['keyword_coverage_std']:.3f}")
        with col3:
            st.metric("Length Ratio", f"{summary['length_ratio_mean']:.3f}", 
                     f"±{summary['length_ratio_std']:.3f}")
        with col4:
            st.metric("Confidence", f"{summary['confidence_mean']:.3f}", 
                     f"±{summary['confidence_std']:.3f}")
        
        # Source metrics (if available)
        if 'source_precision_mean' in summary:
            st.subheader("📚 Source Accuracy Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Source Precision", f"{summary['source_precision_mean']:.3f}", 
                         f"±{summary['source_precision_std']:.3f}")
            with col2:
                st.metric("Source Recall", f"{summary['source_recall_mean']:.3f}", 
                         f"±{summary['source_recall_std']:.3f}")
            with col3:
                st.metric("Source F1-Score", f"{summary['source_f1_mean']:.3f}", 
                         f"±{summary['source_f1_std']:.3f}")
            with col4:
                st.metric("Source Accuracy", f"{summary['source_accuracy_mean']:.3f}", 
                         f"±{summary['source_accuracy_std']:.3f}")
        
        # Comparison between single and multi document
        if 'single_document' in summary and 'multi_document' in summary:
            st.subheader("📊 Single vs Multi Document Comparison")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Single Document Performance**")
                st.metric("Answer Relevance", f"{summary['single_document']['answer_relevance_mean']:.3f}")
                st.metric("Keyword Coverage", f"{summary['single_document']['keyword_coverage_mean']:.3f}")
                st.metric("Confidence", f"{summary['single_document']['confidence_mean']:.3f}")
            
            with col2:
                st.markdown("**Multi Document Performance**")
                st.metric("Answer Relevance", f"{summary['multi_document']['answer_relevance_mean']:.3f}")
                st.metric("Keyword Coverage", f"{summary['multi_document']['keyword_coverage_mean']:.3f}")
                st.metric("Confidence", f"{summary['multi_document']['confidence_mean']:.3f}")
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        if results['detailed_results']:
            df = pd.DataFrame(results['detailed_results'])
            
            # Select columns to display
            display_columns = ['query', 'search_type', 'answer_relevance', 'keyword_coverage', 'confidence']
            if 'source_precision' in df.columns:
                display_columns.extend(['source_precision', 'source_recall', 'source_f1'])
            
            st.dataframe(df[display_columns], use_container_width=True)
            
            # Download results
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Performance visualization
        st.subheader("📈 Performance Charts")
        
        if results['detailed_results']:
            df = pd.DataFrame(results['detailed_results'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Answer relevance distribution
                st.write("**Answer Relevance Distribution**")
                st.bar_chart(df['answer_relevance'].value_counts().sort_index())
            
            with col2:
                # Keyword coverage distribution
                st.write("**Keyword Coverage Distribution**")
                st.bar_chart(df['keyword_coverage'].value_counts().sort_index())
            
            # Search type comparison
            if 'search_type' in df.columns:
                st.write("**Answer Relevance by Search Type**")
                comparison_data = df.groupby('search_type')['answer_relevance'].agg(['mean', 'std', 'count']).reset_index()
                st.dataframe(comparison_data, use_container_width=True)
                
                # Show summary statistics
                st.write("**Summary Statistics by Search Type**")
                for search_type in df['search_type'].unique():
                    subset = df[df['search_type'] == search_type]
                    st.write(f"**{search_type.replace('_', ' ').title()}:**")
                    st.write(f"  - Mean Relevance: {subset['answer_relevance'].mean():.3f}")
                    st.write(f"  - Mean Coverage: {subset['keyword_coverage'].mean():.3f}")
                    st.write(f"  - Mean Confidence: {subset['confidence'].mean():.3f}")
                    st.write(f"  - Count: {len(subset)}")
                    st.write("")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        📚 Document Knowledge Base Q&A System | Built with Streamlit and ChromaDB
    </div>
    """,
    unsafe_allow_html=True
) 