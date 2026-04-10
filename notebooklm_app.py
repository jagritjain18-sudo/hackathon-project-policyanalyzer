import streamlit as st
import os

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8-sig')
except Exception as e:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

from notebooklm_handler import NotebookLMHandler
from htmlTemplates import css, bot_template, user_template

# Page config
st.set_page_config(page_title="PDF NotebookLM Assistant", page_icon="📚", layout="wide")
st.markdown(css, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📚 PDF NotebookLM")
    st.write("---")
    
    # Initialize session state
    if 'notebook_handler' not in st.session_state:
        try:
            st.session_state.notebook_handler = NotebookLMHandler()
        except ValueError as e:
            st.error(str(e))
            st.stop()
    
    if 'pdf_loaded' not in st.session_state:
        st.session_state.pdf_loaded = False
    
    # File upload
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_pdf_path = f"temp_{uploaded_file.name}"
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text
        with st.spinner("Extracting PDF text..."):
            text = st.session_state.notebook_handler.extract_pdf_text(temp_pdf_path)
            if "Error" not in text:
                st.session_state.pdf_loaded = True
                st.success(f"✅ PDF loaded: {uploaded_file.name}")
                st.info(f"PDF contains approximately {len(text)} characters")
            else:
                st.error(text)
        
        # Clean up temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
    
    st.write("---")
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.notebook_handler.clear_conversation()
            st.session_state.conversation = []
    
    with col2:
        if st.button("🗑️ Reset All", use_container_width=True):
            st.session_state.notebook_handler.reset()
            st.session_state.pdf_loaded = False
            st.session_state.conversation = []

# Main content
if not st.session_state.pdf_loaded:
    st.title("📚 PDF NotebookLM Assistant")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## Welcome! 👋
        
        This is a **NotebookLM-like PDF Assistant** powered by Google Generative AI.
        
        ### Features:
        - 📄 **PDF Upload** - Upload any PDF document
        - 📝 **Summarization** - Get brief or detailed summaries
        - 💬 **Q&A** - Ask questions about your document
        - 🔍 **Topic Extraction** - Discover main topics
        - ⚖️ **Section Comparison** - Compare concepts
        
        ### How to use:
        1. Upload a PDF file using the sidebar
        2. Choose an action below
        3. Get instant AI-powered insights!
        """)
    
    with col2:
        st.info("""
        ### Requirements:
        - ✅ GOOGLE_API_KEY in .env file
        - ✅ PDF file to analyze
        
        Get your free API key at:
        https://makersuite.google.com/app/apikey
        """)

else:
    # Tabs for different actions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["💬 Chat", "📝 Summary", "🔍 Topics", "⚖️ Compare", "📋 History"]
    )
    
    # Initialize conversation in session state
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    # Tab 1: Chat / Q&A
    with tab1:
        st.header("💬 Ask Questions")
        st.write("Ask any question about your PDF document")
        
        # Display conversation
        for message in st.session_state.conversation:
            if message["role"] == "user":
                st.markdown(user_template.replace("{{MSG}}", message["content"]), unsafe_allow_html=True)
            else:
                st.markdown(bot_template.replace("{{MSG}}", message["content"]), unsafe_allow_html=True)
        
        # Input for new question
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            question = st.text_input("Your question:", key="question_input", placeholder="Ask about your document...")
        
        with col2:
            send_button = st.button("Send", use_container_width=True)
        
        if send_button and question:
            with st.spinner("Thinking..."):
                answer = st.session_state.notebook_handler.ask_question(question)
                
                # Add to conversation display
                st.session_state.conversation.append({"role": "user", "content": question})
                st.session_state.conversation.append({"role": "assistant", "content": answer})
            
            st.rerun()
    
    # Tab 2: Summary
    with tab2:
        st.header("📝 PDF Summary")
        
        summary_type = st.radio(
            "Choose summary type:",
            ["Brief (100-150 words)", "Detailed (300-500 words)", "Key Points"],
            horizontal=True
        )
        
        summary_input = {
            "Brief (100-150 words)": "brief",
            "Detailed (300-500 words)": "detailed",
            "Key Points": "key_points"
        }
        
        if st.button("Generate Summary", type="primary", use_container_width=True):
            with st.spinner("Generating summary..."):
                summary = st.session_state.notebook_handler.generate_summary(
                    summary_input[summary_type]
                )
                st.markdown(summary)
                
                # Add download button
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name="pdf_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Tab 3: Topics
    with tab3:
        st.header("🔍 Document Topics")
        st.write("Extract main topics and structure from the document")
        
        if st.button("Extract Topics", type="primary", use_container_width=True):
            with st.spinner("Analyzing document structure..."):
                topics = st.session_state.notebook_handler.extract_topics()
                st.markdown(topics)
                
                st.download_button(
                    label="📥 Download Topics",
                    data=topics,
                    file_name="document_topics.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Tab 4: Compare Sections
    with tab4:
        st.header("⚖️ Compare Concepts")
        st.write("Compare and contrast two concepts or sections from your document")
        
        col1, col2 = st.columns(2)
        with col1:
            concept1 = st.text_input("First concept/section:", placeholder="e.g., Concept A")
        
        with col2:
            concept2 = st.text_input("Second concept/section:", placeholder="e.g., Concept B")
        
        if st.button("Compare", type="primary", use_container_width=True):
            if concept1 and concept2:
                with st.spinner("Comparing..."):
                    comparison = st.session_state.notebook_handler.compare_sections(concept1, concept2)
                    st.markdown(comparison)
                    
                    st.download_button(
                        label="📥 Download Comparison",
                        data=comparison,
                        file_name="concept_comparison.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            else:
                st.warning("Please enter both concepts to compare")
    
    # Tab 5: Conversation History
    with tab5:
        st.header("📋 Conversation History")
        
        if st.session_state.conversation:
            # Display as table
            for i, message in enumerate(st.session_state.conversation):
                with st.expander(f"{message['role'].upper()} - Message {i//2 + 1}", expanded=False):
                    st.write(message['content'])
            
            # Export option
            if st.button("📥 Export Conversation", use_container_width=True):
                export_text = "\n\n".join([
                    f"{msg['role'].upper()}:\n{msg['content']}"
                    for msg in st.session_state.conversation
                ])
                
                st.download_button(
                    label="Download Conversation",
                    data=export_text,
                    file_name="conversation_history.txt",
                    mime="text/plain"
                )
        else:
            st.info("No conversation yet. Start asking questions in the Chat tab!")
