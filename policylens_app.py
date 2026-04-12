import streamlit as st
import os
import json
import html

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

from policylens_handler import PolicyLensHandler
from htmlTemplates import css, bot_template, user_template


def highlight_insights(text: str) -> str:
    def safe(s: str) -> str:
        return html.escape(s)

    lines = text.replace('\r\n', '\n').split('\n')
    rendered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            rendered.append('<div class="summary-line">&nbsp;</div>')
            continue

        lower = stripped.lower()
        if 'benefit' in lower or 'advantage' in lower or 'value' in lower:
            cls = 'summary-line highlight-benefits'
        elif 'not covered' in lower or 'missing' in lower or 'lack' in lower or 'exclude' in lower:
            cls = 'summary-line highlight-missing'
        elif 'covered' in lower or 'includes' in lower or 'summary' in lower:
            cls = 'summary-line highlight-covered'
        else:
            cls = 'summary-line'

        content = safe(stripped)
        content = content.replace('Benefits', '<strong>Benefits</strong>')
        content = content.replace('covered', '<strong>covered</strong>')
        content = content.replace('missing', '<strong>missing</strong>')
        rendered.append(f'<div class="{cls}">{content}</div>')
    return '\n'.join(rendered)


def render_snapshot_cards(snapshot_json: dict) -> str:
    covered = html.escape(str(snapshot_json.get('covered', 'No covered topics found.')))
    not_covered = html.escape(str(snapshot_json.get('not_covered', 'No missing areas found.')))
    benefits = html.escape(str(snapshot_json.get('benefits', 'No benefits found.')))
    scenarios = html.escape(str(snapshot_json.get('scenarios', 'No scenarios found.')))

    return f'''
<div class="grid">
  <div class="card covered"><h3>Covered</h3><p>{covered}</p></div>
  <div class="card not-covered"><h3>Not Covered</h3><p>{not_covered}</p></div>
  <div class="card benefits"><h3>Benefits</h3><p>{benefits}</p></div>
  <div class="card scenarios"><h3>Scenarios</h3><p>{scenarios}</p></div>
</div>
'''

# Page config
st.set_page_config(page_title="Policy Lens Assistant", page_icon="📋", layout="wide")
st.markdown(css, unsafe_allow_html=True)

# Initialize session state
if 'notebook_handler' not in st.session_state:
    try:
        st.session_state.notebook_handler = PolicyLensHandler()
    except ValueError as e:
        st.error(str(e))
        st.stop()

if 'pdf_loaded' not in st.session_state:
    st.session_state.pdf_loaded = False
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = ""
if 'pdf_char_count' not in st.session_state:
    st.session_state.pdf_char_count = 0
if 'last_summary' not in st.session_state:
    st.session_state.last_summary = ""
if 'last_snapshot' not in st.session_state:
    st.session_state.last_snapshot = ""
if 'last_snapshot_json' not in st.session_state:
    st.session_state.last_snapshot_json = {}
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

