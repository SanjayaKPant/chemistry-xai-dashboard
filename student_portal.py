"""
student_portal.py — MMALE Student Interface (Updated)
=======================================================
Integrates Saathi (diagnostic), Tarka (argumentation), and Rupak
(modelling) agents into a unified multi-agent learning ecology.

Changes from original:
  - Imports agent system from agents.py
  - Adds agent selector UI showing current active agent
  - Adds TAP level logging to temporal traces
  - Adds representational level logging to temporal traces
  - Implements redirect protocol between agents
  - Adds agent progress tracker to sidebar
  - Preserves ALL existing Saathi / four-tier logic unchanged
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# ── Import the multi-agent system ─────────────────────────────────────────────
from agents import (
    AGENTS,
    initialise_agent,
    call_agent,
    detect_tap_level,
    detect_rep_level,
    detect_redirect,
)

# ── Research constants ────────────────────────────────────────────────────────

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

# ── Main navigation ───────────────────────────────────────────────────────────

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()

    user  = st.session_state.user
    uid   = str(user.get('User_ID')).upper()
    group = str(user.get('Group', 'School A')).strip()

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {group}")

    # Agent progress tracker in sidebar
    _render_agent_progress_sidebar()

    menu = [
        "🏠 Dashboard",
        "📚 Learning Modules",
        "🤖 साथी (Saathi) AI",
        "⚖️ तर्क (Tarka) AI",
        "🧬 रूपक (Rupak) AI",
        "📈 My Progress",
    ]

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio(
        "Navigation", menu,
        index=menu.index(st.session_state.current_tab)
              if st.session_state.current_tab in menu else 0
    )
    st.session_state.current_tab = choice

    if   choice == "🏠 Dashboard":            render_dashboard(user)
    elif choice == "📚 Learning Modules":     render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI":    render_agent_chat(uid, group, "SAATHI")
    elif choice == "⚖️ तर्क (Tarka) AI":     render_agent_chat(uid, group, "TARKA")
    elif choice == "🧬 रूपक (Rupak) AI":     render_agent_chat(uid, group, "RUPAK")
    elif choice == "📈 My Progress":          render_metacognitive_dashboard(uid)

# ── Sidebar agent progress tracker ────────────────────────────────────────────

def _render_agent_progress_sidebar():
    """Shows which agents the student has interacted with."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Agent Journey")

    completed = st.session_state.get("agent_completed", {})

    for key, agent in AGENTS.items():
        icon   = agent["icon"]
        name   = agent["nepali_name"]
        done   = completed.get(key, False)
        status = "✅" if done else "⬜"
        st.sidebar.markdown(f"{status} {icon} **{name}** — {agent['role']}")

    st.sidebar.markdown("---")

# ── Dashboard ─────────────────────────────────────────────────────────────────

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.markdown("---")

    # Multi-agent ecology overview
    st.markdown("### Your Learning Ecology")
    cols = st.columns(3)
    for i, (key, agent) in enumerate(AGENTS.items()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"## {agent['icon']}")
                st.markdown(f"**{agent['name']}**")
                st.caption(agent["role"])
                st.markdown(f"*{agent['practice']}*")

    st.markdown("---")
    st.info(
        "**Step 1:** Complete the four-tier diagnostic in **Learning Modules** to unlock Saathi AI.\n\n"
        "**Step 2:** After Saathi, build your scientific argument with **Tarka AI**.\n\n"
        "**Step 3:** Explore models and representations with **Rupak AI**."
    )

# ── Modules (four-tier diagnostic — UNCHANGED from original) ──────────────────

