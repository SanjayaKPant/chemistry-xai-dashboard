"""
mmale_components.py — Reusable MMALE UI Components
====================================================
Contains:
  1. render_orientation() — Scientific practice cycle orientation
     shown on student dashboard before starting any agent
  2. render_rupak_multimodal() — Rupak with image upload capability
     (GPT-4o Vision) for MMALE group students
  3. render_group_info() — Group-aware information panel
  4. render_progress_journey() — Visual agent journey tracker
  5. call_agent_vision() — Multimodal API call for Rupak image input

Academic justification for multimodal Rupak:
  The MA vs MMALE distinction requires a genuine, measurable difference
  in the mode of interaction — not merely the number of agents.
  In the MA condition, Rupak receives textual descriptions of molecular
  models. In the MMALE condition, Rupak receives actual images of
  student-drawn models via GPT-4o Vision. This creates a measurable
  difference in representational interaction mode that is theoretically
  grounded in Johnstone's (2000) claim that submicroscopic understanding
  requires constructing and evaluating visual representations, not just
  describing them verbally.
"""

import streamlit as st
import base64
from openai import OpenAI
from config import (
    GROUPS, get_group_config, get_accessible_agents,
    is_multimodal, is_control, t, get_language, UI_STRINGS,
)
from agents import AGENTS, AGENT_SEQUENCE, ALL_SIGNAL_CODES

# ═══════════════════════════════════════════════════════════════════════════════
# 1. SCIENTIFIC PRACTICE ORIENTATION (for student dashboard)
# ═══════════════════════════════════════════════════════════════════════════════

PRACTICE_DESCRIPTIONS = {
    "SAATHI": {
        "what":  "Surface what you already know — and what you think you know but don't.",
        "why":   "Good science starts with honest assessment of your current understanding.",
        "icon":  "🔬",
        "step":  "Step 1",
    },
    "KHOJI": {
        "what":  "Form a precise scientific question and a testable hypothesis.",
        "why":   "Scientists don't just answer questions — they ask the right ones first.",
        "icon":  "🔭",
        "step":  "Step 2",
    },
    "PRAMAN": {
        "what":  "Evaluate what evidence supports your hypothesis.",
        "why":   "Science distinguishes opinion from evidence-based claims.",
        "icon":  "🧪",
        "step":  "Step 3",
    },
    "TARKA": {
        "what":  "Build a complete argument: Claim → Evidence → Reasoning → Rebuttal.",
        "why":   "Scientific knowledge must be justified, not just asserted.",
        "icon":  "⚖️",
        "step":  "Step 4",
    },
    "RUPAK": {
        "what":  "Represent the phenomenon at three levels: observable, molecular, symbolic.",
        "why":   "Chemistry understanding requires moving between what you see, what atoms do, "
                 "and what equations mean.",
        "icon":  "🧬",
        "step":  "Step 5",
    },
    "SANDESH": {
        "what":  "Communicate your complete understanding in your own words — in two languages.",
        "why":   "If you cannot explain it clearly, you have not yet understood it.",
        "icon":  "📝",
        "step":  "Step 6",
    },
}

KOREAN_PRACTICE = {
    "SAATHI":  ("진단", "현재 이해 수준 파악"),
    "KHOJI":   ("탐구", "과학적 질문과 가설 형성"),
    "PRAMAN":  ("증거", "증거 평가 및 데이터 분석"),
    "TARKA":   ("논증", "과학적 주장 구성"),
    "RUPAK":   ("모델링", "세 가지 표상 수준 탐색"),
    "SANDESH": ("소통", "이중언어 과학 의사소통"),
}


