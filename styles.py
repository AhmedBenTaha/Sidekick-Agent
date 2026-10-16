"""Look and feel for the Sidekick app.
Gradio 6 passes theme, css and js to launch(), not gr.Blocks().
"""

import gradio as gr

# ==========================================
# DESIGN SYSTEM & CONSTANTS
# ==========================================

# Premium SaaS Color Palette
NAVY = "#0F172A"       # Deep slate for primary text and deep accents
BLUE = "#3B82F6"       # Vibrant primary blue
GOLD = "#F59E0B"       # Rich amber/gold for approvals and completions
PURPLE = "#8B5CF6"     # Modern violet for in-progress states
GRAY = "#64748B"       # Slate 500 for secondary text
BACKGROUND = "#F8FAFC" # Slate 50 for a soft, clean app background
SURFACE = "#FFFFFF"    # Pure white for cards
BORDER = "#E2E8F0"     # Slate 200 for subtle borders

# ==========================================
# THEME CONFIGURATION
# ==========================================

THEME = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50="#EFF6FF",
        c100="#DBEAFE",
        c200="#BFDBFE",
        c300="#93C5FD",
        c400="#60A5FA",
        c500="#3B82F6",
        c600="#2563EB",
        c700="#1D4ED8",
        c800="#1E40AF",
        c900="#1E3A8A",
        c950="#172554",
    ),
    neutral_hue=gr.themes.Color(
        c50="#F8FAFC",
        c100="#F1F5F9",
        c200="#E2E8F0",
        c300="#CBD5E1",
        c400="#94A3B8",
        c500="#64748B",
        c600="#475569",
        c700="#334155",
        c800="#1E293B",
        c900="#0F172A",
        c950="#020617",
    ),
    font=[
        gr.themes.GoogleFont("Inter"),
        "ui-sans-serif",
        "system-ui",
        "sans-serif",
    ],
    font_mono=["JetBrains Mono", "ui-monospace", "monospace"],
)

# ==========================================
# STYLESHEETS
# ==========================================

CSS = """
/* --- GLOBAL & CONTAINER --- */
.gradio-container {
    background: #F8FAFC !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 24px !important;
}

/* --- HEADER --- */
#header {
    padding: 8px 4px 24px;
    margin-bottom: 8px;
}

#header .context-label {
    color: #64748B;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 4px;
}

#header h1 {
    font-family: 'Sora', 'Inter', sans-serif;
    color: #0F172A;
    font-weight: 700;
    font-size: 32px;
    line-height: 1.2;
    margin: 0 0 12px;
    letter-spacing: -0.02em;
}

#header .brand-bar {
    height: 4px;
    width: 120px;
    border-radius: 4px;
    background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #F59E0B 100%);
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

/* --- PANELS & CARDS --- */
#chat, #plan-panel, #ask-panel {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

#chat:hover, #plan-panel:hover, #ask-panel:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
}

/* --- CHAT INTERFACE --- */
#chat {
    min-height: 400px;
}

#chat .message, #chat .wrapper {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #0F172A;
    line-height: 1.6;
}

#chat .user .message, #chat .user .wrapper {
    background: #EFF6FF !important;
    border: 1px solid #DBEAFE !important;
    color: #1E3A8A !important;
}

#chat .bot .message, #chat .bot .wrapper {
    background: #F8FAFC !important;
    border: 1px solid #F1F5F9 !important;
}

/* --- PLAN PANEL --- */
#plan-panel {
    padding: 20px 24px;
}

#plan-panel h3 {
    font-family: 'Inter', sans-serif;
    color: #3B82F6;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

#plan-panel h3::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    background: #3B82F6;
    border-radius: 50%;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

#plan-panel .placeholder {
    color: #94A3B8;
    font-size: 13px;
    font-style: italic;
}

#plan-panel ul {
    list-style: none;
    padding: 0;
    margin: 0;
    position: relative;
}

#plan-panel li {
    font-family: 'Inter', sans-serif;
    color: #0F172A;
    font-size: 14px;
    line-height: 1.5;
    margin: 0;
    padding: 12px 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    border-bottom: 1px solid #F1F5F9;
    transition: background 0.2s ease;
}

#plan-panel li:last-child {
    border-bottom: none;
}

#plan-panel li:hover {
    background: #F8FAFC;
    margin: 0 -12px;
    padding: 12px;
    border-radius: 8px;
}

#plan-panel .mark {
    flex: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    position: relative;
    top: 2px;
    transition: all 0.3s ease;
}

#plan-panel li.pending .mark {
    border: 2px solid #CBD5E1;
    background: #FFFFFF;
}

#plan-panel li.in_progress .mark {
    border: 2px solid #8B5CF6;
    background: #EDE9FE;
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1);
}

#plan-panel li.in_progress .mark::after {
    content: '';
    position: absolute;
    top: 3px; left: 3px;
    width: 6px; height: 6px;
    background: #8B5CF6;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

#plan-panel li.completed .mark {
    border: 2px solid #F59E0B;
    background: #FEF3C7;
}

#plan-panel li.completed .mark::after {
    content: '✓';
    position: absolute;
    top: -2px; left: 1px;
    font-size: 12px;
    font-weight: 800;
    color: #D97706;
}

#plan-panel li.completed {
    color: #64748B;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}

/* --- INPUT & ASK PANEL --- */
#ask-panel {
    padding: 8px;
}

#ask-panel textarea {
    font-family: 'Inter', sans-serif;
    color: #0F172A;
    font-size: 14px;
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease;
}

#ask-panel textarea:focus {
    background: #FFFFFF !important;
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

#ask-panel textarea::placeholder {
    color: #94A3B8;
}

/* --- BUTTONS --- */
button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button:active {
    transform: translateY(1px) !important;
}

#go-button {
    background: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3), 0 2px 4px -1px rgba(59, 130, 246, 0.2) !important;
}

#go-button:hover {
    background: #2563EB !important;
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3), 0 4px 6px -2px rgba(59, 130, 246, 0.2) !important;
}

#approve-button {
    background: #F59E0B !important;
    color: #0F172A !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3), 0 2px 4px -1px rgba(245, 158, 11, 0.2) !important;
}

#approve-button:hover {
    background: #D97706 !important;
    color: #FFFFFF !important;
    box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.3), 0 4px 6px -2px rgba(245, 158, 11, 0.2) !important;
}

#reset-button {
    background: transparent !important;
    color: #EF4444 !important;
    border: 1.5px solid #FCA5A5 !important;
}

#reset-button:hover {
    background: #FEF2F2 !important;
    border-color: #EF4444 !important;
    color: #DC2626 !important;
}

/* --- SCROLLBARS --- */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
}
"""

# ==========================================
# JAVASCRIPT
# ==========================================

JS = """
<script>
    // Force light mode before the Gradio app mounts.
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.replace(url.href);
    }

    // Inject Google Fonts for Sora and Inter to ensure they load correctly 
    // and complement the Gradio theme configuration.
    const linkSora = document.createElement('link');
    linkSora.href = 'https://fonts.googleapis.com/css2?family=Sora:wght@500;700&display=swap';
    linkSora.rel = 'stylesheet';
    document.head.appendChild(linkSora);
    
    const linkInter = document.createElement('link');
    linkInter.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
    linkInter.rel = 'stylesheet';
    document.head.appendChild(linkInter);
</script>
"""