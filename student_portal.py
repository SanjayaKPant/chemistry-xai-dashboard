"""
student_portal.py — MMALE Student Interface (Final)
=====================================================
Fixes applied in this version (12 issues resolved):

  1.  get_spreadsheet() replaces open_by_key() everywhere — performance fix
  2.  config imports added — group access control, language system
  3.  mmale_components imports added — orientation panel, multimodal Rupak
  4.  Group fallback changed from 'School A' to 'CON'
  5.  CON group logic — control students see diagnostic only, no AI tabs
  6.  Group-aware menu — SA sees Saathi; MA sees Saathi+Tarka+Rupak;
      MMALE sees all 6; CON sees no AI tabs
  7.  Language selector — English / Nepali / Korean in sidebar
  8.  Orientation panel — scientific practice cycle on dashboard
  9.  redirect_map updated — all 6 agents covered
  10. Agent access control — unlock gate checks group permissions
  11. Revision form routes to correct 6-agent tab names
  12. render_modules and metacognitive dashboard use get_spreadsheet()

Group behaviour:
  CON   — Four-tier diagnostic only. No AI. Pre/post data collected.
  SA    — Saathi AI only. Diagnostic + Socratic misconception correction.
  MA    — Saathi + Tarka + Rupak. Text-based multi-agent interaction.
  MMALE — All 6 agents. Multimodal Rupak with image upload (GPT-4o Vision).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import (
    get_spreadsheet, log_assessment, log_temporal_trace,
    log_tap_event, log_rep_event,
)
from datetime import datetime, timedelta

# ── Multi-agent system ────────────────────────────────────────────────────────
from agents import (
    AGENTS, AGENT_SEQUENCE, ALL_SIGNAL_CODES,
    initialise_agent, call_agent,
    detect_tap_level, detect_rep_level,
    detect_hypothesis_quality, detect_evidence_quality,
    detect_communication_level, detect_redirect,
)

# ── Group access control and language system ──────────────────────────────────
from config import (
    get_group_config, get_accessible_agents,
    is_multimodal, is_control, build_student_menu,
    get_language, render_language_selector,
    agent_accessible, t,
)

# ── UI components ─────────────────────────────────────────────────────────────
from mmale_components import (
    render_orientation, render_rupak_multimodal,
    render_group_info, render_progress_journey,
)

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"

# ── Agent tab name map (for routing) ─────────────────────────────────────────
AGENT_TAB_MAP = {
    "SAATHI":  "🔬 साथी (Saathi) AI",
    "KHOJI":   "🔭 खोजी (Khoji) AI",
    "PRAMAN":  "🧪 प्रमाण (Praman) AI",
    "TARKA":   "⚖️ तर्क (Tarka) AI",
    "RUPAK":   "🧬 रूपक (Rupak) AI",
    "SANDESH": "📝 सन्देश (Sandesh) AI",
}

# Agent-specific chat placeholders (trilingual)
CHAT_PLACEHOLDERS = {
    "SAATHI":  {
        "en": "Explain your thinking to Saathi...",
        "ne": "साथीलाई आफ्नो सोच बताउनुहोस्...",
        "ko": "사아티에게 생각을 설명해보세요...",
    },
    "KHOJI":   {
        "en": "What puzzles you? What do you want to investigate?",
        "ne": "के तपाईंलाई अचम्म लाग्छ? के खोज्न चाहनुहुन्छ?",
        "ko": "무엇이 궁금한가요? 무엇을 탐구하고 싶나요?",
    },
    "PRAMAN":  {
        "en": "What evidence supports your claim?",
        "ne": "तपाईंको दाबीलाई कुन प्रमाणले समर्थन गर्छ?",
        "ko": "어떤 증거가 주장을 뒷받침하나요?",
    },
    "TARKA":   {
        "en": "State your claim, evidence, or reasoning to Tarka...",
        "ne": "तर्कलाई आफ्नो दाबी, प्रमाण वा तर्क बताउनुहोस्...",
        "ko": "주장, 증거 또는 추론을 타르카에게 말해보세요...",
    },
    "RUPAK":   {
        "en": "Describe what you observe or imagine at the molecular level...",
        "ne": "आणविक स्तरमा के देख्नुहुन्छ वा कल्पना गर्नुहुन्छ?",
        "ko": "분자 수준에서 무엇을 관찰하거나 상상하나요?",
    },
    "SANDESH": {
        "en": "Summarise your scientific understanding here...",
        "ne": "यहाँ आफ्नो वैज्ञानिक बुझाइ संक्षेप गर्नुहोस्...",
        "ko": "여기에 과학적 이해를 요약하세요...",
    },
}

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)
            ).strftime("%Y-%m-%d %H:%M:%S")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def show():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first / 먼저 로그인하세요)")
        st.stop()

    user  = st.session_state.user
    uid   = str(user.get("User_ID", "")).upper()
    # FIX 4: normalise group name ("Control" → "CON", "School A" → "SA" etc.)
    from config import normalise_group
    group = normalise_group(str(user.get("Group", "CON")))

    # ── Language ──────────────────────────────────────────────────────────────
    lang = render_language_selector(sidebar=True)   # FIX 7

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.title(f"🎓 {user.get('Name')}")

    grp_label = t("group_label", lang)
    cfg       = get_group_config(group)
    st.sidebar.markdown(f"**{grp_label}:** {cfg['label']}")

    # FIX: group info and progress journey from mmale_components
    render_group_info(group, lang)      # FIX 3
    render_progress_journey(group, lang)  # FIX 3

    # ── Group-aware navigation menu ───────────────────────────────────────────
    # FIX 5 + 6: CON sees no AI tabs; other groups see only accessible agents
    menu = build_student_menu(group)    # FIX 6

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    # Safety: if current_tab is an agent not in this group's menu, reset
    if st.session_state.current_tab not in menu:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio(
        "Navigation", menu,
        index=menu.index(st.session_state.current_tab),
        key="nav_radio",
    )
    st.session_state.current_tab = choice

    # ── Route ─────────────────────────────────────────────────────────────────
    if   choice == "🏠 Dashboard":              render_dashboard(user, group, lang)
    elif choice == "📚 Learning Modules":       render_modules(uid, group, lang)
    elif choice == "🔬 साथी (Saathi) AI":      render_agent_chat(uid, group, "SAATHI", lang)
    elif choice == "🔭 खोजी (Khoji) AI":       render_agent_chat(uid, group, "KHOJI", lang)
    elif choice == "🧪 प्रमाण (Praman) AI":    render_agent_chat(uid, group, "PRAMAN", lang)
    elif choice == "⚖️ तर्क (Tarka) AI":       render_agent_chat(uid, group, "TARKA", lang)
    elif choice == "🧬 रूपक (Rupak) AI":       render_agent_chat(uid, group, "RUPAK", lang)
    elif choice == "📝 सन्देश (Sandesh) AI":   render_agent_chat(uid, group, "SANDESH", lang)
    elif choice == "📈 My Progress":            render_metacognitive_dashboard(uid, lang)

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_dashboard(user, group: str, lang: str = "ne"):
    name = user.get("Name", "")
    if lang == "ko":
        st.title(f"환영합니다, {name}! 🙏")
    elif lang == "ne":
        st.title(f"नमस्ते, {name}! 🙏")
    else:
        st.title(f"Welcome, {name}! 🙏")

    st.markdown("---")

    # FIX 8: Orientation panel showing scientific practice cycle
    render_orientation(group, lang)

    # Agent ecology cards — only show accessible agents
    accessible = get_accessible_agents(group)
    if accessible:
        st.markdown("---")
        if lang == "ko":
            st.markdown("### 🤖 AI 에이전트 생태계")
        elif lang == "ne":
            st.markdown("### 🤖 AI एजेन्ट पारिस्थितिकी")
        else:
            st.markdown("### 🤖 Your AI Agent Ecology")

        cols = st.columns(len(accessible))
        for i, key in enumerate(accessible):
            agent = AGENTS[key]
            completed = st.session_state.get("agent_completed", {})
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"## {agent['icon']}")
                    if lang == "ko":
                        from config import KOREAN_PRACTICE
                        ko = KOREAN_PRACTICE.get(key, (key, ""))
                        st.markdown(f"**{ko[0]}**")
                        st.caption(ko[1])
                    elif lang == "ne":
                        st.markdown(f"**{agent['nepali_name']}**")
                        st.caption(agent["role"])
                    else:
                        st.markdown(f"**{agent['name']}**")
                        st.caption(agent["role"])
                    if completed.get(key):
                        st.success("✅")

# ═══════════════════════════════════════════════════════════════════════════════
# LEARNING MODULES (four-tier diagnostic)
# ═══════════════════════════════════════════════════════════════════════════════

def render_modules(uid: str, group: str, lang: str = "ne"):
    if lang == "ko":
        st.header("📚 학습 모듈")
    elif lang == "ne":
        st.header("📚 सिकाइ मोड्युलहरू")
    else:
        st.header("📚 Learning Modules")

    try:
        # FIX 1 + 12: use get_spreadsheet() — no new connection per call
        sh = get_spreadsheet()

        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished_modules = []
        if not log_df.empty:
            log_df.columns = [c.strip() for c in log_df.columns]
            user_mask   = (log_df["User_ID"].astype(str).str.upper().str.strip()
                           == uid.strip().upper())
            status_mask = log_df["Status"].astype(str).str.strip() == "POST"
            finished_modules = (
                log_df[user_mask & status_mask]["Module_ID"]
                .astype(str).str.strip().tolist()
            )

        m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())

        # Safety: empty sheet or missing header → no modules yet
        if m_df.empty:
            st.info("No modules deployed yet. Please wait for your teacher to add content." if lang == "en"
                    else "모듈이 아직 없습니다. 선생님을 기다려주세요." if lang == "ko"
                    else "अहिलेसम्म कुनै मोड्युल छैन। कृपया शिक्षकको प्रतीक्षा गर्नुहोस्।")
            return

        # Detect group column (handles "Group", "group", spaces)
        group_col = next(
            (c for c in m_df.columns if c.strip().upper() == "GROUP"), None
        )
        if group_col is None:
            st.warning("Instructional_Materials sheet is missing a 'Group' column. "
                       "Please check with your administrator.")
            return

        # Match both new codes (SA/MA/MMALE/CON) AND old names (School A etc.)
        from config import GROUP_ALIASES, normalise_group
        aliases = GROUP_ALIASES.get(group, [group])
        available = m_df[
            m_df[group_col].astype(str).str.strip().str.upper().isin(aliases)
        ]

        if available.empty:
            st.warning(f"No modules found for group: {group}")
            return

        active_row = None
        for _, row in available.iterrows():
            if str(row["Sub_Title"]).strip() not in finished_modules:
                active_row = row
                break

        if active_row is None:
            if lang == "ko":
                st.success("🎉 모든 모듈 완료!")
            elif lang == "ne":
                st.success("🎉 सबै मोड्युलहरू पूरा भए!")
            else:
                st.success("🎉 All modules complete!")
            return

        m_id = active_row["Sub_Title"]
        st.subheader(f"📖 {m_id}")
        with st.expander(
            "Learning Objectives / सिकाइ उद्देश्यहरू / 학습 목표",
            expanded=True
        ):
            st.write(active_row.get("Objectives", "Explore this concept."))

        st.write(f"**{'진단 질문' if lang=='ko' else 'Diagnostic Question' if lang=='en' else 'निदानात्मक प्रश्न'}:**")
        st.write(active_row["Diagnostic_Question"])

        opts = [active_row["Option_A"], active_row["Option_B"],
                active_row["Option_C"], active_row["Option_D"]]

        # Tier labels adapt to language
        t1_label = ("귀하의 답 (Tier 1):" if lang == "ko"
                    else "तपाईंको उत्तर (Tier 1 Choice):" if lang == "ne"
                    else "Your Answer (Tier 1):")
        t2_label = ("자신감 (Tier 2):" if lang == "ko"
                    else "आत्मविश्वास (Tier 2):" if lang == "ne"
                    else "Confidence in answer (Tier 2):")
        t3_label = ("이 답을 선택한 이유 (Tier 3):" if lang == "ko"
                    else "तपाईंले किन यो उत्तर रोज्नुभयो? (Tier 3 Reasoning):" if lang == "ne"
                    else "Why did you choose this answer? (Tier 3 Reasoning):")
        t4_label = ("추론에 대한 자신감 (Tier 4):" if lang == "ko"
                    else "तर्कमा आत्मविश्वास (Tier 4):" if lang == "ne"
                    else "Confidence in your reasoning (Tier 4):")
        conf_opts = (["추측", "불확실", "확실", "매우 확실"] if lang == "ko"
                     else ["Guessing", "Unsure", "Sure", "Very Sure"])

        t1 = st.radio(t1_label, opts, key=f"t1_{m_id}")
        t2 = st.select_slider(t2_label, conf_opts, key=f"t2_{m_id}")
        t3 = st.text_area(t3_label, key=f"t3_{m_id}")
        t4 = st.select_slider(t4_label, conf_opts, key=f"t4_{m_id}")

        btn_label = ("제출 및 토론 시작" if lang == "ko"
                     else "Submit & Start Discussion" if lang == "en"
                     else "पेश गर्नुहोस् र छलफल सुरु गर्नुहोस्")

        if st.button(btn_label):
            if len(t3.strip()) < 5:
                err = ("추론을 입력해주세요." if lang == "ko"
                       else "❌ Please provide reasoning."
                       if lang == "en" else "❌ कृपया तर्क प्रदान गर्नुहोस्।")
                st.error(err)
            else:
                log_assessment(uid, group, m_id, t1, t2, t3, t4,
                               "INITIAL", get_nepal_time())

                context = {"topic": m_id, "t1": t1, "t3": t3}
                st.session_state.active_module     = active_row.to_dict()
                st.session_state.active_agent      = "SAATHI"
                st.session_state.saathi_messages   = initialise_agent("SAATHI", context)
                st.session_state.agent_context     = context
                st.session_state.current_tap_level = "TAP_1"
                st.session_state.current_rep_level = "MONADIC"
                st.session_state.agent_completed   = {}
                st.session_state.mastery_triggered = False

                # Initialise all message keys to None
                for key in ["khoji", "praman", "tarka", "rupak", "sandesh"]:
                    st.session_state[f"{key}_messages"] = None
                    st.session_state[f"{key}_turn"]     = 0

                # FIX 5: CON group stays in modules; others go to Saathi
                if is_control(group):
                    st.session_state.current_tab = "📚 Learning Modules"
                else:
                    st.session_state.current_tab = AGENT_TAB_MAP["SAATHI"]
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")
        st.exception(e)

# ═══════════════════════════════════════════════════════════════════════════════
# CON GROUP: POST-DIAGNOSTIC FORM (no AI)
# ═══════════════════════════════════════════════════════════════════════════════

def render_con_post_form(uid: str, group: str, module: dict, lang: str):
    """
    Control group students complete Tiers 5-6 without AI interaction.
    They receive a printed study guide (teacher-provided) and then
    submit their revised answer. This preserves the pre/post structure
    for comparison with AI groups.
    """
    if lang == "ko":
        st.success("✅ 진단 답변이 기록되었습니다.")
        st.info("교사가 제공한 학습 자료를 검토한 후 아래에서 최종 답변을 제출하세요.")
    elif lang == "ne":
        st.success("✅ निदानात्मक उत्तर रेकर्ड गरियो।")
        st.info("शिक्षकले दिएको अध्ययन सामग्री हेरेपछि तलको अन्तिम उत्तर पेश गर्नुहोस्।")
    else:
        st.success("✅ Diagnostic answer recorded.")
        st.info("After reviewing the study materials provided by your teacher, "
                "submit your final answer below.")

    with st.form("con_post_form"):
        opts = [module["Option_A"], module["Option_B"],
                module["Option_C"], module["Option_D"]]
        conf_opts = (["추측", "불확실", "확실", "매우 확실"] if lang == "ko"
                     else ["Guessing", "Unsure", "Sure", "Very Sure"])

        t5 = st.radio(
            "최종 선택 (Tier 5):" if lang == "ko"
            else "Final Choice (Tier 5):" if lang == "en"
            else "अन्तिम विकल्प (Tier 5):", opts
        )
        t6 = st.select_slider(
            "최종 자신감 (Tier 6):" if lang == "ko"
            else "Final Confidence (Tier 6):" if lang == "en"
            else "अन्तिम आत्मविश्वास (Tier 6):", conf_opts
        )
        reflection = st.text_area(
            "학습 후 생각이 어떻게 바뀌었나요?" if lang == "ko"
            else "What changed in your thinking after studying?" if lang == "en"
            else "अध्ययनपछि तपाईंको सोच कसरी परिवर्तन भयो?"
        )

        lbl = ("저장 및 완료" if lang == "ko"
               else "Save & Complete" if lang == "en"
               else "सुरक्षित गर्नुहोस् र पूरा गर्नुहोस्")
        if st.form_submit_button(lbl):
            log_assessment(
                uid, group, module["Sub_Title"],
                "N/A", "N/A", reflection, "N/A",
                "POST", get_nepal_time(), t5, t6
            )
            st.session_state.active_module     = None
            st.session_state.mastery_triggered = False
            st.session_state.current_tab       = "🏠 Dashboard"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED AGENT CHAT RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_agent_chat(uid: str, group: str, agent_key: str, lang: str = "ne"):
    module = st.session_state.get("active_module")
    if not module:
        msg = ("먼저 학습 모듈에서 초기 답변을 제출해주세요." if lang == "ko"
               else "⚠️ Please submit an initial answer in Learning Modules first."
               if lang == "en"
               else "⚠️ पहिले Learning Modules मा प्रारम्भिक उत्तर पेश गर्नुहोस्।")
        st.warning(msg)
        return

    # ── FIX 10: Group access check ────────────────────────────────────────────
    if not agent_accessible(agent_key, group):
        st.error(
            f"This agent ({agent_key}) is not available for your research group "
            f"({group}). Accessible agents: {get_accessible_agents(group)}"
        )
        return

    agent   = AGENTS[agent_key]
    msg_key = f"{agent_key.lower()}_messages"

    # ── Sequential unlock gates ───────────────────────────────────────────────
    UNLOCK_MAP = {
        "KHOJI":   ("SAATHI",  AGENT_TAB_MAP["SAATHI"]),
        "PRAMAN":  ("KHOJI",   AGENT_TAB_MAP["KHOJI"]),
        "TARKA":   ("PRAMAN",  AGENT_TAB_MAP["PRAMAN"]),
        "RUPAK":   ("TARKA",   AGENT_TAB_MAP["TARKA"]),
        "SANDESH": ("RUPAK",   AGENT_TAB_MAP["RUPAK"]),
    }
    # For MA group, TARKA unlocks after SAATHI (skip KHOJI/PRAMAN)
    if group == "MA" and agent_key == "TARKA":
        UNLOCK_MAP["TARKA"] = ("SAATHI", AGENT_TAB_MAP["SAATHI"])
    if group == "MA" and agent_key == "RUPAK":
        UNLOCK_MAP["RUPAK"] = ("TARKA", AGENT_TAB_MAP["TARKA"])

    if agent_key in UNLOCK_MAP:
        prereq_key, prereq_tab = UNLOCK_MAP[agent_key]
        if not st.session_state.get("agent_completed", {}).get(prereq_key):
            prereq_name = AGENTS[prereq_key]["name"]
            lock_msg = (f"⚠️ **{prereq_name}**를 먼저 완성해야 "
                        f"**{agent['name']}**를 열 수 있습니다." if lang == "ko"
                        else f"⚠️ पहिले **{AGENTS[prereq_key]['nepali_name']}** पूरा गर्नुहोस्।"
                        if lang == "ne"
                        else f"⚠️ Complete **{prereq_name}** first to unlock "
                             f"**{agent['name']}**.")
            st.warning(lock_msg)
            btn_lbl = (f"{prereq_name}으로 이동" if lang == "ko"
                       else f"{AGENTS[prereq_key]['nepali_name']} मा जानुहोस्"
                       if lang == "ne"
                       else f"Go to {prereq_name}")
            if st.button(btn_lbl):
                st.session_state.current_tab = prereq_tab
                st.rerun()
            return

        if st.session_state.get(msg_key) is None:
            ctx = {
                **st.session_state.get("agent_context", {}),
                "tap_level": st.session_state.get("current_tap_level", "TAP_1"),
                "rep_level": st.session_state.get("current_rep_level", "MONADIC"),
            }
            st.session_state[msg_key] = initialise_agent(agent_key, ctx)
            st.session_state[f"{agent_key.lower()}_turn"] = 0

    messages = st.session_state.get(msg_key, [])

    # ── Post-mastery forms ────────────────────────────────────────────────────
    completed = st.session_state.get("agent_completed", {})

    if agent_key == "SAATHI" and st.session_state.get("mastery_triggered"):
        st.balloons()
        render_revision_form(uid, group, module, lang)
        return

    # Completion screens for each agent
    _completion_screens = {
        "TARKA": ("RUPAK", AGENT_TAB_MAP["RUPAK"],
                  "✅ Argumentation complete! / तर्क पूरा! / 논증 완료!",
                  "Your TAP level: / तपाईंको TAP स्तर: / TAP 수준:",
                  "current_tap_level",
                  "Continue to Rupak AI →"),
        "RUPAK": ("SANDESH", AGENT_TAB_MAP["SANDESH"],
                  "🎉 Representational fluency achieved! / रूपण दक्षता! / 표상 유창성 달성!",
                  "Representational level: / स्तर: / 표상 수준:",
                  "current_rep_level",
                  "Continue to Sandesh AI →"),
        "KHOJI": ("PRAMAN", AGENT_TAB_MAP["PRAMAN"],
                  "✅ Hypothesis formed! / परिकल्पना बनाइयो! / 가설 형성!",
                  "", "", "Continue to Praman AI →"),
        "PRAMAN": ("TARKA", AGENT_TAB_MAP["TARKA"],
                   "✅ Evidence evaluated! / प्रमाण मूल्याङ्कन! / 증거 평가 완료!",
                   "", "", "Continue to Tarka AI →"),
        "SANDESH": (None, None,
                    "🎓 Full Ecology Complete! / पूर्ण पारिस्थितिकी! / 전체 완성!",
                    "", "", ""),
    }

    if agent_key in _completion_screens and completed.get(agent_key):
        next_key, next_tab, success_msg, level_label, level_state, btn_txt = \
            _completion_screens[agent_key]
        st.success(success_msg)
        if level_state:
            st.info(f"{level_label} **{st.session_state.get(level_state, '—')}**")
        if next_tab and st.button(btn_txt):
            st.session_state.current_tab = next_tab
            st.rerun()
        return

    # ── MMALE Multimodal Rupak ────────────────────────────────────────────────
    if agent_key == "RUPAK" and is_multimodal(group):
        render_rupak_multimodal(uid, group, module, lang)
        return

    # ── Standard two-column chat layout ──────────────────────────────────────
    col_phenom, col_chat = st.columns([1, 1.5], gap="large")

    with col_phenom:
        if lang == "ko":
            st.markdown("### 📝 현재 개념")
        elif lang == "ne":
            st.markdown("### 📝 वर्तमान अवधारणा")
        else:
            st.markdown("### 📝 Current Concept")

        with st.container(border=True):
            st.subheader(module.get("Sub_Title", ""))
            st.write(f"**Q:** {module.get('Diagnostic_Question', '')}")
            st.write("---")
            for letter, opt_key in zip("ABCD",
                ["Option_A","Option_B","Option_C","Option_D"]):
                st.write(f"{letter}) {module.get(opt_key, '')}")

        with st.container(border=True):
            st.caption("🔬 Research Instrument")
            st.markdown(f"**{agent['instrument']}**")
            if agent_key == "TARKA":
                st.metric("TAP Level", st.session_state.get("current_tap_level","TAP_1"))
            if agent_key == "RUPAK":
                st.metric("Rep Level", st.session_state.get("current_rep_level","MONADIC"))
            if agent_key == "KHOJI":
                q_level = st.session_state.get("current_q_level", "—")
                st.metric("Question Quality", q_level)
            if agent_key == "PRAMAN":
                eq_level = st.session_state.get("current_eq_level", "—")
                st.metric("Evidence Quality", eq_level)

    with col_chat:
        st.subheader(f"{agent['icon']} {agent['name']}")
        if lang == "ko":
            from config import KOREAN_PRACTICE
            st.caption(KOREAN_PRACTICE.get(agent_key, (agent['role'],""))[1])
        else:
            st.caption(f"{agent['role']} | {agent['practice']}")

        # Render conversation history
        for m in messages[1:]:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text","") for p in content
                    if isinstance(p,dict) and p.get("type")=="text"
                )
            for code in ALL_SIGNAL_CODES:
                content = content.replace(code, "")
            with st.chat_message(m["role"]):
                st.markdown(content.strip())

        # Chat input
        placeholder = CHAT_PLACEHOLDERS.get(agent_key, {}).get(lang, "Type here...")

        if prompt := st.chat_input(placeholder):
            messages.append({"role": "user", "content": prompt})

            with st.spinner(f"{agent['icon']} {agent['nepali_name']} AI..."):
                result = call_agent(
                    agent_key = agent_key,
                    messages  = messages,
                    api_key   = st.secrets["OPENAI_API_KEY"],
                )

            ai_content = result["content"]
            messages.append({"role": "assistant", "content": ai_content})
            st.session_state[msg_key] = messages

            topic = module.get("Sub_Title", "Unknown")

            # ── Research logging ──────────────────────────────────────────────
            log_temporal_trace(
                uid, agent["db_log_type"],
                f"Topic:{topic}|Agent:{agent_key}|Group:{group}|"
                f"Lang:{lang}|Turn:STUDENT|Msg:{prompt[:300]}"
            )
            signals = (
                f"|TAP:{result['tap_level']}" if result.get("tap_level") else ""
            ) + (
                f"|REP:{result['rep_level']}" if result.get("rep_level") else ""
            ) + (
                f"|HQ:{result['hypothesis_level']}" if result.get("hypothesis_level") else ""
            ) + (
                f"|EQ:{result['evidence_level']}" if result.get("evidence_level") else ""
            )
            log_temporal_trace(
                uid, agent["db_log_type"],
                f"Topic:{topic}|Agent:{agent_key}|Group:{group}|"
                f"Turn:AI{signals}|Msg:{ai_content[:300]}"
            )

            # Granular ArgLog / RepLog
            if agent_key == "TARKA":
                st.session_state["tarka_turn"] = (
                    st.session_state.get("tarka_turn", 0) + 1
                )
                log_tap_event(uid, group, topic,
                              result.get("tap_level"),
                              st.session_state["tarka_turn"],
                              prompt, ai_content)

            if agent_key == "RUPAK":
                st.session_state["rupak_turn"] = (
                    st.session_state.get("rupak_turn", 0) + 1
                )
                log_rep_event(uid, group, topic,
                              result.get("rep_level"),
                              st.session_state["rupak_turn"],
                              prompt, ai_content)

            # ── Update research state metrics ─────────────────────────────────
            if result.get("tap_level"):
                st.session_state.current_tap_level = result["tap_level"]
            if result.get("rep_level"):
                st.session_state.current_rep_level = result["rep_level"]
            if result.get("hypothesis_level"):
                st.session_state.current_q_level = result["hypothesis_level"]
            if result.get("evidence_level"):
                st.session_state.current_eq_level = result["evidence_level"]

            # ── Completion detection ──────────────────────────────────────────
            ca = st.session_state.get("agent_completed", {})

            if agent_key == "SAATHI" and result.get("mastery"):
                ca["SAATHI"] = True
                st.session_state.mastery_triggered = True

            if agent_key == "KHOJI" and result.get("hypothesis_level") == "HYPOTHESIS":
                ca["KHOJI"] = True
                log_temporal_trace(uid, "KHOJI_COMPLETE",
                                   f"Topic:{topic}|Group:{group}")

            if agent_key == "PRAMAN" and result.get("evidence_level") == "EQ3":
                ca["PRAMAN"] = True
                log_temporal_trace(uid, "PRAMAN_COMPLETE",
                                   f"Topic:{topic}|Group:{group}")

            if agent_key == "TARKA":
                tap = result.get("tap_level")
                if tap in ("TAP_3","TAP_4","TAP_5"):
                    ca["TARKA"] = True
                    log_assessment(uid, group, topic, "N/A","N/A",
                                   f"Argumentation at {tap}","N/A",
                                   f"TAP_COMPLETE_{tap}", get_nepal_time())

            if agent_key == "RUPAK" and result.get("triadic"):
                ca["RUPAK"] = True
                log_assessment(uid, group, topic, "N/A","N/A",
                               "Triadic fluency","N/A",
                               "TRIADIC_COMPLETE", get_nepal_time())

            if agent_key == "SANDESH" and result.get("comm_complete"):
                ca["SANDESH"] = True
                log_assessment(uid, group, topic, "N/A","N/A",
                               "Full ecology complete","N/A",
                               "ECOLOGY_COMPLETE", get_nepal_time())

            st.session_state.agent_completed = ca

            # ── FIX 9: Full redirect map for all 6 agents ─────────────────────
            redirect = result.get("redirect")
            if redirect and redirect in AGENT_TAB_MAP:
                # Only redirect if target agent is accessible to this group
                if agent_accessible(redirect, group):
                    st.info(f"🔄 → {AGENTS[redirect]['name']}")
                    st.session_state.current_tab = AGENT_TAB_MAP[redirect]
                    st.rerun()

            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TIER 5 & 6 REVISION FORM
# ═══════════════════════════════════════════════════════════════════════════════

def render_revision_form(uid: str, group: str, module: dict, lang: str = "ne"):
    success_msg = (t("mastery_detected", lang) if hasattr(t, "__call__")
                   else "🌟 Mastery Detected!")
    st.success(success_msg)

    with st.form("t56_form"):
        if lang == "ko":
            st.markdown("### 최종 평가 (Tier 5 & 6)")
        elif lang == "ne":
            st.markdown("### अन्तिम मूल्याङ्कन (Tier 5 & 6)")
        else:
            st.markdown("### Final Assessment (Tiers 5 & 6)")

        opts = [module["Option_A"], module["Option_B"],
                module["Option_C"], module["Option_D"]]
        conf_opts = (["추측","불확실","확실","매우 확실"] if lang == "ko"
                     else ["Guessing","Unsure","Sure","Very Sure"])

        t5 = st.radio(
            "최종 선택 (Tier 5):" if lang=="ko"
            else "अन्तिम विकल्प (Tier 5):" if lang=="ne"
            else "Final Choice (Tier 5):", opts
        )
        t6 = st.select_slider(
            "최종 자신감 (Tier 6):" if lang=="ko"
            else "अन्तिम आत्मविश्वास (Tier 6):" if lang=="ne"
            else "Final Confidence (Tier 6):", conf_opts
        )
        reflection = st.text_area(
            "생각이 어떻게 바뀌었나요?" if lang=="ko"
            else "तपाईंको सोचमा के परिवर्तन आयो?" if lang=="ne"
            else "What changed in your thinking?"
        )

        btn = ("저장 및 계속" if lang=="ko"
               else "सुरक्षित गर्नुहोस्" if lang=="ne"
               else "Save & Continue")

        if st.form_submit_button(btn):
            log_assessment(
                uid, group, module["Sub_Title"],
                "N/A","N/A", reflection,"N/A",
                "POST", get_nepal_time(), t5, t6
            )
            st.session_state.mastery_triggered = False
            # FIX 11: route to correct next agent based on group
            accessible = get_accessible_agents(group)
            if "KHOJI" in accessible:
                st.session_state.current_tab = AGENT_TAB_MAP["KHOJI"]
            elif "TARKA" in accessible:
                st.session_state.current_tab = AGENT_TAB_MAP["TARKA"]
            else:
                st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# METACOGNITIVE PROGRESS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_metacognitive_dashboard(uid: str, lang: str = "ne"):
    if lang == "ko":
        st.title("📈 나의 학습 진도 대시보드")
    elif lang == "ne":
        st.title("📈 मेरो प्रगति ड्यासबोर्ड")
    else:
        st.title("📈 My Progress Dashboard")
    st.markdown("---")

    try:
        # FIX 12: use get_spreadsheet()
        sh     = get_spreadsheet()
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if log_df.empty:
            st.info("No data yet. Start a learning module to see your progress!")
            return

        user_data = log_df[
            log_df["User_ID"].astype(str).str.upper() == uid.upper()
        ].copy()

        if user_data.empty:
            st.info("Complete your first module to unlock analytics.")
            return

        total    = len(user_data)
        mastered = len(user_data[user_data["Status"] == "POST"])
        tap_rows = user_data[user_data["Status"].str.startswith("TAP_COMPLETE", na=False)]
        rep_rows = user_data[user_data["Status"] == "TRIADIC_COMPLETE"]
        eco_rows = user_data[user_data["Status"] == "ECOLOGY_COMPLETE"]

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Modules",      total)
        m2.metric("Mastered",     mastered)
        m3.metric("Arguments",    len(tap_rows))
        m4.metric("Models",       len(rep_rows))
        m5.metric("Full Ecology", len(eco_rows))

        # Confidence evolution chart
        if lang == "ko":
            st.markdown("### 🧬 개념적 성장 분석")
        elif lang == "ne":
            st.markdown("### 🧬 अवधारणागत वृद्धि विश्लेषण")
        else:
            st.markdown("### 🧬 Conceptual Growth Analysis")

        conf_map  = {"Guessing":1,"Unsure":2,"Sure":3,"Very Sure":4,
                     "추측":1,"불확실":2,"확실":3,"매우 확실":4,
                     "अनुमान":1,"अनिश्चित":2,"निश्चित":3,"एकदम निश्चित":4}
        plot_data = []
        for mod in user_data["Module_ID"].unique():
            rows    = user_data[user_data["Module_ID"] == mod]
            initial = rows[rows["Status"] == "INITIAL"]
            post    = rows[rows["Status"] == "POST"]
            if not initial.empty and not post.empty:
                t2_val = initial.iloc[0].get("T2", "Guessing")
                t6_val = post.iloc[0].get("T6", "Guessing")
                plot_data.extend([
                    {"Module": mod, "Stage": "Before AI", "Confidence": conf_map.get(t2_val,1)},
                    {"Module": mod, "Stage": "After AI",  "Confidence": conf_map.get(t6_val,1)},
                ])

        if plot_data:
            fig = px.line(
                pd.DataFrame(plot_data),
                x="Stage", y="Confidence", color="Module", markers=True,
                title="Confidence Before vs After AI Interaction",
                labels={"Confidence": "Level (1–4)"},
            )
            fig.update_layout(yaxis=dict(
                tickmode="array", tickvals=[1,2,3,4],
                ticktext=["Guessing","Unsure","Sure","Very Sure"],
            ))
            st.plotly_chart(fig, use_container_width=True)

        # Learning journal
        if lang == "ko":
            st.markdown("### 📝 학습 일지")
        elif lang == "ne":
            st.markdown("### 📝 सिकाइ पत्रिका")
        else:
            st.markdown("### 📝 Learning Journal")

        display_cols = [c for c in ["Timestamp","Module_ID","Status","T1","T5"]
                        if c in user_data.columns]
        display_df = user_data[display_cols].sort_values(
            by="Timestamp", ascending=False
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Progress dashboard error: {e}")
