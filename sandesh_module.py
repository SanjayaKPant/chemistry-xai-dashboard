"""
sandesh_module.py — Sandesh Open-Response Assessment Module
============================================================
Implements the corrected response collection system for Sandesh
questions (Q15, Q16, Q18) that require constructed responses
rather than multiple-choice answers.

WHY THIS IS A SEPARATE MODULE (JOST reviewer justification):
Sandesh questions assess science communication competence —
a construct that requires constructed responses evaluated against
a rubric, not answer-key matching. Using the standard Tier 1-6
multiple-choice system for these items would:
  (1) produce meaningless "Incorrect" results in Assessment_Logs
  (2) confound confidence-in-selection with confidence-in-composition
  (3) make inter-rater reliability impossible without rubric anchors

This module implements the correct design:
  DRAFT → Sandesh AI interaction → REVISED → Rubric-scored

Also contains the post-study reflection survey (Q18 part d)
administered AFTER all in-system data collection is complete.

Data streams produced:
  OpenResponse sheet   — draft + revised text with word counts
  ReflectionSurvey sheet — post-study AI perception items
"""

import streamlit as st
from database_manager import (
    log_open_response, log_reflection_survey, get_nepal_time,
)
from agents import initialise_agent, call_agent, ALL_SIGNAL_CODES

# ── Rubric definitions (for researcher coding, displayed to student) ──────────

SANDESH_RUBRICS = {
    "Q15_analogy_communication": {
        "title": "Q15 — Audience-Adapted Science Communication",
        "criteria": [
            {
                "label": "Scientific Accuracy",
                "levels": {
                    0: "Contains significant factual errors about alkali metal reactivity",
                    1: "Mostly accurate but missing the mechanism (shielding/IE)",
                    2: "Accurate and includes the electron-loss mechanism",
                    3: "Accurate, mechanistic, and precisely linked to evidence",
                },
            },
            {
                "label": "Analogy Quality",
                "levels": {
                    0: "No analogy used, or analogy is misleading",
                    1: "Analogy present but weakly connected to the chemistry",
                    2: "Analogy clearly represents electron loss / distance from nucleus",
                    3: "Analogy is original, accurate, and would be understood by Year 9",
                },
            },
            {
                "label": "Audience Appropriateness",
                "levels": {
                    0: "Uses technical terminology without explanation",
                    1: "Avoids jargon but oversimplifies to the point of inaccuracy",
                    2: "Accessible language that preserves scientific accuracy",
                    3: "Engaging, grade-appropriate, and scientifically complete",
                },
            },
        ],
        "max_score": 9,
    },
    "Q16_bilingual_summary": {
        "title": "Q16 — Bilingual One-Sentence Scientific Summary",
        "criteria": [
            {
                "label": "English Completeness (Claim + Mechanism + Evidence)",
                "levels": {
                    0: "Missing two or more components",
                    1: "Claim only or claim + evidence without mechanism",
                    2: "Claim + mechanism OR claim + evidence (not both)",
                    3: "Claim + mechanism + evidence with correct IE values (418/496)",
                },
            },
            {
                "label": "Nepali Translation Quality",
                "levels": {
                    0: "No Nepali attempt or completely inaccurate",
                    1: "Partial Nepali attempt with significant gaps",
                    2: "Accurate Nepali summary using common vocabulary",
                    3: "Accurate Nepali summary using scientific vocabulary "
                       "(आयनीकरण ऊर्जा, इलेक्ट्रोन परिरक्षण)",
                },
            },
            {
                "label": "Scientific Vocabulary (both languages)",
                "levels": {
                    0: "No scientific vocabulary in either language",
                    1: "Some English scientific terms but no Nepali equivalents",
                    2: "Correct English scientific terms; attempts Nepali equivalents",
                    3: "Precise scientific vocabulary in both English and Nepali",
                },
            },
        ],
        "max_score": 9,
    },
    "Q18_synthesis": {
        "title": "Q18 — Full Synthesis Paragraph (parts a–c only)",
        "criteria": [
            {
                "label": "(a) Conceptual Change — What did you learn?",
                "levels": {
                    0: "Vague ('I learned more about chemistry') or absent",
                    1: "Names a topic but not a specific conceptual shift",
                    2: "Identifies a specific misconception that changed",
                    3: "Articulates the shift from performance to understanding "
                       "(e.g., 'I used to think mass determined reactivity; now I understand shielding')",
                },
            },
            {
                "label": "(b) Key Evidence — What changed your thinking?",
                "levels": {
                    0: "No specific evidence cited",
                    1: "Vague reference ('the data showed...')",
                    2: "Specific evidence cited (e.g., ionisation energies)",
                    3: "Specific evidence + explanation of why it was convincing",
                },
            },
            {
                "label": "(c) Further Investigation — Generative question",
                "levels": {
                    0: "No further question proposed",
                    1: "Descriptive question ('What else can K react with?')",
                    2: "Causal question about the same phenomenon",
                    3: "Novel causal question that extends beyond the topic "
                       "(e.g., 'How does shielding work differently in transition metals?')",
                },
            },
        ],
        "max_score": 9,
    },
}

