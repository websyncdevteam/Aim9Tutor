import streamlit as st
import tempfile
from pathlib import Path

# Import core modules
from config import settings
from core.pdf_validator import validate_pdf, PDFValidationError
from core.pdf_processor import process_pdf
from core.vector_store import VectorStore
from core.chat_engine import ChatEngine
from core.teach_engine import TeachEngine
from core.quiz_engine import QuizEngine
from core.voice_engine import VoiceEngine
from core.progress_manager import ProgressManager
from core.usage_tracker import UsageTracker

# ------------------------------------------------------------
# Custom CSS – Dark Theme (white text on dark background)
# ------------------------------------------------------------
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global dark theme */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }

    /* Main title – keep gradient but make it pop on dark */
    .main-title {
        background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem !important;
        margin-bottom: 0.5rem;
    }

    /* Sidebar title */
    .sidebar-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff !important;
        text-align: center;
        margin-bottom: 1rem;
        border-bottom: 3px solid #818cf8;
        padding-bottom: 0.5rem;
    }

    /* Sidebar itself */
    .css-1d391kg {
        background-color: #1e1e2e !important;
    }
    .sidebar .sidebar-content {
        background-color: #1e1e2e;
    }

    /* Card containers – dark with subtle border */
    .card {
        background-color: #262730 !important;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        border: 1px solid #3e3f4e;
        color: #f0f0f0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff !important;
        margin-bottom: 1rem;
        border-left: 5px solid #818cf8;
        padding-left: 1rem;
    }

    /* Buttons – keep gradient but ensure text white */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        background: linear-gradient(90deg, #4f46e5 0%, #7e22ce 100%);
        color: white !important;
        transition: all 0.2s ease;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #4338ca 0%, #6b21a5 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        transform: translateY(-1px);
    }

    /* Radio buttons – dark background, white text */
    .stRadio label {
        background: #2d2f3a !important;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 1px solid #4b5563;
        cursor: pointer;
        transition: background 0.2s;
    }
    .stRadio label:hover {
        background: #3f4250 !important;
    }
    .stRadio label span {
        color: white !important;
    }
    /* Selected radio state */
    .stRadio [data-baseweb="radio"] input:checked + div {
        background-color: #818cf8 !important;
        border-color: #a78bfa !important;
    }

    /* Select boxes, text inputs – dark */
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input {
        background-color: #2d2f3a !important;
        color: white !important;
        border-color: #4b5563 !important;
    }

    /* Chat input and messages */
    .stChatInput input {
        background-color: #2d2f3a !important;
        color: white !important;
        border: 1px solid #4b5563 !important;
    }
    .stChatMessage {
        background-color: #262730 !important;
        color: white !important;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .stChatMessage p {
        color: white !important;
    }

    /* User/assistant differentiation */
    .stChatMessage[data-testid="user-message"] {
        background-color: #2e3a4f !important;
    }
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #2d2f3a !important;
    }

    /* Audio player – make it fit dark theme */
    audio {
        border-radius: 20px;
        margin-top: 0.5rem;
        width: 100%;
        filter: invert(1) hue-rotate(180deg); /* optional: invert colors for dark mode */
    }

    /* Alert boxes – keep readable */
    .stAlert {
        border-radius: 8px;
        border-left: 5px solid;
        background-color: #2d2f3a !important;
        color: white !important;
    }
    .stAlert p {
        color: white !important;
    }

    /* Metrics */
    .stMetric {
        background-color: #262730 !important;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #3e3f4e;
    }
    .stMetric label, .stMetric .metric-value {
        color: white !important;
    }

    /* Sidebar text elements */
    .sidebar-content p, .sidebar-content span, .sidebar-content label {
        color: #e5e7eb !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem !important;
        }
        .sidebar-title {
            font-size: 1.5rem;
        }
        .stButton button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# API Key Check
# ------------------------------------------------------------
API_KEY_MISSING = not settings.GOOGLE_API_KEY
if API_KEY_MISSING:
    st.set_page_config(page_title="AIM9tutor (Preview Mode)", layout="wide")
else:
    st.set_page_config(page_title="AIM9tutor", layout="wide")

# ------------------------------------------------------------
# Initialize Session State (same as before)
# ------------------------------------------------------------
if 'progress' not in st.session_state:
    st.session_state.progress = ProgressManager()
if 'usage' not in st.session_state:
    st.session_state.usage = UsageTracker()
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = VectorStore()

# Chat engine – only if API key exists
if 'chat_engine' not in st.session_state:
    if not API_KEY_MISSING:
        try:
            st.session_state.chat_engine = ChatEngine()
        except Exception as e:
            st.session_state.chat_engine = None
            st.error(f"Failed to initialize Chat Engine: {e}")
    else:
        st.session_state.chat_engine = None

# Voice engine – only if API key exists
if 'voice_engine' not in st.session_state:
    if not API_KEY_MISSING:
        try:
            st.session_state.voice_engine = VoiceEngine()
        except Exception as e:
            st.session_state.voice_engine = None
            st.warning(f"Voice engine disabled: {e}")
    else:
        st.session_state.voice_engine = None