def render_modules(uid, group):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")

        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished_modules = []
        if not log_df.empty:
            log_df.columns = [c.strip() for c in log_df.columns]
            user_mask   = log_df['User_ID'].astype(str).str.upper().str.strip() == uid.strip().upper()
            status_mask = log_df['Status'].astype(str).str.strip() == 'POST'
            finished_modules = (
                log_df[user_mask & status_mask]['Module_ID']
                .astype(str).str.strip().tolist()
            )

        m_df      = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        available = m_df[m_df['Group'].astype(str).str.strip() == group.strip()]

        if available.empty:
            st.warning(f"No modules found for group: {group}")
            return

        active_row = None
        for _, row in available.iterrows():
            if str(row['Sub_Title']).strip() not in finished_modules:
                active_row = row
                break

        if active_row is None:
            st.success("🎉 All modules complete! / तपाईंको लागि सबै मोड्युलहरू पूरा भए!")
            return

        m_id = active_row['Sub_Title']
        st.subheader(f"📖 Concept: {m_id}")
        with st.expander("Learning Objectives", expanded=True):
            st.write(active_row.get('Objectives', 'Explore this concept.'))

        st.write(f"**Diagnostic Question:**\n{active_row['Diagnostic_Question']}")
        opts = [active_row['Option_A'], active_row['Option_B'],
                active_row['Option_C'], active_row['Option_D']]
        t1 = st.radio("तपाईंको उत्तर (Tier 1 Choice):", opts, key=f"t1_{m_id}")
        t2 = st.select_slider("आत्मविश्वास (Tier 2):",
                               ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
        t3 = st.text_area("तपाईंले किन यो उत्तर रोज्नुभयो? (Tier 3 Reasoning):", key=f"t3_{m_id}")
        t4 = st.select_slider("तर्कमा आत्मविश्वास (Tier 4):",
                               ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

        if st.button("Submit & Start Discussion with Saathi"):
            if len(t3.strip()) < 5:
                st.error("❌ Please provide reasoning to continue.")
            else:
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())

                # Initialise Saathi with student context
                context = {"topic": m_id, "t1": t1, "t3": t3}
                st.session_state.active_module   = active_row.to_dict()
                st.session_state.active_agent    = "SAATHI"
                st.session_state.saathi_messages = initialise_agent("SAATHI", context)
                st.session_state.tarka_messages  = None  # unlocked after Saathi mastery
                st.session_state.rupak_messages  = None  # unlocked after Tarka TAP_3+

                # Store context for agent handoffs
                st.session_state.agent_context   = context
                st.session_state.current_tap_level = "TAP_1"
                st.session_state.current_rep_level = "MONADIC"
                st.session_state.agent_completed   = {}
                st.session_state.mastery_triggered = False

                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

# ── Unified agent chat renderer ────────────────────────────────────────────────

def render_agent_chat(uid: str, group: str, agent_key: str):
    """
    Single renderer for all three agents.
    Handles unlock gating, redirect protocol, and database logging.
    """
    module = st.session_state.get('active_module')
    if not module:
        st.warning("⚠️ Please submit an initial answer in 'Learning Modules' first.")
        return

    agent   = AGENTS[agent_key]
    msg_key = f"{agent_key.lower()}_messages"

    # ── Unlock gate ────────────────────────────────────────────────────────────
    if agent_key == "TARKA":
        if not st.session_state.get("agent_completed", {}).get("SAATHI"):
            st.warning("⚠️ Complete your discussion with **Saathi AI** first to unlock Tarka.")
            if st.button("Go to Saathi AI"):
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()
            return
        # First visit: initialise Tarka
        if st.session_state.get(msg_key) is None:
            tap = st.session_state.get("current_tap_level", "TAP_1")
            ctx = {**st.session_state.get("agent_context", {}), "tap_level": tap}
            st.session_state[msg_key] = initialise_agent("TARKA", ctx)

    if agent_key == "RUPAK":
        if not st.session_state.get("agent_completed", {}).get("TARKA"):
            st.warning("⚠️ Complete your argumentation with **Tarka AI** first to unlock Rupak.")
            if st.button("Go to Tarka AI"):
                st.session_state.current_tab = "⚖️ तर्क (Tarka) AI"
                st.rerun()
            return
        # First visit: initialise Rupak
        if st.session_state.get(msg_key) is None:
            rep = st.session_state.get("current_rep_level", "macroscopic level")
            ctx = {**st.session_state.get("agent_context", {}), "rep_level": rep}
            st.session_state[msg_key] = initialise_agent("RUPAK", ctx)

    messages = st.session_state.get(msg_key, [])

    # ── Post-mastery / post-completion forms ───────────────────────────────────
    completed = st.session_state.get("agent_completed", {})
    if agent_key == "SAATHI" and st.session_state.get('mastery_triggered'):
        st.balloons()
        render_revision_form(uid, group, module)
        return

    if agent_key == "TARKA" and completed.get("TARKA"):
        st.success("✅ Argumentation complete! Rupak AI is now unlocked.")
        tap = st.session_state.get("current_tap_level", "unknown")
        st.info(f"Your final argumentation level: **{tap}**")
        if st.button("Continue to Rupak AI →"):
            st.session_state.current_tab = "🧬 रूपक (Rupak) AI"
            st.rerun()
        return

    if agent_key == "RUPAK" and completed.get("RUPAK"):
        st.success("🎉 Representational fluency achieved! Your learning ecology journey is complete.")
        rep = st.session_state.get("current_rep_level", "unknown")
        st.info(f"Your representational level: **{rep}**")
        return

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_phenom, col_chat = st.columns([1, 1.5], gap="large")

    with col_phenom:
        st.markdown("### 📝 Current Concept")
        with st.container(border=True):
            st.subheader(module.get('Sub_Title', ''))
            st.write(f"**Q:** {module.get('Diagnostic_Question', '')}")
            st.write("---")
            opts = "\n\n".join([
                f"A) {module.get('Option_A', '')}",
                f"B) {module.get('Option_B', '')}",
                f"C) {module.get('Option_C', '')}",
                f"D) {module.get('Option_D', '')}",
            ])
            st.write(opts)

        # Research instrument badge
        with st.container(border=True):
            st.caption("🔬 Research Instrument")
            st.markdown(f"**{agent['instrument']}**")
            if agent_key == "TARKA":
                tap = st.session_state.get("current_tap_level", "TAP_1")
                st.metric("Current TAP Level", tap)
            if agent_key == "RUPAK":
                rep = st.session_state.get("current_rep_level", "MONADIC")
                st.metric("Representational Level", rep)

    with col_chat:
        st.subheader(f"{agent['icon']} {agent['name']}")
        st.caption(f"Role: {agent['role']} | Practice: {agent['practice']}")

        # Display conversation (skip system prompt)
        for m in messages[1:]:
            with st.chat_message(m["role"]):
                # Clean signal codes from display
                display_content = m["content"]
                for code in [
                    "[MASTERY_DETECTED]", "[TAP_LEVEL_5_DETECTED]",
                    "[TAP_LEVEL_4_DETECTED]", "[TAP_LEVEL_3_DETECTED]",
                    "[TAP_LEVEL_2_DETECTED]", "[TAP_LEVEL_1_DETECTED]",
                    "[TRIADIC_FLUENCY_DETECTED]", "[BIADIC_REPRESENTATION_DETECTED]",
                    "[MONADIC_CONFINEMENT_DETECTED]", "[REDIRECT_TO_TARKA]",
                    "[REDIRECT_TO_RUPAK]", "[REDIRECT_TO_SAATHI]",
                ]:
                    display_content = display_content.replace(code, "")
                st.markdown(display_content.strip())

        # Chat input
        placeholder = {
            "SAATHI": "Explain your thinking to Saathi...",
            "TARKA":  "State your claim, evidence, or reasoning to Tarka...",
            "RUPAK":  "Describe what you observe or imagine at the molecular level...",
        }.get(agent_key, "Type your response...")

        if prompt := st.chat_input(placeholder):
            messages.append({"role": "user", "content": prompt})

            with st.spinner(f"{agent['icon']} {agent['nepali_name']} AI is analysing..."):
                result = call_agent(
                    agent_key = agent_key,
                    messages  = messages,
                    api_key   = st.secrets["OPENAI_API_KEY"],
                )

            ai_content = result["content"]
            messages.append({"role": "assistant", "content": ai_content})
            st.session_state[msg_key] = messages

            topic = module.get('Sub_Title', 'Unknown')

            # ── Log student turn ──────────────────────────────────────────────
            log_temporal_trace(
                uid, agent["db_log_type"],
                f"Topic:{topic}|Agent:{agent_key}|Turn:STUDENT|Msg:{prompt}"
            )

            # ── Log AI turn with research signals ─────────────────────────────
            tap_signal = f"|TAP:{result['tap_level']}" if result["tap_level"] else ""
            rep_signal = f"|REP:{result['rep_level']}" if result["rep_level"] else ""
            log_temporal_trace(
                uid, agent["db_log_type"],
                f"Topic:{topic}|Agent:{agent_key}|Turn:AI"
                f"{tap_signal}{rep_signal}|Msg:{ai_content}"
            )

            # ── Update research state ─────────────────────────────────────────
            if result["tap_level"]:
                st.session_state.current_tap_level = result["tap_level"]
            if result["rep_level"]:
                st.session_state.current_rep_level = result["rep_level"]

            # ── Handle agent-specific completion signals ───────────────────────
            if agent_key == "SAATHI" and result["mastery"]:
                completed_agents = st.session_state.get("agent_completed", {})
                completed_agents["SAATHI"] = True
                st.session_state.agent_completed = completed_agents
                st.session_state.mastery_triggered = True

            if agent_key == "TARKA":
                tap = result.get("tap_level")
                if tap in ("TAP_3", "TAP_4", "TAP_5"):
                    completed_agents = st.session_state.get("agent_completed", {})
                    completed_agents["TARKA"] = True
                    st.session_state.agent_completed = completed_agents
                    # Log argumentation completion to database
                    log_assessment(
                        uid, group, topic,
                        "N/A", "N/A",
                        f"Argumentation completed at {tap}",
                        "N/A", f"TAP_COMPLETE_{tap}", get_nepal_time()
                    )

            if agent_key == "RUPAK":
                if result.get("triadic"):
                    completed_agents = st.session_state.get("agent_completed", {})
                    completed_agents["RUPAK"] = True
                    st.session_state.agent_completed = completed_agents
                    # Log modelling completion to database
                    log_assessment(
                        uid, group, topic,
                        "N/A", "N/A",
                        "Representational fluency achieved: TRIADIC",
                        "N/A", "TRIADIC_COMPLETE", get_nepal_time()
                    )

            # ── Handle redirect protocol ──────────────────────────────────────
            redirect = result.get("redirect")
            if redirect:
                redirect_map = {
                    "TARKA":  "⚖️ तर्क (Tarka) AI",
                    "RUPAK":  "🧬 रूपक (Rupak) AI",
                    "SAATHI": "🤖 साथी (Saathi) AI",
                }
                target_tab = redirect_map.get(redirect)
                if target_tab:
                    st.info(f"🔄 Redirecting you to {AGENTS[redirect]['name']}...")
                    st.session_state.current_tab = target_tab
                    st.rerun()

            st.rerun()

# ── Tier 5 & 6 revision form (UNCHANGED from original) ────────────────────────

def render_revision_form(uid, group, module):
    st.success("🌟 Mastery Detected! / अवधारणा स्पष्ट भयो।")
    with st.form("t56_form"):
        st.markdown("### Final Assessment (Tiers 5 & 6)")
        opts = [module['Option_A'], module['Option_B'],
                module['Option_C'], module['Option_D']]
        t5 = st.radio("Final Choice (Tier 5):", opts)
        t6 = st.select_slider(
            "Final Confidence (Tier 6):", ["Guessing", "Unsure", "Sure", "Very Sure"]
        )
        reflection = st.text_area("What changed in your thinking?")

        if st.form_submit_button("Save & Continue to Tarka AI"):
            log_assessment(
                uid, group, module['Sub_Title'],
                "N/A", "N/A", reflection, "N/A",
                "POST", get_nepal_time(), t5, t6
            )
            st.session_state.mastery_triggered = False
            st.session_state.current_tab = "⚖️ तर्क (Tarka) AI"
            st.rerun()

# ── Progress dashboard ────────────────────────────────────────────────────────

def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress Dashboard)")
    st.markdown("---")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if log_df.empty:
            st.info("No data yet. Start a learning module to see your progress!")
            return

        user_data = log_df[
            log_df['User_ID'].astype(str).str.upper() == uid.upper()
        ].copy()

        if user_data.empty:
            st.info("Complete your first module to unlock analytics.")
            return

        # ── Top metrics ────────────────────────────────────────────────────────
        total     = len(user_data)
        mastered  = len(user_data[user_data['Status'] == 'POST'])
        tap_rows  = user_data[user_data['Status'].str.startswith('TAP_COMPLETE', na=False)]
        rep_rows  = user_data[user_data['Status'] == 'TRIADIC_COMPLETE']

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Modules Explored",       total)
        m2.metric("Concepts Mastered",      mastered)
        m3.metric("Arguments Completed",    len(tap_rows))
        m4.metric("Models Completed",       len(rep_rows))

        # ── Confidence evolution (original chart preserved) ────────────────────
        st.markdown("### 🧬 Conceptual Growth Analysis")
        conf_map  = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
        plot_data = []

        for mod in user_data['Module_ID'].unique():
            mod_rows = user_data[user_data['Module_ID'] == mod]
            initial  = mod_rows[mod_rows['Status'] == 'INITIAL']
            post     = mod_rows[mod_rows['Status'] == 'POST']
            if not initial.empty and not post.empty:
                plot_data.append({
                    "Module": mod, "Stage": "Before Saathi",
                    "Confidence": conf_map.get(initial.iloc[0].get('T2', 'Guessing'), 1)
                })
                plot_data.append({
                    "Module": mod, "Stage": "After Saathi",
                    "Confidence": conf_map.get(post.iloc[0].get('T6', 'Guessing'), 1)
                })

        if plot_data:
            df_viz = pd.DataFrame(plot_data)
            fig    = px.line(
                df_viz, x="Stage", y="Confidence", color="Module",
                markers=True, title="Confidence Gain per Concept (Saathi)",
                labels={"Confidence": "Certainty Level (1-4)"}
            )
            fig.update_layout(yaxis=dict(
                tickmode='array', tickvals=[1, 2, 3, 4],
                ticktext=["Guessing", "Unsure", "Sure", "Very Sure"]
            ))
            st.plotly_chart(fig, use_container_width=True)

        # ── Argumentation progress ─────────────────────────────────────────────
        if not tap_rows.empty:
            st.markdown("### ⚖️ Argumentation Progress (Tarka AI)")
            tap_display = tap_rows[['Timestamp', 'Module_ID', 'Status', 'T3']].copy()
            tap_display.columns = ["Time", "Concept", "TAP Level", "Reflection"]
            st.dataframe(tap_display, use_container_width=True, hide_index=True)

        # ── Learning journal ───────────────────────────────────────────────────
        st.markdown("### 📝 Learning Journal")
        display_df = user_data[['Timestamp', 'Module_ID', 'Status', 'T1', 'T5']].sort_values(
            by='Timestamp', ascending=False
        )
        display_df.columns = ["Time", "Concept", "Phase", "Initial Choice", "Final Choice"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
