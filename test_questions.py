"""
test_questions.py — MMALE Sample Question Set & Agent Test Prompts
===================================================================
Topic: Periodic Table — Alkali Metals (Grade 11 Chemistry, Nepal)

This module provides:
  1. A complete diagnostic question for the four-tier instrument
  2. Six test conversation sequences — one per agent — to verify
     that each agent behaves correctly before classroom deployment
  3. Expected signal outputs for each sequence (for QA testing)
  4. A Korean supervisor summary of the research design

Usage:
  Run this file directly to see the test questions:
    python3 test_questions.py

  Or import the constants into your testing workflow:
    from test_questions import SAMPLE_MODULE, AGENT_TEST_SEQUENCES
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SAMPLE MODULE — Periodic Table: Alkali Metals
# Matches the structure of Instructional_Materials Google Sheet
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_MODULE = {
    "Main_Title":           "Periodic Table",
    "Sub_Title":            "Alkali Metals and Their Properties",
    "Group":                "MMALE",
    "Objectives": (
        "Students will be able to: (1) explain why alkali metals are highly "
        "reactive using electron configuration; (2) predict reactivity trends "
        "down Group IA; (3) construct a scientific argument using Toulmin's "
        "framework; (4) represent the phenomenon at macroscopic, submicroscopic, "
        "and symbolic levels; (5) communicate scientific understanding bilingually."
    ),
    "Diagnostic_Question": (
        "Sodium (Na) reacts vigorously with water to produce hydrogen gas and "
        "sodium hydroxide. Potassium (K) reacts even more vigorously with water "
        "than sodium. Which of the following BEST explains why potassium is more "
        "reactive than sodium?"
    ),
    "Option_A": (
        "A) Potassium has more protons in its nucleus, making it heavier "
        "and more likely to react."
    ),
    "Option_B": (
        "B) Potassium's outermost electron is further from the nucleus and "
        "experiences more electron shielding, so it is lost more easily."
    ),
    "Option_C": (
        "C) Potassium has more neutrons, which makes the nucleus unstable "
        "and causes it to react with water."
    ),
    "Option_D": (
        "D) Potassium reacts faster because it is a liquid at room temperature "
        "and has more surface area."
    ),
    "Correct_Answer": "Option_B",
    "Socratic_Tree": (
        "[SAATHI] Key misconception: students often think reactivity is caused by "
        "nuclear mass (protons/neutrons) rather than valence electron behaviour. "
        "Correct explanation: reactivity increases down Group IA because atomic "
        "radius increases, shielding increases, and ionisation energy decreases — "
        "meaning the outermost electron is lost more easily.\n\n"
        "[TARKA_CONTEXT] Main claim: Potassium is more reactive than sodium because "
        "its outermost electron requires less energy to remove. Evidence: ionisation "
        "energy of K (418 kJ/mol) < Na (496 kJ/mol). Reasoning: larger atomic radius "
        "and greater electron shielding reduce nuclear attraction on the valence "
        "electron. Counterargument: 'Potassium is heavier, so it should be less "
        "reactive' — challenge this directly.\n\n"
        "[RUPAK_CONTEXT] Macroscopic: vigorous fizzing, purple flame, solution turns "
        "alkaline. Submicroscopic: K atom donates one electron to H₂O; K⁺ and OH⁻ "
        "ions form; H₂ gas released. Symbolic: "
        "2K(s) + 2H₂O(l) → 2KOH(aq) + H₂(g)"
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT TEST SEQUENCES
# Each sequence simulates a realistic student interaction for QA testing
# Format: list of {"role": "user"/"assistant", "content": str, "expect": str}
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_TEST_SEQUENCES = {

    # ── AGENT 1: SAATHI ───────────────────────────────────────────────────────
    "SAATHI": {
        "description": "Tests Socratic misconception detection for Alkali Metals",
        "topic":       "Alkali Metals and Their Properties",
        "t1_answer":   "A) Potassium has more protons, making it heavier and more reactive",
        "t3_reasoning":"Heavier elements react more because they have more mass",
        "test_turns": [
            {
                "student": "I think potassium reacts more because it has more protons.",
                "expect_signal": None,
                "expect_redirect": None,
                "purpose": "Misconception activation — Saathi should probe, not correct",
            },
            {
                "student": "Because more protons means the atom is bigger and stronger?",
                "expect_signal": None,
                "purpose": "Saathi should ask about electron behaviour, not nuclear mass",
            },
            {
                "student": "Oh, so the outermost electron in potassium is further away "
                           "from the nucleus and feels less pull, so it comes off more easily. "
                           "That is why potassium ionises more easily than sodium.",
                "expect_signal": "[MASTERY_DETECTED]",
                "purpose": "Complete mechanistic explanation — should trigger mastery",
            },
        ],
        "expected_db_log": "SAATHI_CHAT",
        "expected_completion_status": "POST",
    },

    # ── AGENT 2: KHOJI ────────────────────────────────────────────────────────
    "KHOJI": {
        "description": "Tests question quality scaffolding and hypothesis formation",
        "topic":       "Alkali Metals and Their Properties",
        "test_turns": [
            {
                "student": "Why do alkali metals react with water?",
                "expect_signal": "[QUESTION_QUALITY_2]",
                "purpose": "Level 2 question — Khoji should push toward causal framing",
            },
            {
                "student": "How does the distance of the outermost electron from the "
                           "nucleus affect how easily it is lost in a reaction?",
                "expect_signal": "[QUESTION_QUALITY_3]",
                "purpose": "Level 3 causal question — Khoji should acknowledge and move to hypothesis",
            },
            {
                "student": "If the outermost electron is further from the nucleus, "
                           "then the element will lose it more easily and react more "
                           "vigorously with water, because nuclear attraction decreases "
                           "with distance.",
                "expect_signal": "[HYPOTHESIS_FORMED]",
                "purpose": "Complete testable hypothesis — should trigger HYPOTHESIS_FORMED",
            },
        ],
        "expected_db_log": "KHOJI_CHAT",
        "expected_completion_status": "KHOJI_COMPLETE",
    },

    # ── AGENT 3: PRAMAN ───────────────────────────────────────────────────────
    "PRAMAN": {
        "description": "Tests evidence quality evaluation",
        "topic":       "Alkali Metals and Their Properties",
        "test_turns": [
            {
                "student": "My evidence is that the teacher told us potassium is more reactive.",
                "expect_signal": "[EVIDENCE_QUALITY_1]",
                "purpose": "Anecdotal evidence — Praman should redirect to data",
            },
            {
                "student": "Potassium reacted more violently with water than sodium "
                           "in the demonstration — it produced a purple flame and "
                           "exploded more.",
                "expect_signal": "[EVIDENCE_QUALITY_2]",
                "purpose": "Observational evidence — Praman should push for interpretation",
            },
            {
                "student": "The ionisation energy of potassium is 418 kJ/mol compared "
                           "to sodium's 496 kJ/mol. This means less energy is needed "
                           "to remove potassium's outermost electron, which explains why "
                           "it reacts more vigorously — the electron is lost more readily.",
                "expect_signal": "[EVIDENCE_QUALITY_3]",
                "purpose": "Interpreted data with mechanism — should trigger EQ3",
            },
        ],
        "expected_db_log": "PRAMAN_CHAT",
        "expected_completion_status": "PRAMAN_COMPLETE",
    },

    # ── AGENT 4: TARKA ────────────────────────────────────────────────────────
    "TARKA": {
        "description": "Tests full Toulmin argumentation scaffolding",
        "topic":       "Alkali Metals and Their Properties",
        "test_turns": [
            {
                "student": "Potassium is more reactive than sodium.",
                "expect_signal": "[TAP_LEVEL_1_DETECTED]",
                "purpose": "Claim only — Tarka should request evidence",
            },
            {
                "student": "Potassium is more reactive than sodium because its ionisation "
                           "energy is lower — 418 kJ/mol versus 496 kJ/mol for sodium.",
                "expect_signal": "[TAP_LEVEL_2_DETECTED]",
                "purpose": "Claim + data — Tarka should request reasoning/warrant",
            },
            {
                "student": "Potassium is more reactive than sodium because its ionisation "
                           "energy is lower (418 vs 496 kJ/mol). This is because potassium "
                           "has a larger atomic radius and greater electron shielding, so "
                           "the outermost electron experiences less nuclear attraction and "
                           "is removed more easily.",
                "expect_signal": "[TAP_LEVEL_3_DETECTED]",
                "purpose": "Claim + data + warrant — Tarka should introduce rebuttal",
            },
            {
                "student": "Some might argue that potassium reacts more because it is "
                           "heavier, but this is incorrect — reactivity in Group IA is "
                           "determined by ionisation energy, not atomic mass. The trend "
                           "of decreasing ionisation energy down the group confirms that "
                           "electron shielding and atomic radius are the key factors.",
                "expect_signal": "[TAP_LEVEL_5_DETECTED]",
                "purpose": "Complete argument with rebuttal — should trigger TAP_5",
            },
        ],
        "expected_db_log": "TARKA_CHAT",
        "expected_completion_status": "TAP_COMPLETE_TAP_5",
    },

    # ── AGENT 5: RUPAK ────────────────────────────────────────────────────────
    "RUPAK": {
        "description": "Tests Johnstone's triangle navigation",
        "topic":       "Alkali Metals and Their Properties",
        "test_turns": [
            {
                "student": "I can see that potassium reacts very violently with water — "
                           "it produces a purple flame and hisses loudly.",
                "expect_signal": "[MONADIC_CONFINEMENT_DETECTED]",
                "purpose": "Macroscopic only — Rupak should push to submicroscopic",
            },
            {
                "student": "At the molecular level, the potassium atom gives its outermost "
                           "electron to a water molecule. The K becomes K⁺ and the water "
                           "splits to form OH⁻ and hydrogen gas H₂.",
                "expect_signal": "[BIADIC_REPRESENTATION_DETECTED]",
                "purpose": "Macro + submicro — Rupak should push to symbolic level",
            },
            {
                "student": "The balanced equation is: 2K(s) + 2H₂O(l) → 2KOH(aq) + H₂(g). "
                           "The 's' means solid potassium, 'l' is liquid water, 'aq' means "
                           "the ions are dissolved. The ratio 2:2:2:1 shows conservation "
                           "of atoms. And if I work backwards from the equation, I know "
                           "the solution will be alkaline (pH > 7) because of the OH⁻ ions.",
                "expect_signal": "[TRIADIC_FLUENCY_DETECTED]",
                "purpose": "All three levels + reverse translation — should trigger TRIADIC",
            },
        ],
        "expected_db_log": "RUPAK_CHAT",
        "expected_completion_status": "TRIADIC_COMPLETE",
    },

    # ── AGENT 6: SANDESH ──────────────────────────────────────────────────────
    "SANDESH": {
        "description": "Tests bilingual science communication and synthesis",
        "topic":       "Alkali Metals and Their Properties",
        "test_turns": [
            {
                "student": "Potassium reacts with water.",
                "expect_signal": "[COMMUNICATION_PARTIAL]",
                "purpose": "Incomplete summary — Sandesh should request what/why/evidence",
            },
            {
                "student": "Potassium reacts vigorously with water because its outermost "
                           "electron is easily lost due to low ionisation energy, producing "
                           "KOH and H₂. Evidence: ionisation energy of K (418 kJ/mol) is "
                           "lower than Na (496 kJ/mol), confirming easier electron removal.",
                "expect_signal": None,
                "purpose": "Good English summary — Sandesh should request Nepali translation",
            },
            {
                "student": (
                    "पोटासियम पानीसँग तीव्र रूपमा प्रतिक्रिया गर्छ किनभने "
                    "यसको बाहिरी इलेक्ट्रोन कम आयनीकरण ऊर्जाको कारण सजिलै "
                    "हटाइन्छ। यसले KOH र H₂ उत्पादन गर्छ। "
                    "Potassium reacts vigorously with water because its outermost "
                    "electron is easily removed due to its lower ionisation energy "
                    "compared to sodium, producing potassium hydroxide and hydrogen gas."
                ),
                "expect_signal": "[COMMUNICATION_COMPLETE]",
                "purpose": "Accurate bilingual synthesis — should trigger COMMUNICATION_COMPLETE",
            },
        ],
        "expected_db_log": "SANDESH_CHAT",
        "expected_completion_status": "ECOLOGY_COMPLETE",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# KOREAN SUPERVISOR SUMMARY
# For review by PhD supervisor and Korean research committee
# ═══════════════════════════════════════════════════════════════════════════════

KOREAN_SUPERVISOR_SUMMARY = """
MMALE 연구 시스템 요약
(Multimodal Multi-Agent Learning Ecology)
박사과정 연구 — 네팔 고등학교 화학 교육

