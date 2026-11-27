"""verdanti.ai, web app entry point.

Run:  streamlit run app.py
Config (env vars, .env file, or Streamlit secrets):
  OPENAI_API_KEY   required for AI design
  APP_PASSCODE     access code people must enter before AI designs run (protects your API budget)
  SUPABASE_URL / SUPABASE_KEY   optional: store saved projects in Supabase (otherwise ./storage)
"""
import os
import streamlit as st

st.set_page_config(page_title="verdanti.ai | Smarter landscapes. Less water.", page_icon=next((str(p) for p in __import__("pathlib").Path(__file__).parent.joinpath("data").glob("icon.png")), "🌱"), layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
for k in ("OPENAI_API_KEY", "APP_PASSCODE", "OPENAI_TEXT_MODEL", "OPENAI_IMAGE_MODEL",
          "SESSION_DESIGN_LIMIT", "DAILY_DESIGN_LIMIT", "SUPABASE_URL", "SUPABASE_KEY", "STORE_DIR"):
    try:
        if k in st.secrets and not os.getenv(k):
            os.environ[k] = str(st.secrets[k])
    except Exception:
        pass
if os.getenv("FAKE_OPENAI"):          # developer mode: canned AI responses, no API cost
    os.environ.setdefault("OPENAI_API_KEY", "fake")
    import tests.fake_openai  # noqa: F401
try:
    from pillow_heif import register_heif_opener   # iPhone HEIC photos
    register_heif_opener()
except ImportError:
    pass

from ui import theme, state, home, studio, pages_misc

APP_NAME = "verdanti.ai"

state.init()
theme.inject()

# ── top navigation ──
page = st.session_state["page"]
if page != "studio":
    st.markdown(f"<style>.st-key-nav_{page} button {{ color: {theme.FOREST} !important; "
                f"border-bottom: 2px solid {theme.CLAY} !important; font-weight: 600 !important; }}</style>",
                unsafe_allow_html=True)
with st.container(key="nav"):
    left, right = st.columns([2.6, len(state.PAGES) + 1], vertical_alignment="center")
    left.markdown(theme.brand(), unsafe_allow_html=True)
    with right.container(key="navlinks"):        # its own row, so phones can swipe it sideways
        cols = st.columns(len(state.PAGES), vertical_alignment="center")
        for col, (pid, label) in zip(cols, state.PAGES.items()):
            with col.container(key=f"nav_{pid}"):
                st.button(label, type="tertiary", on_click=state.go, args=(pid,), use_container_width=True)

if page != "studio" and (st.session_state.get("_bg_ready") or any(a.get("job_id") for a in st.session_state["areas"])):
    studio.background_notice()

{"home": home.render, "studio": studio.render, "plan": pages_misc.plan,
 "plants": pages_misc.plants, "saved": pages_misc.saved, "privacy": pages_misc.privacy}.get(page, home.render)()

state.autosave()      # every change is saved to the backend (engine/store.py)

# ── go to the top of the page when switching pages ──
if st.session_state.get("_last_page") != page:
    st.session_state["_last_page"] = page
    st.session_state["_nav_n"] = st.session_state.get("_nav_n", 0) + 1
    import streamlit.components.v1 as components
    components.html(f"""<script>// page change {st.session_state["_nav_n"]}
const d = window.parent.document;
const top = () => {{
  const nav = d.querySelector('.st-key-nav');
  if (nav) nav.scrollIntoView({{block: 'start'}});
  d.querySelectorAll('*').forEach(el => {{ if (el.scrollTop > 0) el.scrollTop = 0; }});
  window.parent.scrollTo(0, 0);
}};
[0, 150, 500, 1000].forEach(ms => setTimeout(top, ms));
</script>""", height=0)