# ── Stimulus data (ionisation energies — provided to ALL groups) ───────────────

IONISATION_ENERGY_STIMULUS = """
**Data provided for this task** (source: NIST Chemistry WebBook):

| Element | Ionisation Energy (kJ/mol) | Atomic Radius (pm) |
|---------|--------------------------|-------------------|
| Li (Z=3)  | 520 | 152 |
| Na (Z=11) | 496 | 186 |
| K (Z=19)  | 418 | 227 |
| Rb (Z=37) | 403 | 248 |
| Cs (Z=55) | 376 | 265 |
"""

# ── Main Sandesh assessment renderer ─────────────────────────────────────────

def render_sandesh_open_response(uid: str, group: str,
                                  module: dict, lang: str = "ne"):
    """
    Renders the open-response assessment for Sandesh questions.
    Replaces the standard Tier 1-6 multiple-choice system for
    communication and synthesis items.

    Structure:
      1. Show stimulus material (data table)
      2. Collect DRAFT response (before AI)
      3. Sandesh AI interaction
      4. Collect REVISED response (after AI)
      5. Show rubric for self-assessment
    """
    topic = module.get("Sub_Title", "Alkali Metals")

    # Determine which question variant this module is
    sub_title = str(module.get("Sub_Title", "")).lower()
    if "q15" in sub_title or "analogy" in sub_title or "audience" in sub_title:
        q_variant = "Q15"
        rubric_key = "Q15_analogy_communication"
    elif "q16" in sub_title or "bilingual" in sub_title:
        q_variant = "Q16"
        rubric_key = "Q16_bilingual_summary"
    else:
        q_variant = "Q18"
        rubric_key = "Q18_synthesis"

    rubric = SANDESH_RUBRICS[rubric_key]

    # ── Column layout ─────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1.5], gap="large")

    with col_left:
        st.markdown("### 📝 Task")
        with st.container(border=True):
            st.markdown(f"**{module.get('Diagnostic_Question', '')}**")

        # Always show ionisation energy stimulus
        with st.expander("📊 Data Table (available for all groups)", expanded=True):
            st.markdown(IONISATION_ENERGY_STIMULUS)

        # Show rubric
        with st.expander("📋 Scoring Rubric", expanded=False):
            st.markdown(f"**{rubric['title']}**")
            st.caption(f"Maximum score: {rubric['max_score']} points")
            for criterion in rubric['criteria']:
                st.markdown(f"**{criterion['label']}**")
                for score, desc in criterion['levels'].items():
                    color = ['🔴', '🟡', '🟢', '🌟'][score]
                    st.write(f"{color} {score}pt: {desc}")
                st.markdown("---")

    with col_right:
        phase = st.session_state.get(f"sandesh_phase_{q_variant}", "DRAFT")
        sandesh_msgs = st.session_state.get("sandesh_messages", [])
        sandesh_completed = st.session_state.get(
            "agent_completed", {}
        ).get("SANDESH", False)

        # ── Phase 1: DRAFT ────────────────────────────────────────────────────
        if phase == "DRAFT":
            if lang == "ko":
                st.subheader("📝 초안 작성 (AI 전)")
                draft_label = "여기에 답변을 작성하세요:"
                rating_label = "답변의 완성도는? (1=매우 미완성, 4=완성)"
                submit_label = "초안 저장 후 Sandesh AI와 대화 시작"
            elif lang == "ne":
                st.subheader("📝 मस्यौदा लेख्नुहोस् (AI अघि)")
                draft_label = "यहाँ आफ्नो उत्तर लेख्नुहोस्:"
                rating_label = "तपाईंको उत्तर कति पूर्ण छ? (१=धेरै अपूर्ण, ४=पूर्ण)"
                submit_label = "मस्यौदा सुरक्षित गर्नुहोस् र Sandesh AI सुरु गर्नुहोस्"
            else:
                st.subheader("📝 Write Your Draft (Before AI)")
                draft_label = "Write your response here:"
                rating_label = "How complete is your response? (1=very incomplete, 4=complete)"
                submit_label = "Save Draft and Start Sandesh AI Discussion"

            st.info(
                "Write your BEST response before talking to Sandesh AI. "
                "This is your baseline — be honest about what you currently know."
                if lang == "en" else
                "Sandesh AI सँग कुरा गर्नु अघि आफ्नो उत्तम उत्तर लेख्नुहोस्। "
                "यो तपाईंको आधाररेखा हो।"
            )

            draft_text = st.text_area(
                draft_label,
                height=200,
                key=f"sandesh_draft_{q_variant}",
                placeholder=(
                    "Write 3-5 sentences. Include: what happens, why it happens, "
                    "evidence with numbers, and an analogy for a younger student."
                    if q_variant == "Q15" else
                    "Write in BOTH English and Nepali. Include: claim + mechanism + evidence."
                    if q_variant == "Q16" else
                    "Write 150-200 words covering: (a) what you now understand, "
                    "(b) what changed your thinking, (c) what you still want to investigate."
                ),
            )

            self_rating_draft = st.select_slider(
                rating_label,
                options=[1, 2, 3, 4],
                value=2,
                format_func=lambda x: {
                    1: "1 — Very incomplete",
                    2: "2 — Partial",
                    3: "3 — Mostly complete",
                    4: "4 — Complete",
                }.get(x, str(x)),
                key=f"sandesh_self_rating_draft_{q_variant}",
            )

            if st.button(submit_label, type="primary"):
                if len(draft_text.strip()) < 20:
                    st.error(
                        "Please write at least a few sentences before continuing."
                        if lang == "en" else
                        "कृपया जारी राख्नु अघि केही वाक्य लेख्नुहोस्।"
                    )
                else:
                    log_open_response(
                        uid=uid, group=group, module_id=topic,
                        item_num=int(q_variant[1:]),
                        phase="DRAFT",
                        response_text=draft_text,
                        self_rating=self_rating_draft,
                        timestamp=get_nepal_time(),
                    )
                    # Initialise Sandesh AI with the draft as context
                    context = {
                        **st.session_state.get("agent_context", {}),
                        "lang": lang,
                        "student_draft": draft_text,
                    }
                    st.session_state["sandesh_messages"] = initialise_agent(
                        "SANDESH", context
                    )
                    # Inject draft into first message
                    if st.session_state["sandesh_messages"]:
                        st.session_state["sandesh_messages"].append({
                            "role": "user",
                            "content": (
                                f"Here is my draft response:\n\n{draft_text}\n\n"
                                "Please help me improve it."
                            ),
                        })
                    st.session_state[f"sandesh_phase_{q_variant}"] = "AI_DISCUSSION"
                    st.rerun()

        # ── Phase 2: AI DISCUSSION ────────────────────────────────────────────
        elif phase == "AI_DISCUSSION":
            st.subheader("🤖 Sandesh AI Discussion")
            st.caption(
                "Discuss your draft with Sandesh. When you are ready to write "
                "your final version, click 'Write Final Response'."
                if lang == "en" else
                "Sandesh सँग आफ्नो मस्यौदा छलफल गर्नुहोस्।"
            )

            for m in sandesh_msgs[1:]:
                content = m.get("content", "")
                for code in ALL_SIGNAL_CODES:
                    content = content.replace(code, "")
                with st.chat_message(m["role"]):
                    st.markdown(content.strip())

            placeholder = (
                "Ask Sandesh for feedback on your draft..."
                if lang == "en" else
                "Sandesh लाई आफ्नो मस्यौदामा प्रतिक्रियाको लागि सोध्नुहोस्..."
            )

            if prompt := st.chat_input(placeholder):
                sandesh_msgs.append({"role": "user", "content": prompt})
                with st.spinner("📝 Sandesh AI is reviewing..."):
                    result = call_agent(
                        agent_key="SANDESH",
                        messages=sandesh_msgs,
                        api_key=st.secrets["OPENAI_API_KEY"],
                    )
                ai_content = result["content"]
                sandesh_msgs.append({"role": "assistant", "content": ai_content})
                st.session_state["sandesh_messages"] = sandesh_msgs

                from database_manager import log_temporal_trace
                log_temporal_trace(uid, "SANDESH_OPEN_CHAT",
                    f"Topic:{topic}|Q:{q_variant}|Student:{prompt[:200]}")
                log_temporal_trace(uid, "SANDESH_OPEN_CHAT",
                    f"Topic:{topic}|Q:{q_variant}|"
                    f"COMM:{result.get('comm_level','?')}|AI:{ai_content[:200]}")
                st.rerun()

            if st.button("✍️ Write My Final Response →", type="secondary"):
                st.session_state[f"sandesh_phase_{q_variant}"] = "REVISED"
                st.rerun()

        # ── Phase 3: REVISED RESPONSE ─────────────────────────────────────────
        elif phase == "REVISED":
            if lang == "ko":
                st.subheader("✅ 최종 답변 (AI 후)")
                revised_label = "AI와 대화 후 수정된 답변:"
                rating_label  = "수정 후 완성도는?"
                change_label  = "무엇을 바꿨나요? 왜 바꿨나요?"
                submit_label  = "최종 답변 저장"
            elif lang == "ne":
                st.subheader("✅ अन्तिम उत्तर (AI पछि)")
                revised_label = "AI सँग छलफल पछि परिमार्जित उत्तर:"
                rating_label  = "परिमार्जन पछि पूर्णता?"
                change_label  = "तपाईंले के परिवर्तन गर्नुभयो र किन?"
                submit_label  = "अन्तिम उत्तर सुरक्षित गर्नुहोस्"
            else:
                st.subheader("✅ Final Response (After AI)")
                revised_label = "Write your revised response after the AI discussion:"
                rating_label  = "How complete is your revised response?"
                change_label  = "What did you change from your draft, and why?"
                submit_label  = "Save Final Response"

            revised_text = st.text_area(
                revised_label,
                height=200,
                key=f"sandesh_revised_{q_variant}",
            )

            self_rating_rev = st.select_slider(
                rating_label,
                options=[1, 2, 3, 4],
                value=3,
                format_func=lambda x: {
                    1: "1 — Very incomplete",
                    2: "2 — Partial",
                    3: "3 — Mostly complete",
                    4: "4 — Complete",
                }.get(x, str(x)),
                key=f"sandesh_self_rating_rev_{q_variant}",
            )

            change_reflection = st.text_area(
                change_label,
                height=80,
                key=f"sandesh_change_{q_variant}",
                placeholder="e.g. I added the ionisation energy numbers and changed my analogy to be clearer...",
            )

            if st.form_submit_button if False else st.button(submit_label, type="primary"):
                if len(revised_text.strip()) < 20:
                    st.error("Please write your revised response before saving.")
                else:
                    log_open_response(
                        uid=uid, group=group, module_id=topic,
                        item_num=int(q_variant[1:]),
                        phase="REVISED",
                        response_text=revised_text + " | CHANGE: " + change_reflection,
                        self_rating=self_rating_rev,
                        timestamp=get_nepal_time(),
                    )
                    completed = st.session_state.get("agent_completed", {})
                    completed["SANDESH"] = True
                    st.session_state.agent_completed = completed
                    st.session_state[f"sandesh_phase_{q_variant}"] = "COMPLETE"

                    from database_manager import log_assessment
                    log_assessment(
                        uid, group, topic,
                        "N/A", "N/A",
                        f"Communication complete: {q_variant}",
                        "N/A", "ECOLOGY_COMPLETE", get_nepal_time()
                    )
                    st.rerun()

        # ── Phase 4: COMPLETE ─────────────────────────────────────────────────
        elif phase == "COMPLETE" or sandesh_completed:
            st.success(
                "🎓 Communication complete! Your draft and revised response have been recorded."
                if lang == "en" else
                "🎓 सञ्चार पूरा! तपाईंको मस्यौदा र परिमार्जित उत्तर रेकर्ड गरियो।"
            )
            st.info(
                "A researcher will evaluate your response using the rubric shown on the left. "
                "Your self-rating has also been recorded."
                if lang == "en" else
                "एक अनुसन्धानकर्ताले देब्रेतर्फको मापदण्डले तपाईंको उत्तर मूल्यांकन गर्नेछन्।"
            )