연구 목적:
본 연구는 생성형 AI(Generative AI)가 네팔 고등학교 화학 수업에서
학생들의 과학적 실천(Scientific Practices)을 어떻게 매개(mediate)하는지를
설계 기반 연구(Design-Based Research, DBR) 방법론으로 탐구합니다.

연구 그룹 (4개):
  CON   — 통제 집단: AI 없음, 표준 수업
  SA    — 단일 에이전트: Saathi AI (진단 전용)
  MA    — 다중 에이전트: Saathi + Tarka + Rupak
  MMALE — 완전 생태계: 6개 에이전트 + 멀티모달

6개 AI 에이전트 및 과학적 실천:
  साथी (Saathi)   — 오개념 진단 및 소크라테스 대화
  खोजी (Khoji)   — 탐구 질문 및 가설 형성
  प्रमाण (Praman) — 증거 평가 및 데이터 분석
  तर्क (Tarka)   — 과학적 논증 (Toulmin 모형)
  रूपक (Rupak)   — 화학 모델링 (Johnstone의 삼각형)
  सन्देश (Sandesh) — 과학적 의사소통 (이중언어)

핵심 이론적 프레임워크:
  - Agentivism (Yan & Gašević, 2026): 수행(performance)과 학습(learning)의 분리
  - Toulmin 논증 패턴 (TAP): 주장-증거-추론-반박
  - Johnstone의 삼각형: 거시적-미시적-상징적 표상
  - 설계 기반 연구 (DBR): 4단계 24개월