def render_orientation(group_code: str, lang: str = "ne"):
    """
    Renders the scientific practice cycle orientation panel.
    Shown on student dashboard before starting any agent.
    Adapts content to the student's research group.
    """
    from config import normalise_group
    group_code = normalise_group(group_code)   # handle "Control" → "CON" etc.
    accessible = get_accessible_agents(group_code)
    cfg        = get_group_config(group_code)

    st.markdown("---")

    if lang == "ko":
        st.markdown("### 🧪 과학적 실천 사이클")
        st.caption(f"연구 그룹: **{cfg['label']}**")
    elif lang == "ne":
        st.markdown("### 🧪 वैज्ञानिक अभ्यास चक्र")
        st.caption(f"अनुसन्धान समूह: **{cfg['label']}**")
    else:
        st.markdown("### 🧪 Your Scientific Practice Cycle")
        st.caption(f"Research Group: **{cfg['label']}**")

    if is_control(group_code):
        if lang == "ko":
            st.info("📋 귀하의 그룹은 표준 수업 자료를 사용합니다. "
                    "아래 진단 질문을 완성하세요.")
        elif lang == "ne":
            st.info("📋 तपाईंको समूहले मानक कक्षा सामग्री प्रयोग गर्दछ। "
                    "तलको निदानात्मक प्रश्न पूरा गर्नुहोस्।")
        else:
            st.info("📋 Your group uses standard classroom materials. "
                    "Complete the diagnostic question below.")
        return

    # Display only accessible agents
    if not accessible:   # safety: CON group or unknown → no columns
        return
    cols = st.columns(len(accessible))
    for i, key in enumerate(accessible):
        info = PRACTICE_DESCRIPTIONS.get(key, {})
        ko   = KOREAN_PRACTICE.get(key, ("", ""))
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"### {info.get('icon','')} {info.get('step','')}")

                if lang == "ko":
                    st.markdown(f"**{ko[0]}**")
                    st.caption(ko[1])
                elif lang == "ne":
                    name_ne = AGENTS[key]["nepali_name"] if key in AGENTS else key
                    st.markdown(f"**{name_ne}**")
                    st.caption(info.get("what", ""))
                else:
                    st.markdown(f"**{AGENTS[key]['name'] if key in AGENTS else key}**")
                    st.caption(info.get("what", ""))

                completed = st.session_state.get("agent_completed", {})
                if completed.get(key):
                    st.success("✅")
                elif i == 0 or completed.get(accessible[i-1] if i > 0 else None):
                    st.warning("▶ Active")
                else:
                    st.info("🔒 Locked")

    # Scientific practice cycle explanation
    st.markdown("---")
    if lang == "ko":
        st.caption(
            "💡 각 AI 에이전트는 실제 과학자들이 수행하는 특정 과학적 실천을 도와줍니다. "
            "순서대로 완성하여 완전한 과학적 이해를 구축하세요."
        )
    elif lang == "ne":
        st.caption(
            "💡 प्रत्येक AI एजेन्टले वास्तविक वैज्ञानिकहरूले गर्ने विशेष वैज्ञानिक "
            "अभ्यासमा मद्दत गर्छ। पूर्ण वैज्ञानिक बुझाइ निर्माण गर्न क्रमशः पूरा गर्नुहोस्।"
        )
    else:
        st.caption(
            "💡 Each AI agent scaffolds a specific scientific practice that real scientists use. "
            "Complete them in sequence to build genuine scientific understanding."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MULTIMODAL RUPAK — Image upload + GPT-4o Vision (MMALE group only)
# ═══════════════════════════════════════════════════════════════════════════════

def render_rupak_multimodal(uid: str, group_code: str, module: dict, lang: str = "ne"):
    """
    Renders the multimodal version of Rupak for MMALE group.
    Allows students to upload hand-drawn molecular model images.
    GPT-4o Vision analyzes the image and provides epistemic feedback.

    This is the key feature that distinguishes MMALE from MA:
      MA:    Rupak receives TEXT descriptions of molecular models
      MMALE: Rupak receives IMAGES of student-drawn molecular models

    The epistemic significance: visual model construction and evaluation
    is qualitatively different from verbal description. Students must
    externalize their submicroscopic mental model as a drawing before
    Rupak can respond to its accuracy — this is genuine model-based
    learning (Justi & Gilbert, 2002).
    """
    from agents import RUPAK_SYSTEM_PROMPT
    from database_manager import log_temporal_trace

    topic = module.get("Sub_Title", "this concept")

    if lang == "ko":
        st.markdown("### 🧬 Rupak AI (रूपक) — 분자 모델링")
        st.info(
            "**MMALE 특별 기능:** 분자 모델을 종이에 그린 후 사진을 업로드하세요. "
            "Rupak이 귀하의 모델을 분석하고 세 가지 표상 수준에서 피드백을 제공합니다."
        )
        upload_label = "분자 모델 이미지 업로드 (손으로 그린 그림 또는 사진)"
        text_label   = "또는 텍스트로 분자를 설명하세요:"
        submit_label = "Rupak에게 분석 요청"
    elif lang == "ne":
        st.markdown("### 🧬 Rupak AI (रूपक) — आणविक मोडेलिङ")
        st.info(
            "**MMALE विशेष सुविधा:** कागजमा आणविक मोडेल बनाएर फोटो अपलोड गर्नुहोस्। "
            "Rupak ले तपाईंको मोडेलको विश्लेषण गरेर तीन तहमा प्रतिक्रिया दिनेछ।"
        )
        upload_label = "आणविक मोडेल छवि अपलोड गर्नुहोस् (हातले बनाएको चित्र)"
        text_label   = "वा पाठमा अणु वर्णन गर्नुहोस्:"
        submit_label = "Rupak लाई विश्लेषण गर्न अनुरोध"
    else:
        st.markdown("### 🧬 Rupak AI (रूपक) — Molecular Modelling")
        st.info(
            "**MMALE Feature:** Draw your molecular model on paper and upload a photo. "
            "Rupak will analyse your model and give feedback at all three "
            "representational levels (macroscopic, submicroscopic, symbolic)."
        )
        upload_label = "Upload your molecular model image (hand-drawn is perfect)"
        text_label   = "Or describe your model in text:"
        submit_label = "Ask Rupak to Analyse"

    col_draw, col_chat = st.columns([1, 1.5], gap="large")

    with col_draw:
        with st.container(border=True):
            st.caption("📐 Draw your molecular model on paper, then photograph it.")

            # Johnstone's triangle reference
            st.markdown("""
**Three levels to represent:**
- 🔴 **Macroscopic**: What you observe
- 🟡 **Submicroscopic**: Atoms and molecules
- 🔵 **Symbolic**: Equation and formulae
            """)

            uploaded_image = st.file_uploader(
                upload_label,
                type=["jpg", "jpeg", "png", "webp"],
                key=f"rupak_img_{topic}",
            )

            if uploaded_image:
                st.image(uploaded_image, caption="Your molecular model", use_column_width=True)

            text_description = st.text_area(
                text_label,
                placeholder="e.g., I drew Na giving its electron to Cl, forming Na+ and Cl-...",
                key=f"rupak_text_{topic}",
                height=100,
            )

    with col_chat:
        # Display previous Rupak conversation
        rupak_msgs = st.session_state.get("rupak_messages", [])
        for m in rupak_msgs[1:]:  # skip system prompt
            display = m.get("content", "")
            if isinstance(display, list):
                # multimodal message — extract text parts only for display
                display = " ".join(
                    p.get("text", "") for p in display if isinstance(p, dict) and p.get("type") == "text"
                )
            for code in ALL_SIGNAL_CODES:
                display = display.replace(code, "")
            with st.chat_message(m["role"]):
                st.markdown(display.strip())

        if st.button(submit_label, type="primary"):
            if not uploaded_image and len(text_description.strip()) < 5:
                st.error("Please upload an image or describe your model in text.")
                return

            # Build multimodal message content
            if uploaded_image:
                img_bytes  = uploaded_image.read()
                img_b64    = base64.b64encode(img_bytes).decode("utf-8")
                mime_type  = uploaded_image.type or "image/jpeg"
                user_content = [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{img_b64}",
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"This is my molecular model drawing for: {topic}. "
                            + (text_description.strip() if text_description.strip()
                               else "Please analyse my drawn model.")
                        ),
                    },
                ]
            else:
                user_content = text_description.strip()

            user_msg = {"role": "user", "content": user_content}

            if not rupak_msgs:
                from agents import initialise_agent
                ctx = {**st.session_state.get("agent_context", {})}
                rupak_msgs = initialise_agent("RUPAK", ctx)

            rupak_msgs.append(user_msg)

            with st.spinner("🧬 Rupak is analysing your model..."):
                result = call_agent_vision(
                    messages  = rupak_msgs,
                    api_key   = st.secrets["OPENAI_API_KEY"],
                    is_vision = uploaded_image is not None,
                )

            ai_content = result["content"]
            rupak_msgs.append({"role": "assistant", "content": ai_content})
            st.session_state["rupak_messages"] = rupak_msgs

            # Log with image flag
            img_flag = "|MODE:IMAGE" if uploaded_image else "|MODE:TEXT"
            log_temporal_trace(
                uid, "RUPAK_MULTIMODAL_CHAT",
                f"Topic:{topic}{img_flag}|REP:{result.get('rep_level','?')}|"
                f"Student:{str(user_content)[:200]}"
            )
            log_temporal_trace(
                uid, "RUPAK_MULTIMODAL_CHAT",
                f"Topic:{topic}{img_flag}|AI:{ai_content[:300]}"
            )

            # Update rep level
            if result.get("rep_level"):
                st.session_state["current_rep_level"] = result["rep_level"]

            # Check for triadic completion
            if result.get("triadic"):
                completed = st.session_state.get("agent_completed", {})
                completed["RUPAK"] = True
                st.session_state.agent_completed = completed
                from database_manager import log_assessment, get_nepal_time
                log_assessment(
                    uid, group_code, topic,
                    "N/A", "N/A",
                    "Triadic fluency via multimodal model analysis",
                    "N/A", "TRIADIC_COMPLETE", get_nepal_time()
                )

            st.rerun()


