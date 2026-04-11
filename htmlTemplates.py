css = '''
<style>
body, .stApp, .streamlit-expanderHeader {
  background: #0b1220 !important;
  color: #e2e8f0 !important;
  font-family: 'Poppins', sans-serif;
}

#MainMenu, footer, header {
  visibility: hidden;
}

.navbar {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 2rem;
  margin-bottom: 1rem;
  border-radius: 1.5rem;
  backdrop-filter: blur(20px);
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.navbar h1 {
  margin: 0;
  font-size: 1.75rem;
}

.navbar .nav-links {
  display: flex;
  gap: 1rem;
}

.navbar .nav-links a {
  color: #cbd5e1;
  text-decoration: none;
  padding: 0.75rem 1rem;
  border-radius: 999px;
  transition: background 0.2s ease;
}

.navbar .nav-links a:hover {
  background: rgba(99, 102, 241, 0.15);
}

.hero-panel {
  padding: 2rem;
  border-radius: 1.75rem;
  background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.95));
  border: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: 0 18px 80px rgba(15, 23, 42, 0.4);
  margin-bottom: 1.5rem;
}

.hero-panel h2 {
  margin-top: 0;
  font-size: 2.4rem;
  color: #f8fafc;
}

.hero-panel p {
  color: #cbd5e1;
  line-height: 1.75;
}

.top-row {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.upload-panel, .meta-panel, .status-panel, .preview-panel {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 1.5rem;
  box-shadow: 0 14px 50px rgba(0,0,0,0.20);
  padding: 1.5rem;
}

.upload-panel h3,
.meta-panel h3,
.status-panel h3,
.preview-panel h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.status-panel {
  display: grid;
  gap: 0.75rem;
}

.status-card {
  padding: 1rem;
  border-radius: 1.25rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.status-card strong {
  display: block;
  margin-bottom: 0.35rem;
  color: #f8fafc;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 1.5rem;
}

.card {
  padding: 1.5rem;
  border-radius: 1.75rem;
  backdrop-filter: blur(12px);
  background: rgba(255,255,255,0.06);
  box-shadow: 0 16px 60px rgba(0,0,0,0.22);
  transition: transform 0.3s ease, border-color 0.3s ease;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.card:hover {
  transform: translateY(-3px);
}

.card h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
}

.card.covered { border-color: rgba(96, 165, 250, 0.45); }
.card.not-covered { border-color: rgba(248, 113, 113, 0.45); }
.card.benefits { border-color: rgba(74, 222, 128, 0.45); }
.card.scenarios { border-color: rgba(59, 130, 246, 0.45); }

.summary-box {
  padding: 1.5rem;
  border-radius: 1.5rem;
  margin-bottom: 1.5rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(148, 163, 184, 0.10);
}

.summary-box h3 {
  margin-top: 0;
}

.summary-line {
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  margin-bottom: 0.55rem;
  background: rgba(148, 163, 184, 0.08);
}

.highlight-benefits {
  background: rgba(52, 211, 153, 0.16);
  border-left: 4px solid #22c55e;
}

.highlight-missing {
  background: rgba(248, 113, 113, 0.16);
  border-left: 4px solid #ef4444;
}

.highlight-covered {
  background: rgba(59, 130, 246, 0.16);
  border-left: 4px solid #3b82f6;
}

.running-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
  padding: 0.5rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  font-size: 0.95rem;
}

.info-banner {
  padding: 1rem 1.25rem;
  border-radius: 1.25rem;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.12);
  margin-bottom: 1.5rem;
}

.info-banner strong { color: #f8fafc; }

.chat-message {
    padding: 1.5rem; border-radius: 0.7rem; margin-bottom: 1rem; display: flex;
}
.chat-message.user {
    background-color: #16213d;
}
.chat-message.bot {
    background-color: #1f2937;
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-1.png">
    </div>    
    <div class="message">{{MSG}}</div>
</div>'''