데이터 수집 도구:
  - 4계층 진단 도구 (Tier 1–6): 수행-학습 격차 측정
  - TAP 수준 분포: 논증 품질 추적
  - 표상 수준 로그 (ArgLog, RepLog): 구글 스프레드시트 자동 기록
  - 교사 반성 일지 및 교실 관찰

연구 윤리:
  본 연구는 네팔 교육부 승인 및 학교 동의를 받아 진행됩니다.
  모든 학생 데이터는 익명화되어 보관됩니다.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# QA TEST RUNNER — for manual verification before classroom deployment
# ═══════════════════════════════════════════════════════════════════════════════

def print_test_plan():
    print("=" * 70)
    print("MMALE AGENT TEST PLAN — Alkali Metals (Grade 11 Chemistry, Nepal)")
    print("=" * 70)
    print()

    for agent_key, seq in AGENT_TEST_SEQUENCES.items():
        print(f"\n{'─' * 60}")
        print(f"AGENT: {agent_key} — {seq['description']}")
        print(f"Topic: {seq['topic']}")
        print(f"Expected DB log type: {seq['expected_db_log']}")
        print(f"Expected completion status: {seq['expected_completion_status']}")
        print()
        for i, turn in enumerate(seq["test_turns"], 1):
            print(f"  Turn {i}:")
            print(f"    Student: \"{turn['student'][:80]}...\"" if len(turn['student']) > 80
                  else f"    Student: \"{turn['student']}\"")
            print(f"    Purpose: {turn['purpose']}")
            if turn.get("expect_signal"):
                print(f"    Expected signal: {turn['expect_signal']}")
            print()

    print("\n" + "=" * 70)
    print("SAMPLE MODULE CONFIGURATION")
    print("=" * 70)
    for k, v in SAMPLE_MODULE.items():
        val = str(v)[:80] + "..." if len(str(v)) > 80 else str(v)
        print(f"  {k:25s}: {val}")

    print("\n" + "=" * 70)
    print("KOREAN SUPERVISOR SUMMARY")
    print("=" * 70)
    print(KOREAN_SUPERVISOR_SUMMARY)


if __name__ == "__main__":
    print_test_plan()