def call_agent_vision(messages: list, api_key: str, is_vision: bool = False) -> dict:
    """
    Extended call_agent for multimodal (vision) interactions.
    Used by render_rupak_multimodal for MMALE group.
    Sends image + text to GPT-4o Vision API.
    """
    from agents import (
        detect_rep_level, detect_redirect,
        detect_tap_level, detect_communication_level,
    )

    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model    = "gpt-4o",    # gpt-4o supports vision natively
        messages = messages,
        max_tokens = 1000,
    )
    content = resp.choices[0].message.content

    display = content
    for code in ALL_SIGNAL_CODES:
        display = display.replace(code, "")

    return {
        "content":       content,
        "display":       display.strip(),
        "rep_level":     detect_rep_level(content),
        "tap_level":     detect_tap_level(content),
        "redirect":      detect_redirect(content),
        "comm_level":    detect_communication_level(content),
        "triadic":       "[TRIADIC_FLUENCY_DETECTED]" in content,
        "vision_used":   is_vision,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. GROUP INFO PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def render_group_info(group_code: str, lang: str = "ne"):
    """Compact sidebar panel showing what the student's group can access."""
    from config import normalise_group
    group_code = normalise_group(group_code)
    cfg = get_group_config(group_code)

    if lang == "ko":
        label = "연구 그룹"
    elif lang == "ne":
        label = "अनुसन्धान समूह"
    else:
        label = "Research Group"

    with st.sidebar.expander(f"🔬 {label}: {group_code}", expanded=False):
        st.caption(cfg["description"])
        agents = cfg["agents"]
        if not agents:
            st.info("No AI agents — standard instruction")
        else:
            for key in agents:
                a = AGENTS.get(key, {})
                st.write(f"{a.get('icon','')} **{a.get('nepali_name',key)}** — {a.get('role','')}")
        if cfg["multimodal"]:
            st.success("✅ Multimodal image input enabled (Rupak AI)")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VISUAL AGENT JOURNEY TRACKER (sidebar)
# ═══════════════════════════════════════════════════════════════════════════════

def render_progress_journey(group_code: str, lang: str = "ne"):
    from config import normalise_group
    group_code = normalise_group(group_code)
    """
    Visual progress tracker for the sidebar.
    Shows agent sequence with completion status.
    More compact and informative than the original text list.
    """
    accessible = get_accessible_agents(group_code)
    if not accessible:
        return

    completed = st.session_state.get("agent_completed", {})

    if lang == "ko":
        st.sidebar.markdown("### 🗺️ 학습 여정")
    elif lang == "ne":
        st.sidebar.markdown("### 🗺️ सिकाइ यात्रा")
    else:
        st.sidebar.markdown("### 🗺️ Learning Journey")

    total     = len(accessible)
    done      = sum(1 for k in accessible if completed.get(k))
    pct       = int(done / total * 100) if total else 0

    st.sidebar.progress(pct / 100, text=f"{done}/{total} agents complete")

    for i, key in enumerate(accessible):
        a    = AGENTS.get(key, {})
        icon = a.get("icon", "")
        if lang == "ko":
            name = KOREAN_PRACTICE.get(key, (key, ""))[0]
        elif lang == "ne":
            name = a.get("nepali_name", key)
        else:
            name = a.get("role", key)

        if completed.get(key):
            st.sidebar.markdown(f"✅ {icon} ~~{name}~~")
        elif i == 0 or completed.get(accessible[i-1]):
            st.sidebar.markdown(f"▶️ **{icon} {name}** ← active")
        else:
            st.sidebar.markdown(f"🔒 {icon} {name}")
