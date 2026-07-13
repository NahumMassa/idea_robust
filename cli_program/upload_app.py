"""
Setlist Upload App
A local Streamlit page for uploading setlist data to the DB.
Run with: streamlit run cli_program/upload_app.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# ── path setup ────────────────────────────────────────────────────────────────
# Add project root so `models` is importable, and cli_program for format helpers
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "cli_program"))

from format_setlist import get_data_from_text, get_timestamp_for_Sunday
from upload import upload_data_to_db

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Setlist Upload",
    page_icon="🎵",
    layout="centered",
)

# ── styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* page background */
.stApp { background: #0f1117; }

/* title area */
h1 { 
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.2rem !important;
}

/* cards */
.upload-card {
    background: #1a1d2e;
    border: 1px solid #2d2f45;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
}

/* section labels */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 0.4rem;
}

/* preview table rows */
.preview-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #2d2f45;
    font-size: 0.9rem;
}
.preview-row:last-child { border-bottom: none; }
.tag-song  { color: #a78bfa; font-weight: 600; flex: 2; }
.tag-artist{ color: #60a5fa; flex: 2; }
.tag-link  { color: #34d399; font-size: 0.78rem; flex: 3;
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* upload button */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 2rem;
    width: 100%;
    font-size: 1rem;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] > button:hover { opacity: 0.88; }

/* success / error callout */
.msg-success {
    background: #052e16; border: 1px solid #16a34a;
    border-radius: 8px; padding: 1rem 1.2rem; color: #4ade80;
    font-weight: 500; margin-top: 1rem;
}
.msg-error {
    background: #2d0a0a; border: 1px solid #dc2626;
    border-radius: 8px; padding: 1rem 1.2rem; color: #f87171;
    font-weight: 500; margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

BLUEPRINT = """\
Song title 1
Song title 2
Song title 3
---
Artist 1
Artist 2
Artist 3
---
https://youtu.be/...
https://youtu.be/...
https://youtu.be/...
"""

def next_sunday() -> datetime:
    today = datetime.now()
    days_ahead = 6 - today.weekday()  # 6 = Sunday
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🎵 Setlist Upload")
st.caption("Paste your setlist below, preview it, and push it to the database.")

st.markdown("---")

# ── Input ─────────────────────────────────────────────────────────────────────
col_text, col_date = st.columns([3, 1], gap="large")

with col_text:
    st.markdown('<p class="section-label">Setlist text</p>', unsafe_allow_html=True)
    raw_text = st.text_area(
        label="setlist_input",
        label_visibility="collapsed",
        placeholder=BLUEPRINT,
        height=260,
        key="setlist_text",
    )

with col_date:
    st.markdown('<p class="section-label">Performance date</p>', unsafe_allow_html=True)
    perf_date = st.date_input(
        label="perf_date",
        label_visibility="collapsed",
        value=next_sunday(),
        key="perf_date",
    )

# ── Preview ───────────────────────────────────────────────────────────────────
titles, artists, links = [], [], []

if raw_text.strip():
    titles, artists, links = get_data_from_text(raw_text)

    if titles:
        st.markdown("---")
        st.markdown('<p class="section-label">Preview</p>', unsafe_allow_html=True)
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)

        header = '<div class="preview-row"><span class="tag-song">Song</span><span class="tag-artist">Artist</span><span class="tag-link">Link</span></div>'
        st.markdown(header, unsafe_allow_html=True)

        for song, artist, link in zip(titles, artists, links):
            row = (
                f'<div class="preview-row">'
                f'<span class="tag-song">{song}</span>'
                f'<span class="tag-artist">{artist}</span>'
                f'<span class="tag-link">{link}</span>'
                f'</div>'
            )
            st.markdown(row, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # count validation
        if not (len(titles) == len(artists) == len(links)):
            st.warning(
                f"⚠️  Mismatched counts — Songs: {len(titles)}, "
                f"Artists: {len(artists)}, Links: {len(links)}. "
                "Make sure each section has the same number of lines."
            )
    else:
        st.info("Start typing your setlist above to see a preview.")

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown("---")

upload_ready = bool(titles) and len(titles) == len(artists) == len(links)

if st.button("⬆️  Upload to database", disabled=not upload_ready, key="upload_btn"):
    date_str = perf_date.strftime("%Y-%m-%d")
    with st.spinner(f"Uploading {len(titles)} songs for {date_str}…"):
        try:
            upload_data_to_db((titles, artists, links), date_str)
            st.markdown(
                f'<div class="msg-success">✅ Successfully uploaded <strong>{len(titles)} songs</strong> '
                f'for <strong>{date_str}</strong>.</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.markdown(
                f'<div class="msg-error">❌ Upload failed: {e}</div>',
                unsafe_allow_html=True,
            )
elif not upload_ready and raw_text.strip():
    st.caption("Fix the mismatched counts above before uploading.")

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Idea Robust · Setlist Uploader · runs on localhost")
