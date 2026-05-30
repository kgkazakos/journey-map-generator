"""
Streamlit UI for journey-map-generator — CPR Orbital Tool #38
"""
import json
import os

import streamlit as st

# Page config
st.set_page_config(
    page_title="Journey Map Generator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# DM Mono + DM Sans fonts (consistent with CPR series)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
code, pre, .stCode {
    font-family: 'DM Mono', monospace !important;
}
h1, h2, h3 {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
}

/* Emotion arc */
.emotion-bar-positive { background: #0f6e56; border-radius: 4px; height: 12px; }
.emotion-bar-negative { background: #d85a30; border-radius: 4px; height: 12px; }
.emotion-bar-neutral  { background: #aaa; border-radius: 4px; height: 12px; }

/* Phase card */
.phase-card {
    border-left: 3px solid #854f0b;
    padding: 12px 16px;
    border-radius: 6px;
    background: #fafafa;
    margin-bottom: 10px;
}

/* Pain badges */
.badge-critical { background: #faeeda; color: #854f0b; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-family: 'DM Mono', monospace; }
.badge-moderate { background: #e6f1fb; color: #185fa5; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-family: 'DM Mono', monospace; }
.badge-minor    { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-family: 'DM Mono', monospace; }

.stButton > button {
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


SAMPLE_DATA = """## Phase: Awareness
- User first heard about the product through a colleague's recommendation.
- They searched for alternatives and compared pricing before deciding.
- The landing page was confusing — couldn't figure out what the product actually did.

## Phase: Onboarding
- Signing up was quick but email verification failed twice before working.
- The setup wizard felt overwhelming — too many options at once.
- User couldn't find how to import existing data and spent 20 minutes looking.

## Phase: Core Use
- Daily use is mostly smooth, but search is frustratingly slow with large datasets.
- Collaborative features are consistently loved and rated highest in user interviews.
- Export doesn't support their company's file format — a critical blocker for some teams.
- Notifications are confusing — users can't tell which ones are important vs noise.

## Phase: Problem
- Error messages show only codes, not explanations. Users feel completely lost.
- Support chat averages a 4-hour response time — unacceptable for production issues.

## Phase: Resolution
- Most users find workarounds eventually but feel annoyed the product doesn't handle it natively.
- Long-term users are satisfied overall but always mention onboarding as a rough start.
"""


def _emotion_color(score: float) -> str:
    if score > 0.3:
        return "#0f6e56"
    if score > -0.2:
        return "#854f0b"
    return "#d85a30"


def _emotion_emoji(emotion: str) -> str:
    mapping = {
        "delighted": "😄",
        "satisfied": "😊",
        "hopeful": "🤞",
        "neutral": "😐",
        "anxious": "😰",
        "confused": "😕",
        "overwhelmed": "😩",
        "frustrated": "😤",
    }
    return mapping.get(emotion, "😐")


def _severity_badge(sev: str) -> str:
    cls = f"badge-{sev}"
    return f'<span class="{cls}">{sev.upper()}</span>'


def render_emotion_arc(phases):
    """Render emotion arc as a horizontal timeline."""
    steps = []
    for ph in phases:
        for st in ph.get("steps", []):
            steps.append({
                "label": f"{ph['name'][:15]}",
                "step": st.get("name", "")[:20],
                "score": st.get("emotion_score", 0),
                "emotion": st.get("emotion", "neutral"),
            })

    if not steps:
        return

    st_cols = st.columns(len(steps))
    for i, (col, step_data) in enumerate(zip(st_cols, steps)):
        score = step_data["score"]
        color = _emotion_color(score)
        emoji = _emotion_emoji(step_data["emotion"])
        bar_height = int(abs(score) * 60) + 10
        direction = "↑" if score >= 0 else "↓"

        col.markdown(
            f"""<div style="text-align:center;">
            <div style="font-size:20px;">{emoji}</div>
            <div style="width:6px;height:{bar_height}px;background:{color};margin:4px auto;border-radius:3px;"></div>
            <div style="font-size:9px;color:#888;line-height:1.3;">{step_data['label']}</div>
            <div style="font-size:9px;color:#555;font-family:'DM Mono',monospace;">{score:+.1f}</div>
            </div>""",
            unsafe_allow_html=True,
        )


# -------------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🗺️ Journey Map Generator")
    st.caption("CPR Orbital Tool #38 · S6 Pre-study & impact")
    st.divider()

    persona_name = st.text_input("Persona name", value="Primary User")
    persona_role = st.text_input("Persona role", value="", placeholder="e.g. Senior Product Manager")
    map_title = st.text_input("Journey map title", value="", placeholder="Auto-generated if blank")

    st.divider()
    st.markdown("**LLM Enrichment**")
    llm_backend = st.selectbox(
        "Backend",
        options=["claude", "gemini", "openai", "none (rule-based only)"],
        index=0,
        help="claude = Claude Opus 4, gemini = Gemini 3.1 Pro, openai = GPT-5.5",
    )

    api_key_hint = {
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "none (rule-based only)": None,
    }
    key_name = api_key_hint.get(llm_backend)
    if key_name:
        api_key = st.text_input(f"{key_name}", type="password", placeholder="sk-...")
        if api_key:
            os.environ[key_name] = api_key
    else:
        api_key = None

    st.divider()
    st.markdown("**Export**")
    export_format = st.radio("Format", ["Markdown", "JSON", "CSV"], horizontal=True)
    st.divider()
    st.caption("github.com/kgkazakos/journey-map-generator")


# -------------------------------------------------------------------------
# Main content
# -------------------------------------------------------------------------

st.title("🗺️ Journey Map Generator")
st.caption("Scaffold journey maps with phases, pain points, and emotional arcs from coded research data.")

tab_input, tab_map, tab_arc, tab_export = st.tabs([
    "📥 Research Data", "📋 Journey Map", "📈 Emotion Arc", "📤 Export"
])

with tab_input:
    st.markdown("**Paste your coded research data below.** Use `## Phase: Name` headings to separate phases, and `-` bullet points for observations.")
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_data = st.text_area(
            "Research data",
            value=SAMPLE_DATA,
            height=400,
            label_visibility="collapsed",
        )
    with col2:
        st.markdown("**Format guide**")
        st.code("""## Phase: Awareness
- User found product via LinkedIn.
- Landing page was confusing.

## Phase: Onboarding
- Sign-up was quick but confusing.
- Import didn't work — 20 min lost.

## Phase: Core Use
- Search is frustratingly slow.
- Collaboration features are loved.
""", language="markdown")

    generate_btn = st.button("🗺️ Generate Journey Map", type="primary", use_container_width=True)


# -------------------------------------------------------------------------
# Generation logic
# -------------------------------------------------------------------------

if generate_btn:
    if not raw_data.strip():
        st.error("Please paste some research data first.")
        st.stop()

    with st.spinner("Scaffolding journey map…"):
        try:
            from journey_map_generator import scaffold_journey_map
            from journey_map_generator.export import to_json, to_markdown, to_csv

            journey = scaffold_journey_map(
                raw_data=raw_data,
                persona_name=persona_name or "Primary User",
                persona_role=persona_role or None,
                title=map_title or None,
            )

            backend_clean = llm_backend.split(" ")[0]
            if backend_clean != "none" and (api_key or os.environ.get(api_key_hint.get(backend_clean, ""), "")):
                try:
                    from journey_map_generator.llm import enrich_journey_map
                    with st.spinner(f"Enriching with {backend_clean}…"):
                        journey = enrich_journey_map(journey, raw_data, backend=backend_clean)
                    st.toast(f"✅ LLM enrichment complete ({backend_clean})", icon="🤖")
                except Exception as e:
                    st.warning(f"LLM enrichment failed: {e}. Showing rule-based output.")
            elif backend_clean != "none":
                st.info("No API key provided — showing rule-based output. Enter key in sidebar to enable LLM enrichment.")

            st.session_state["journey"] = journey
            st.session_state["journey_json"] = to_json(journey)
            st.session_state["journey_md"] = to_markdown(journey)
            st.session_state["journey_csv"] = to_csv(journey)
            st.success("✅ Journey map generated!")

        except Exception as e:
            st.error(f"Error generating journey map: {e}")
            st.exception(e)
            st.stop()


# -------------------------------------------------------------------------
# Display results
# -------------------------------------------------------------------------

journey_data = st.session_state.get("journey")

with tab_map:
    if not journey_data:
        st.info("Generate a journey map using the Research Data tab.")
    else:
        j = journey_data
        # Header
        st.markdown(f"## {j.title}")
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("Persona", j.persona.name)
        with meta_col2:
            total_steps = sum(len(ph.steps) for ph in j.phases)
            st.metric("Total Steps", total_steps)
        with meta_col3:
            total_pps = len(j.all_pain_points())
            st.metric("Pain Points", total_pps)

        if j.summary:
            st.divider()
            st.markdown("**Journey Summary**")
            st.markdown(j.summary)

        if j.key_insights:
            st.divider()
            st.markdown("**Key Insights**")
            for i, ins in enumerate(j.key_insights, 1):
                st.markdown(f"{i}. {ins}")

        if j.critical_moments:
            st.divider()
            st.markdown("**⚡ Moments of Truth**")
            for m in j.critical_moments:
                st.markdown(f"- {m}")

        st.divider()
        st.markdown("**Journey Phases**")

        for ph in j.phases:
            sentiment = ph.overall_sentiment
            sentiment_icon = "🟢" if sentiment > 0.2 else "🟡" if sentiment > -0.2 else "🔴"

            with st.expander(f"{sentiment_icon} **{ph.name}** — sentiment {sentiment:+.2f}", expanded=True):
                st.caption(ph.description)

                if ph.steps:
                    for st_data in ph.steps:
                        emo_color = _emotion_color(st_data.emotion_score)
                        emoji = _emotion_emoji(st_data.emotion.value if hasattr(st_data.emotion, 'value') else str(st_data.emotion))

                        st.markdown(
                            f"<div style='border-left:3px solid {emo_color};padding:8px 12px;margin:6px 0;border-radius:4px;background:#fafafa'>"
                            f"<b>{emoji} {st_data.name[:80]}</b><br>"
                            f"<span style='font-size:12px;color:#888;font-family:DM Mono,monospace;'>"
                            f"{st_data.emotion.value if hasattr(st_data.emotion,'value') else st_data.emotion} "
                            f"· score {st_data.emotion_score:+.2f} · effort {st_data.effort.value if hasattr(st_data.effort,'value') else st_data.effort}"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )

                        if st_data.pain_points:
                            for pp in st_data.pain_points:
                                sev = pp.severity.value if hasattr(pp.severity, 'value') else pp.severity
                                badge = _severity_badge(sev)
                                st.markdown(
                                    f"&nbsp;&nbsp;{badge} {pp.description[:120]}",
                                    unsafe_allow_html=True,
                                )

                        if st_data.opportunities:
                            for opp in st_data.opportunities:
                                st.markdown(f"&nbsp;&nbsp;💡 {opp.description[:120]}")

        if j.source_data_summary:
            st.caption(j.source_data_summary)
        if j.llm_backend:
            st.caption(f"LLM enrichment: {j.llm_backend}")


with tab_arc:
    if not journey_data:
        st.info("Generate a journey map first.")
    else:
        j = journey_data
        st.markdown("### Emotional Arc")
        st.caption("How the user's emotional state evolves through the journey.")

        arc = j.emotion_arc()
        if arc:
            # Bar chart using native streamlit
            import pandas as pd

            arc_data = []
            for label, score in arc:
                arc_data.append({"Moment": label, "Emotion Score": score})

            df = pd.DataFrame(arc_data)
            st.bar_chart(df.set_index("Moment"), color="#854f0b")

            st.divider()
            st.markdown("**Step-by-step breakdown**")
            for label, score in arc:
                color = _emotion_color(score)
                bar_w = int(abs(score) * 100)
                direction = "positive" if score >= 0 else "negative"
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;margin:3px 0;'>"
                    f"<span style='font-size:12px;width:300px;font-family:DM Mono,monospace;color:#555;'>{label[:50]}</span>"
                    f"<div style='width:{bar_w}px;height:10px;background:{color};border-radius:3px;'></div>"
                    f"<span style='font-size:11px;color:#888;font-family:DM Mono,monospace;'>{score:+.2f}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Phase sentiment summary
        st.divider()
        st.markdown("**Phase Sentiments**")
        for ph in j.phases:
            sentiment = ph.overall_sentiment
            color = _emotion_color(sentiment)
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;margin:4px 0;'>"
                f"<span style='font-weight:500;width:180px;'>{ph.name}</span>"
                f"<div style='width:{int(abs(sentiment)*120)+5}px;height:14px;background:{color};border-radius:4px;'></div>"
                f"<span style='font-size:12px;color:#888;font-family:DM Mono,monospace;'>{sentiment:+.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


with tab_export:
    if not journey_data:
        st.info("Generate a journey map first.")
    else:
        fmt = export_format

        if fmt == "Markdown":
            st.code(st.session_state.get("journey_md", ""), language="markdown")
            st.download_button(
                "⬇️ Download Markdown",
                data=st.session_state.get("journey_md", ""),
                file_name="journey-map.md",
                mime="text/markdown",
            )
        elif fmt == "JSON":
            st.code(st.session_state.get("journey_json", ""), language="json")
            st.download_button(
                "⬇️ Download JSON",
                data=st.session_state.get("journey_json", ""),
                file_name="journey-map.json",
                mime="application/json",
            )
        elif fmt == "CSV":
            st.code(st.session_state.get("journey_csv", ""))
            st.download_button(
                "⬇️ Download CSV",
                data=st.session_state.get("journey_csv", ""),
                file_name="journey-map.csv",
                mime="text/csv",
            )
