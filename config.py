"""
config.py — MMALE Research Configuration
==========================================
Central configuration for:
  1. Research group definitions and agent access rules
  2. Trilingual language management (English / Nepali / Korean)
  3. Group-aware agent unlock logic

RESEARCH GROUPS:
  CON   — Control group: no AI agents, standard instruction only
  SA    — Single Agent: Saathi only (diagnostic + Socratic)
  MA    — Multiple Agents: Saathi + Tarka + Rupak (text-based)
  MMALE — Full Ecology: all 6 agents + multimodal capability

LANGUAGE POLICY:
  The system is used by Nepali students and supervised by Korean
  professors. Rather than forcing a single language, the system
  detects the user's role and preferred language, defaulting to
  English + Nepali for students and English + Korean for supervisors.
  Students may toggle their preferred language from the sidebar.
  AI agents respond in the student's chosen language automatically
  via their system prompts.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCH GROUP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Group codes used throughout the system
GROUPS = {
    "CON": {
        "label":        "Control Group (CON)",
        "description":  "Standard classroom instruction — no AI agent access",
        "agents":       [],          # empty = no agent access
        "multimodal":   False,
        "color":        "#d62728",
    },
    "SA": {
        "label":        "Single Agent (SA)",
        "description":  "Saathi AI only — diagnostic and Socratic misconception correction",
        "agents":       ["SAATHI"],
        "multimodal":   False,
        "color":        "#ff7f0e",
    },
    "MA": {
        "label":        "Multiple Agents (MA)",
        "description":  "Saathi + Tarka + Rupak — argumentation and modelling",
        "agents":       ["SAATHI", "TARKA", "RUPAK"],
        "multimodal":   False,
        "color":        "#1f77b4",
    },
    "MMALE": {
        "label":        "Full MMALE Ecology",
        "description":  "All 6 agents + multimodal image input (Rupak vision)",
        "agents":       ["SAATHI", "KHOJI", "PRAMAN", "TARKA", "RUPAK", "SANDESH"],
        "multimodal":   True,
        "color":        "#2ca02c",
    },
}

def get_group_config(group_code: str) -> dict:
    """Returns config for a group code. Defaults to CON if unknown."""
    return GROUPS.get(str(group_code).upper().strip(), GROUPS["CON"])

def get_accessible_agents(group_code: str) -> list:
    """Returns list of agent keys accessible to a research group."""
    return get_group_config(group_code)["agents"]

def agent_accessible(agent_key: str, group_code: str) -> bool:
    """True if the given agent is accessible to the given group."""
    return agent_key in get_accessible_agents(group_code)

def is_multimodal(group_code: str) -> bool:
    """True if the group has multimodal (image) capability."""
    return get_group_config(group_code)["multimodal"]

def is_control(group_code: str) -> bool:
    """True if the group is CON (no AI access)."""
    return str(group_code).upper().strip() == "CON"

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DISTRIBUTION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

# Rationale for load distribution across 4 groups:
# - CON:   ~25% of students — baseline comparison, minimal system load
# - SA:    ~25% — one API call per turn (Saathi only)
# - MA:    ~25% — up to 3 API calls per topic (Saathi → Tarka → Rupak)
# - MMALE: ~25% — up to 6 API calls per topic + vision calls for Rupak
#
# API cost estimate per student per topic:
# CON:   $0.00 (no API calls)
# SA:    ~$0.02–0.05 (5–15 Saathi turns × ~$0.003/call)
# MA:    ~$0.06–0.15 (combined Saathi + Tarka + Rupak sessions)
# MMALE: ~$0.10–0.25 (all 6 agents; Rupak vision adds ~$0.01/image)
#
# Recommendation: duplicate each group across 2 classes (as per PhD
# methodology) giving ~80 students total, ~20 per group.

AGENT_MENU_ICONS = {
    "SAATHI":  ("🔬", "साथी (Saathi) AI"),
    "KHOJI":   ("🔭", "खोजी (Khoji) AI"),
    "PRAMAN":  ("🧪", "प्रमाण (Praman) AI"),
    "TARKA":   ("⚖️", "तर्क (Tarka) AI"),
    "RUPAK":   ("🧬", "रूपक (Rupak) AI"),
    "SANDESH": ("📝", "सन्देश (Sandesh) AI"),
}

def build_student_menu(group_code: str) -> list:
    """
    Builds the navigation menu for a student based on their group.
    CON students see no agent tabs.
    Other groups see only their accessible agents.
    """
    accessible = get_accessible_agents(group_code)
    menu = ["🏠 Dashboard", "📚 Learning Modules"]
    for key in ["SAATHI", "KHOJI", "PRAMAN", "TARKA", "RUPAK", "SANDESH"]:
        if key in accessible:
            icon, name = AGENT_MENU_ICONS[key]
            menu.append(f"{icon} {name}")
    menu.append("📈 My Progress")
    return menu

# ═══════════════════════════════════════════════════════════════════════════════
# TRILINGUAL LANGUAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# UI strings in all three languages
# Format: UI_STRINGS[key][language_code]
# Language codes: "en" (English), "ne" (Nepali), "ko" (Korean)

UI_STRINGS = {
    # Navigation
    "dashboard":        {"en": "🏠 Dashboard",
                         "ne": "🏠 ड्यासबोर्ड",
                         "ko": "🏠 대시보드"},
    "learning_modules": {"en": "📚 Learning Modules",
                         "ne": "📚 सिकाइ मोड्युलहरू",
                         "ko": "📚 학습 모듈"},
    "my_progress":      {"en": "📈 My Progress",
                         "ne": "📈 मेरो प्रगति",
                         "ko": "📈 나의 진도"},
    "logout":           {"en": "Logout",
                         "ne": "बाहिरिनुहोस्",
                         "ko": "로그아웃"},
    "login":            {"en": "Login",
                         "ne": "लगइन",
                         "ko": "로그인"},

    # Student portal messages
    "namaste":          {"en": "Welcome",
                         "ne": "नमस्ते",
                         "ko": "환영합니다"},
    "submit_answer":    {"en": "Submit & Start Discussion",
                         "ne": "पेश गर्नुहोस् र छलफल सुरु गर्नुहोस्",
                         "ko": "제출하고 토론 시작하기"},
    "reasoning_prompt": {"en": "Why did you choose this answer? (Tier 3 Reasoning):",
                         "ne": "तपाईंले यो उत्तर किन रोज्नुभयो? (तह ३ तर्क):",
                         "ko": "왜 이 답을 선택했나요? (3단계 추론):"},
    "confidence_label": {"en": "Confidence in your answer (Tier 2):",
                         "ne": "आत्मविश्वास (तह २):",
                         "ko": "답에 대한 자신감 (2단계):"},
    "confidence_opts":  {"en": ["Guessing", "Unsure", "Sure", "Very Sure"],
                         "ne": ["अनुमान", "अनिश्चित", "निश्चित", "एकदम निश्चित"],
                         "ko": ["추측", "불확실", "확실", "매우 확실"]},

    # Control group message
    "con_message":      {"en": "Your class is using standard learning materials. "
                               "Complete the diagnostic question below.",
                         "ne": "तपाईंको कक्षाले मानक सिकाइ सामग्री प्रयोग गर्दैछ। "
                               "तलको निदानात्मक प्रश्न पूरा गर्नुहोस्।",
                         "ko": "귀하의 수업은 표준 학습 자료를 사용합니다. "
                               "아래 진단 문제를 완성하세요."},

    # Research group labels
    "group_label":      {"en": "Research Group",
                         "ne": "अनुसन्धान समूह",
                         "ko": "연구 그룹"},

    # Agent roles
    "agent_saathi_role":  {"en": "Diagnostic Agent",
                           "ne": "निदानात्मक एजेन्ट",
                           "ko": "진단 에이전트"},
    "agent_khoji_role":   {"en": "Inquiry Agent",
                           "ne": "अनुसन्धान एजेन्ट",
                           "ko": "탐구 에이전트"},
    "agent_praman_role":  {"en": "Evidence Agent",
                           "ne": "प्रमाण एजेन्ट",
                           "ko": "증거 에이전트"},
    "agent_tarka_role":   {"en": "Argumentation Agent",
                           "ne": "तर्क एजेन्ट",
                           "ko": "논증 에이전트"},
    "agent_rupak_role":   {"en": "Modelling Agent",
                           "ne": "मोडेलिङ एजेन्ट",
                           "ko": "모델링 에이전트"},
    "agent_sandesh_role": {"en": "Communication Agent",
                           "ne": "सञ्चार एजेन्ट",
                           "ko": "의사소통 에이전트"},

    # Mastery messages
    "mastery_detected": {"en": "🌟 Mastery Detected! Concept understood.",
                         "ne": "🌟 दक्षता पत्ता लागेको छ! अवधारणा बुझ्नुभयो।",
                         "ko": "🌟 숙달 감지됨! 개념을 이해했습니다."},
    "ecology_complete": {"en": "🎓 Full Ecology Complete! Outstanding scientific reasoning.",
                         "ne": "🎓 पूर्ण पारिस्थितिकी पूरा! उत्कृष्ट वैज्ञानिक तर्क।",
                         "ko": "🎓 전체 생태계 완성! 뛰어난 과학적 추론입니다."},

    # Researcher portal
    "pi_dashboard":     {"en": "PhD Principal Investigator Dashboard",
                         "ne": "पीएचडी मुख्य अन्वेषक ड्यासबोर्ड",
                         "ko": "박사과정 주임 연구원 대시보드"},
    "live_monitor":     {"en": "Live Study Monitor",
                         "ne": "लाइभ अध्ययन मनिटर",
                         "ko": "실시간 연구 모니터"},
}

def t(key: str, lang: str = "en") -> str:
    """
    Translate a UI string key to the given language.
    Falls back to English if key or language not found.

    Usage:
        from config import t
        st.write(t("namaste", lang))
    """
    return UI_STRINGS.get(key, {}).get(lang, UI_STRINGS.get(key, {}).get("en", key))

def get_language(user: dict = None) -> str:
    """
    Determines the active language from session state or user role.

    Priority:
      1. st.session_state.language (user toggled in sidebar)
      2. Role-based default:
           Researcher/Supervisor → "en" (English, for Korean supervisors
           the portal text is in English; Korean used in specific labels)
           Teacher → "en" + Nepali agent prompts
           Student → "ne" (Nepali default, can switch)
      3. Default: "en"
    """
    import streamlit as st
    if "language" in st.session_state:
        return st.session_state.language
    if user:
        role = str(user.get("Role", "Student")).strip()
        if role in ["Researcher", "Supervisor", "Admin"]:
            return "en"
    return "ne"   # default to Nepali for students

def render_language_selector(sidebar: bool = True):
    """
    Renders a language selector widget.
    Stores selection in st.session_state.language.

    Design rationale: rather than forcing one language, students choose.
    This respects linguistic autonomy and is itself a culturally sensitive
    design feature — aligning with the middle-path approach from Phase 0.
    """
    import streamlit as st
    options = {"English": "en", "नेपाली": "ne", "한국어": "ko"}
    labels  = list(options.keys())

    # Current selection
    current = st.session_state.get("language", "ne")
    current_label = next((k for k, v in options.items() if v == current), "English")

    if sidebar:
        selected = st.sidebar.selectbox(
            "🌐 Language / भाषा / 언어",
            labels,
            index=labels.index(current_label),
            key="lang_selector",
        )
    else:
        selected = st.selectbox(
            "🌐 Language / भाषा / 언어",
            labels,
            index=labels.index(current_label),
            key="lang_selector",
        )

    st.session_state.language = options[selected]
    return options[selected]

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT SYSTEM PROMPT LANGUAGE INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

LANGUAGE_INSTRUCTION = {
    "en": "Respond in English only.",
    "ne": "Respond in Nepali (Devanagari script preferred, Romanised acceptable) "
          "unless the student writes in English, in which case use English.",
    "ko": "Respond in Korean (한국어) unless the student writes in English or Nepali.",
}

def inject_language(system_prompt: str, lang: str) -> str:
    """
    Appends a language instruction to any agent system prompt.
    Called in call_agent() before sending to OpenAI.
    """
    instruction = LANGUAGE_INSTRUCTION.get(lang, LANGUAGE_INSTRUCTION["en"])
    return system_prompt + f"\n\nLANGUAGE INSTRUCTION: {instruction}"