# Main content
st.markdown('''
<div class="navbar">
  <div>
    <h1>Policy Lens Assistant</h1>
    <p class="nav-subtitle">Upload a PDF and get instant structured snapshots, summaries, and AI insight highlighting.</p>
  </div>
  <div class="nav-links">
    <a href="#summary">Summary</a>
    <a href="#snapshot">Snapshot</a>
    <a href="#chat">Chat</a>
  </div>
</div>
''', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('''
    <div class="hero-panel">
      <h2>Upload your PDF</h2>
      <p>Drag and drop or select a PDF to extract policy details, exclusions, benefits, and structured snapshot insights.</p>
    </div>
    ''', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    if uploaded_file is not None:
        temp_pdf_path = f"temp_{uploaded_file.name}"
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Extracting PDF text..."):
            text = st.session_state.notebook_handler.extract_pdf_text(temp_pdf_path)
            if "Error" not in text:
                st.session_state.pdf_loaded = True
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.pdf_char_count = len(text)
                st.success(f"✅ PDF loaded: {uploaded_file.name}")
                st.info(f"PDF contains approximately {len(text)} characters")
            else:
                st.error(text)

        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

with col2:
    st.markdown('''
    <div class="meta-panel">
      <h3>Quick Actions</h3>
      <p>Manage your session and reset content without leaving the page.</p>
    </div>
    ''', unsafe_allow_html=True)
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.notebook_handler.clear_conversation()
        st.session_state.conversation = []
    if st.button("🗑️ Reset All", use_container_width=True):
        st.session_state.notebook_handler.reset()
        st.session_state.pdf_loaded = False
        st.session_state.uploaded_file_name = ""
        st.session_state.pdf_char_count = 0
        st.session_state.last_summary = ""
        st.session_state.last_snapshot = ""
        st.session_state.last_snapshot_json = {}
        st.session_state.conversation = []

    if st.session_state.pdf_loaded:
        st.markdown('''
        <div class="status-panel">
          <div class="status-card"><strong>PDF Loaded</strong>''' + st.session_state.uploaded_file_name + '''</div>
          <div class="status-card"><strong>Characters</strong>''' + str(st.session_state.pdf_char_count) + '''</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="status-panel">
          <div class="status-card"><strong>Ready</strong>Select a PDF to begin analysis.</div>
        </div>
        ''', unsafe_allow_html=True)

if not st.session_state.pdf_loaded:
    st.markdown('''
    <div class="info-banner">
      <strong>No PDF loaded.</strong> Upload a file to analyze policy wording, exclusions, benefits, and scenarios.
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('''
    <div class="grid">
      <div class="card covered"><h3>Covered</h3><p>Snapshot cards will display selected covered policy elements here.</p></div>
      <div class="card not-covered"><h3>Not Covered</h3><p>Missing or excluded benefits will appear here.</p></div>
      <div class="card benefits"><h3>Benefits</h3><p>Key value propositions from the policy will show here.</p></div>
      <div class="card scenarios"><h3>Scenarios</h3><p>Real-world use cases and claim scenarios will appear here.</p></div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('''
    <div class="preview-panel">
      <h3>Why Snapshot?</h3>
      <p>This feature creates a structured JSON view from your PDF, with clear cards for coverage, gaps, benefits and scenarios.</p>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown('''
    <div class="info-banner">
      <strong>Document loaded:</strong> ''' + st.session_state.uploaded_file_name + ''' • ''' + str(st.session_state.pdf_char_count) + ''' characters
    </div>
    ''', unsafe_allow_html=True)

    if st.session_state.last_summary:
        st.markdown('<div class="summary-box"><h3 id="summary">Summary Output</h3>' + highlight_insights(st.session_state.last_summary) + '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="summary-box"><h3 id="summary">Summary Output</h3><p>Generate a summary in the Summary tab to see highlighted AI insights.</p></div>', unsafe_allow_html=True)

    if st.session_state.last_snapshot_json:
        st.markdown('<h3 id="snapshot">Snapshot Cards</h3>' + render_snapshot_cards(st.session_state.last_snapshot_json), unsafe_allow_html=True)
    else:
        st.markdown('<div class="summary-box"><h3 id="snapshot">Snapshot Cards</h3><p>Generate a snapshot in the Snapshot tab to populate the cards.</p></div>', unsafe_allow_html=True)

    if st.session_state.last_snapshot:
        with st.expander("Show raw snapshot response", expanded=False):
            st.code(st.session_state.last_snapshot, language='json')

st.write("---")

# Tabs for different actions
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["💬 Chat", "📝 Summary", "🔍 Topics", "📌 Snapshot", "⚖️ Compare", "📋 History"]
)

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
            st.session_state.last_summary = summary
            st.markdown(highlight_insights(summary), unsafe_allow_html=True)
            
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

# Tab 4: Snapshot
with tab4:
    st.header("📌 Snapshot")
    st.write("Generate a structured JSON snapshot of the PDF content")
    
    if st.button("Generate Snapshot", type="primary", use_container_width=True):
        with st.spinner("Generating snapshot..."):
            snapshot = st.session_state.notebook_handler.generate_snapshot()
            st.session_state.last_snapshot = snapshot
            try:
                snapshot_json = json.loads(snapshot)
                st.session_state.last_snapshot_json = snapshot_json
                st.json(snapshot_json)
            except Exception:
                st.session_state.last_snapshot_json = {}
                st.error("Snapshot could not be parsed as strict JSON. Showing raw response below.")
                st.code(snapshot, language='json')

            with st.expander("Show raw snapshot response", expanded=False):
                st.code(snapshot, language='json')
            
            st.download_button(
                label="📥 Download Snapshot",
                data=snapshot,
                file_name="pdf_snapshot.json",
                mime="application/json",
                use_container_width=True
            )

# Tab 5: Compare Sections
with tab5:
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

# Tab 6: Conversation History
with tab6:
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