# Teach/Quiz engines depend on chat_engine
if 'teach_engine' not in st.session_state:
    st.session_state.teach_engine = None
if 'quiz_engine' not in st.session_state:
    st.session_state.quiz_engine = None

# UI state
if 'mode' not in st.session_state:
    st.session_state.mode = "Teach"
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
if 'language' not in st.session_state:
    st.session_state.language = "English"
if 'gender' not in st.session_state:
    st.session_state.gender = "female"

# ------------------------------------------------------------
# Sidebar (same layout, now with dark theme)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">📚 AIM9tutor</div>', unsafe_allow_html=True)

    if API_KEY_MISSING:
        st.error("🚫 **Google API Key Missing**")
        st.caption("Add your key to `.env` to enable AI features. UI shown for preview only.")
        st.markdown("---")
    
    # PDF Upload
    uploaded_file = st.file_uploader("Upload PDF (Class 1-9)", type=["pdf"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = Path(tmp.name)
        
        try:
            preview = validate_pdf(tmp_path)
            st.success("✅ PDF validated successfully!")
            st.session_state.pdf_uploaded = True
            st.session_state.pdf_path = tmp_path
            st.session_state.pdf_name = uploaded_file.name
            st.session_state.progress.load_chapter(uploaded_file.name)
            
            with st.spinner("Processing PDF..."):
                chunks = process_pdf(tmp_path)
                st.session_state.vector_store.create_collection()
                st.session_state.vector_store.add_chunks(chunks, metadata={"source": uploaded_file.name})
                st.success(f"📄 Indexed {len(chunks)} chunks.")
        except PDFValidationError as e:
            st.error(f"Invalid PDF: {e}")
            st.session_state.pdf_uploaded = False
    
    # Class selection
    class_level = st.selectbox("🎓 Class", settings.ALLOWED_CLASSES, index=4)
    
    # Language selection
    language = st.selectbox("🗣️ Language", list(settings.LANGUAGES.keys()))
    st.session_state.language = settings.LANGUAGES[language]
    
    # Voice gender
    gender = st.radio("🎙️ Voice", ["female", "male"], horizontal=True)
    st.session_state.gender = gender
    
    # Mode selection
    mode = st.radio("🛠️ Mode", ["Teach", "Quiz", "Doubt Chat"], horizontal=True)
    st.session_state.mode = mode
    
    # Budget indicator
    st.markdown("---")
    if not API_KEY_MISSING:
        cost = st.session_state.usage.calculate_cost()
        st.metric("💰 Estimated Cost", f"₹{cost:.2f}")
        if st.session_state.usage.budget_warning():
            st.warning("⚠️ Approaching budget limit")
        if st.session_state.usage.budget_exceeded():
            st.error("🚫 Budget exceeded. Please contact admin.")
            st.stop()
    else:
        st.metric("💰 Estimated Cost", "N/A (no API key)")
    
    # Competitive mode toggle
    competitive = st.checkbox("🚀 Competitive Mode (allow beyond PDF)")

# ------------------------------------------------------------
# Main Area (rest unchanged)
# ------------------------------------------------------------
st.markdown('<h1 class="main-title">🧑‍🏫 AIM9tutor</h1>', unsafe_allow_html=True)

if not st.session_state.pdf_uploaded:
    st.info("📤 Please upload a PDF to begin.")
    st.stop()

if API_KEY_MISSING:
    st.error("🚫 Google API Key is required to use Teach, Quiz, or Chat modes. Please add your key to `.env` and restart.")
    st.stop()

# Now we know API key exists, ensure engines are initialized
if st.session_state.chat_engine is None:
    st.error("Chat engine failed to initialize. Check your API key and internet connection.")
    st.stop()

# Set up chat engine system prompt
st.session_state.chat_engine.set_system_prompt(
    class_level=class_level,
    language=st.session_state.language,
    competitive_mode=competitive
)

# Initialize teach/quiz engines if not already
if st.session_state.teach_engine is None:
    st.session_state.teach_engine = TeachEngine(st.session_state.chat_engine, st.session_state.vector_store)
if st.session_state.quiz_engine is None:
    st.session_state.quiz_engine = QuizEngine(st.session_state.chat_engine, st.session_state.vector_store)

# ------------------------------------------------------------
# Mode Routing (Teach, Quiz, Doubt Chat) – no changes needed
# ------------------------------------------------------------
if st.session_state.mode == "Teach":
    st.markdown('<div class="section-header">📖 Teach Mode</div>', unsafe_allow_html=True)
    
    if not st.session_state.teach_engine.sections:
        with st.spinner("Preparing lessons..."):
            full_context = st.session_state.vector_store.retrieve_context("overview of chapter", n_results=10)
            full_text = "\n".join(full_context)
            st.session_state.teach_engine.generate_sections(full_text)
    
    current = st.session_state.teach_engine.get_current_section()
    if current:
        with st.container():
            st.markdown(f'<div class="card"><h3>📌 {current["title"]}</h3>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("📘 Teach This Section", use_container_width=True):
                    with st.spinner("Teaching..."):
                        teaching = st.session_state.teach_engine.teach_section(current['title'])
                        st.markdown(teaching)
                        
                        if st.session_state.voice_engine:
                            try:
                                audio_path, chars = st.session_state.voice_engine.synthesize(
                                    teaching,
                                    language=st.session_state.language,
                                    gender=st.session_state.gender,
                                    class_level=class_level
                                )
                                st.session_state.usage.add_tts_usage(chars)
                                st.audio(str(audio_path))
                            except Exception as e:
                                st.warning(f"Voice playback failed: {e}")
                        else:
                            st.info("🔇 Voice disabled (configure API key for TTS)")
            
            with col2:
                if st.button("⏩ Next Section", use_container_width=True):
                    st.session_state.teach_engine.next_section()
                    st.rerun()
            
            with col3:
                if st.button("🔄 Give Recap", use_container_width=True):
                    recap = st.session_state.teach_engine.generate_recap()
                    st.info(recap)
                    if st.session_state.voice_engine:
                        try:
                            audio_path, chars = st.session_state.voice_engine.synthesize(
                                recap,
                                language=st.session_state.language,
                                gender=st.session_state.gender,
                                class_level=class_level
                            )
                            st.session_state.usage.add_tts_usage(chars)
                            st.audio(str(audio_path))
                        except Exception as e:
                            st.warning(f"Voice playback failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("🎉 You've completed all sections!")
        if st.button("Restart Teaching"):
            st.session_state.teach_engine.current_section_index = 0
            st.rerun()

elif st.session_state.mode == "Quiz":
    st.markdown('<div class="section-header">📝 Quiz Mode</div>', unsafe_allow_html=True)
    
    if not st.session_state.quiz_engine.questions:
        if st.button("🎲 Generate Quiz", use_container_width=True):
            with st.spinner("Creating questions..."):
                st.session_state.quiz_engine.generate_questions()
            st.rerun()
    else:
        q = st.session_state.quiz_engine.get_current_question()
        if q:
            with st.container():
                st.markdown(f'<div class="card"><h4>❓ Question {st.session_state.quiz_engine.current_index + 1}/{len(st.session_state.quiz_engine.questions)}</h4>', unsafe_allow_html=True)
                st.write(q['question'])
                options = q['options']
                choice = st.radio("Choose your answer:", options, key=f"q_{st.session_state.quiz_engine.current_index}", label_visibility="collapsed")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Submit Answer", use_container_width=True):
                        is_correct, explanation = st.session_state.quiz_engine.check_answer(choice)
                        if is_correct:
                            st.balloons()
                            st.success("✅ Correct!")
                            st.session_state.quiz_engine.score += 1
                        else:
                            st.error(f"❌ Not quite. {explanation}")
                            if st.button("📚 Teach Me This", key="reteach"):
                                context = st.session_state.vector_store.retrieve_context(q['question'], n_results=2)
                                re_teach, _, _ = st.session_state.chat_engine.send_message(
                                    f"Explain the concept behind this question: {q['question']}",
                                    context_chunks=context
                                )
                                st.markdown(re_teach)
                                if st.session_state.voice_engine:
                                    try:
                                        audio_path, chars = st.session_state.voice_engine.synthesize(
                                            re_teach,
                                            language=st.session_state.language,
                                            gender=st.session_state.gender,
                                            class_level=class_level
                                        )
                                        st.session_state.usage.add_tts_usage(chars)
                                        st.audio(str(audio_path))
                                    except Exception as e:
                                        st.warning(f"Voice playback failed: {e}")
                        
                        st.session_state.quiz_engine.record_quiz_result(is_correct)
                
                with col2:
                    if st.button("⏩ Next Question", use_container_width=True):
                        st.session_state.quiz_engine.next_question()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success(f"🎉 Quiz completed! Your score: **{st.session_state.quiz_engine.score}/{len(st.session_state.quiz_engine.questions)}**")
            if st.button("🔄 Restart Quiz", use_container_width=True):
                st.session_state.quiz_engine = QuizEngine(st.session_state.chat_engine, st.session_state.vector_store)
                st.rerun()

elif st.session_state.mode == "Doubt Chat":
    st.markdown('<div class="section-header">💬 Doubt Chat</div>', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history in cards
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio" in msg and msg["audio"]:
                st.audio(msg["audio"])
    
    # Chat input
    if prompt := st.chat_input("Ask your doubt..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        context = st.session_state.vector_store.retrieve_context(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, input_tokens, output_tokens = st.session_state.chat_engine.send_message(
                    prompt, context_chunks=context
                )
                st.session_state.usage.add_gemini_usage(input_tokens, output_tokens)
                st.markdown(response)
                
                audio_path = None
                if st.session_state.voice_engine:
                    try:
                        audio_path, chars = st.session_state.voice_engine.synthesize(
                            response,
                            language=st.session_state.language,
                            gender=st.session_state.gender,
                            class_level=class_level
                        )
                        st.session_state.usage.add_tts_usage(chars)
                        st.audio(str(audio_path))
                    except Exception as e:
                        st.warning(f"Voice playback failed: {e}")
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "audio": str(audio_path) if audio_path else None
        })