# ── Post-study reflection survey (Q18 part d — administered AFTER study) ─────

def render_post_study_reflection(uid: str, group: str, lang: str = "ne"):
    """
    Post-study reflection survey — administered AFTER all in-system
    data collection is complete.

    This is Q18 part (d): "Did AI help you understand the chemistry
    more deeply or just help you answer questions?"

    Administered separately to avoid demand characteristics during study.
    """
    st.title(
        "📋 학습 후 반성 설문" if lang == "ko" else
        "📋 अध्ययन पछिको प्रतिबिम्ब सर्वेक्षण" if lang == "ne" else
        "📋 Post-Study Reflection Survey"
    )

    st.info(
        "This survey is about your experience with the AI agents — not about chemistry. "
        "There are no right or wrong answers. Please be honest."
        if lang == "en" else
        "यो सर्वेक्षण AI एजेन्टहरूसँगको तपाईंको अनुभवबारे छ। "
        "कुनै सही वा गलत उत्तर छैन। कृपया इमानदार हुनुहोस्।"
    )

    st.markdown("---")

    # Q18d-1: Understanding vs answering (Agentivism core distinction)
    if lang == "ko":
        label_1 = "AI 에이전트는 화학 개념을 더 깊이 이해하는 데 도움이 되었나요?"
        label_2 = "AI 에이전트는 주로 질문에 답하는 데 도움이 되었나요 (깊은 이해 없이)?"
    elif lang == "ne":
        label_1 = "AI एजेन्टहरूले रसायन विज्ञान अवधारणाहरू अझ गहिरो बुझ्न मद्दत गर्यो?"
        label_2 = "AI एजेन्टहरूले मुख्यतः प्रश्नहरूको उत्तर दिन मद्दत गर्यो (गहिरो बुझाइ बिना)?"
    else:
        label_1 = "The AI agents helped me understand the chemistry concepts more deeply."
        label_2 = "The AI agents mainly helped me answer the questions (without deeper understanding)."

    ai_understanding = st.slider(
        label_1,
        min_value=1, max_value=5, value=3,
        help="1 = Strongly disagree, 5 = Strongly agree",
        key="reflect_understanding",
    )
    st.caption("1 = Strongly disagree → 5 = Strongly agree")

    ai_answering = st.slider(
        label_2,
        min_value=1, max_value=5, value=3,
        help="1 = Strongly disagree, 5 = Strongly agree",
        key="reflect_answering",
    )
    st.caption("1 = Strongly disagree → 5 = Strongly agree")

    st.markdown("---")

    agent_options = ["Saathi (साथी)", "Khoji (खोजी)", "Praman (प्रमाण)",
                     "Tarka (तर्क)", "Rupak (रूपक)", "Sandesh (सन्देश)", "None / सबै समान"]

    hardest = st.selectbox(
        "Which agent was HARDEST to work with? / कुन एजेन्टसँग काम गर्न गाह्रो थियो?"
        if lang == "ne" else
        "Which agent was most challenging?",
        agent_options,
        key="reflect_hardest",
    )

    most_useful = st.selectbox(
        "Which agent was MOST USEFUL for your learning? / कुन एजेन्ट सबैभन्दा उपयोगी थियो?"
        if lang == "ne" else
        "Which agent was most useful for your learning?",
        agent_options,
        key="reflect_useful",
    )

    st.markdown("---")

    open_comment = st.text_area(
        "Any other thoughts about the AI learning system? / AI सिकाइ प्रणालीबारे कुनै विचार?"
        if lang == "ne" else
        "Any other thoughts about the AI learning system?",
        height=120,
        key="reflect_comment",
        placeholder=(
            "e.g. I found Tarka hardest because I had never built a scientific argument before..."
            if lang == "en" else
            "जस्तै: Tarka गाह्रो थियो किनभने मैले पहिले कहिल्यै वैज्ञानिक तर्क बनाएको थिइनँ..."
        ),
    )

    submit_label = (
        "제출" if lang == "ko" else
        "पेश गर्नुहोस्" if lang == "ne" else
        "Submit Reflection"
    )

    if st.button(submit_label, type="primary"):
        log_reflection_survey(
            uid=uid,
            group=group,
            ai_helped_understanding=ai_understanding,
            ai_helped_answering=ai_answering,
            hardest_agent=hardest,
            most_useful_agent=most_useful,
            open_comment=open_comment,
            timestamp=get_nepal_time(),
        )
        st.success(
            "✅ Reflection recorded. Thank you!"
            if lang == "en" else
            "✅ प्रतिबिम्ब रेकर्ड गरियो। धन्यवाद!"
        )
        st.balloons()
