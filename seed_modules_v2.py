"""
seed_modules.py — Seed all 6 curriculum-aligned modules
=========================================================
Run once: streamlit run seed_modules.py
Click "Seed All Modules" — adds 24 rows (6 modules × 4 groups).
Delete this file after seeding.
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
GROUPS    = ["CON", "SA", "MA", "MMALE"]

MODULES = [
  {
    "Sub_Title": "Alkali Metals — Saathi Diagnostic",
    "Objectives": "Students identify why K is more reactive than Na using electron shell reasoning from textbook",
    "Diagnostic_Question": "Sodium (Na) has the electronic configuration 2, 8, 1 and potassium (K) has the configuration 2, 8, 8, 1. Both elements are in Group IA of the periodic table. Which statement BEST explains why potassium is MORE reactive than sodium during a chemical reaction?\nNepali: सोडियम (Na) को इलेक्ट्रोन विन्यास २, ८, १ र पोटासियम (K) को २, ८, ८, १ छ। कुन कथनले पोटासियम सोडियम भन्दा बढी प्रतिक्रियाशील हुनुको उत्तम व्याख्या गर्छ?",
    "Option_A": "A) Potassium has more protons in its nucleus, which makes it heavier and therefore more chemically active.",
    "Option_B": "B) Potassium has more electron shells, so its outermost electron is further from the nucleus and easier to give away during a reaction.",
    "Option_C": "C) Potassium has more neutrons, making its nucleus less stable and more likely to react.",
    "Option_D": "D) Both Na and K have valency 1, so they are equally reactive with each other.",
    "Correct_Answer": "Option_B",
    "Socratic_Tree": "[SAATHI] Correct: B. Probe A: Ask which part of atom takes part in reactions (valence electrons, not nucleus). Then ask what extra shells do to outermost electron position. Probe C: Ask if neutrons have electrical charge and whether they can attract electrons. Probe D: Ask student to compare 2,8,1 vs 2,8,8,1 and identify what is different about outermost electron position. MASTERY: student states (1) K has more shells than Na; (2) K outermost electron is further from nucleus; (3) K gives away electron more easily. Curriculum concepts only — no ionisation energy, no shielding, no effective nuclear charge. Use: shells, valence electron, nucleus, further away, easier to give away. [KHOJI_CONTEXT] Target Q3: How does having more electron shells affect how easily the outermost electron is given away during a chemical reaction? Target hypothesis: IF number of electron shells increases (Li to Na to K) THEN outermost electron is easier to give away BECAUSE it is further from nucleus and nucleus holds it less strongly. Falsification: alkali metal with more shells but less reactive would disprove it. [PRAMAN_CONTEXT] EQ1 reject: teacher or textbook statements without data. EQ2: lab observations — reaction speed, litmus colour, fizzing amount. EQ3: observation linked to electron configuration — K has 4 shells so outermost electron is further from nucleus than Na 3 shells. No ionisation energy. [TARKA_CONTEXT] Claim: K more reactive than Na. Evidence: K config 2,8,8,1 (4 shells), Na config 2,8,1 (3 shells). Reasoning: more shells means outermost electron is further from nucleus so nucleus holds it less strongly so K gives away electron more easily in ionic bond formation. Backing: Li 2 shells reacts slowest, Na 3 shells faster, K 4 shells fastest. Rebuttal at TAP3: both have valency 1 so should be equally reactive. Counter: valency says how many electrons exchange not how easily — shell position determines ease. [RUPAK_CONTEXT] Macro: vigorous fizzing (H2 gas), alkaline solution (litmus blue), heat, more violent than Na. Submicro: K atom (2,8,8,1) gives 4th shell electron, K+ forms (2,8,8) with complete octet like argon, OH- forms causing alkalinity, H atoms pair to form H2. Symbolic: Potassium + Water → Potassium hydroxide + Hydrogen; K config before 2,8,8,1 after K+ is 2,8,8. MMALE image: 4 shells before, 3 shells after, arrow showing electron leaving 4th shell, K+ label. [SANDESH_CONTEXT] TYPE: standard Tier system for this module. English target: K and Na both have valency 1 and Group IA, K has 4 shells (2,8,8,1) Na has 3 (2,8,1), K outermost electron one shell further from nucleus so held less strongly so K gives away electron more easily producing more vigorous reaction. Nepali vocab: बाहिरी इलेक्ट्रोन, इलेक्ट्रोन कक्षा, नाभिबाट टाढा, सजिलै दिन सकिन्छ.",
  },
  {
    "Sub_Title": "Alkali Metals — Khoji Inquiry",
    "Objectives": "Students form a scientific question and hypothesis about electron shells and reactivity using textbook data",
    "Diagnostic_Question": "Look at the electron configurations from your textbook:\nLi: 2,1 (2 shells) | Na: 2,8,1 (3 shells) | K: 2,8,8,1 (4 shells)\nAll three have valency 1. Class demonstration: Li fizzes slowly, Na fizzes vigorously, K fizzes very violently.\nWrite ONE scientific question beginning with How or Why to investigate WHY they react differently despite having the same valency.\nनेपाली: पाठ्यपुस्तकको इलेक्ट्रोन विन्यास हेर्नुहोस्। तिनीहरू समान संयोजकता भए पनि फरक रूपमा किन प्रतिक्रिया गर्छन् भनी अनुसन्धान गर्न How वा Why बाट सुरु हुने एउटा वैज्ञानिक प्रश्न लेख्नुहोस्।",
    "Option_A": "OPEN_TEXT: Write your scientific question",
    "Option_B": "OPEN_TEXT: Write your hypothesis: IF [electron shells] THEN [reactivity] BECAUSE [reason]",
    "Option_C": "OPEN_TEXT: What would disprove your hypothesis?",
    "Option_D": "N/A",
    "Correct_Answer": "HYPOTHESIS_FORMED",
    "Socratic_Tree": "[KHOJI_CONTEXT] Target Q3: How does having more electron shells affect how easily the outermost electron is given away during a chemical reaction? Target hypothesis: IF number of electron shells increases THEN outermost electron is easier to give away BECAUSE it is further from nucleus and held less strongly. Probe for Q1/Q2: make question more specific — name the variable that changes (number of shells) and what it might affect (ease of electron release). Probe for hypothesis: use IF-THEN-BECAUSE structure. Falsification: alkali metal with more shells but less reactive would disprove. Curriculum only: shells, valence electron, nucleus, distance, hold less strongly.",
  },
  {
    "Sub_Title": "Alkali Metals — Praman Evidence",
    "Objectives": "Students classify evidence quality (EQ1/EQ2/EQ3) for claims about alkali metal reactivity",
    "Diagnostic_Question": "A student claims: Potassium reacts more vigorously with water than sodium because K has configuration 2,8,8,1 while Na has 2,8,1.\nClassify each piece of evidence as EQ1 (anecdotal), EQ2 (observational), or EQ3 (interpreted with atomic explanation):\n(a) My teacher said potassium is more reactive than sodium.\n(b) Potassium produced a more violent reaction and turned litmus paper blue more quickly than sodium did.\n(c) Potassium has 4 electron shells (2,8,8,1) while sodium has only 3 shells (2,8,1). K outermost electron is one shell further from the nucleus than Na outermost electron, so the nucleus holds it less strongly, making it easier for K to give away that electron in a reaction.\nنेپाली: दाबीको लागि (क), (ख), (ग) प्रमाणहरू EQ1, EQ2, वा EQ3 मा वर्गीकृत गर्नुहोस्।",
    "Option_A": "EQ1, EQ2, EQ3 (classify a, b, c in this order)",
    "Option_B": "EQ1, EQ3, EQ2",
    "Option_C": "EQ2, EQ1, EQ3",
    "Option_D": "EQ2, EQ2, EQ3",
    "Correct_Answer": "Option_A",
    "Socratic_Tree": "[PRAMAN_CONTEXT] Correct: A (a=EQ1, b=EQ2, c=EQ3). EQ1 probe: does the teacher statement provide any measurement or observation? EQ2 probe: observation describes WHAT happens not WHY. EQ3 probe: connects observable (more violent) to atomic structure (shell count, electron distance). Challenge after correct: what would you add to (b) to make it EQ3? They need to add the electron configuration reasoning. Curriculum only: shell count, outermost electron distance, nucleus holds less strongly.",
  },
  {
    "Sub_Title": "Alkali Metals — Tarka Argumentation",
    "Objectives": "Students build and evaluate a complete TAP Level 5 argument about alkali metal reactivity using curriculum concepts",
    "Diagnostic_Question": "Evaluate this argument: 'Potassium is more reactive than sodium. I know this because in the demonstration, potassium reacted more violently with water. This is because potassium has the electronic configuration 2,8,8,1.'\n(a) Identify the CLAIM, EVIDENCE, and REASONING.\n(b) What is MISSING?\n(c) Write an IMPROVED version with claim + evidence + reasoning + rebuttal.\nनेपाली: यस तर्कको मूल्यांकन गर्नुहोस् र सुधारिएको संस्करण लेख्नुहोस्।",
    "Option_A": "A) The argument is complete and scientifically convincing as stated.",
    "Option_B": "B) The argument is missing the REASONING — it does not explain WHY the configuration difference causes the reactivity difference.",
    "Option_C": "C) The argument is missing EVIDENCE — no data from electron configurations is given.",
    "Option_D": "D) The argument is missing a REBUTTAL — it does not address counterarguments.",
    "Correct_Answer": "Option_B",
    "Socratic_Tree": "[TARKA_CONTEXT] Correct: B. The original argument has claim (K more reactive) and evidence (lab observation + config 2,8,8,1) but MISSING reasoning — does not explain WHY 2,8,8,1 causes more reactivity. Reasoning target: K has 4 shells, Na has 3 shells, K outermost electron is one shell further from nucleus, nucleus holds it less strongly, K gives away electron more easily, causes more vigorous reaction. Rebuttal to introduce at TAP3: both have valency 1 so should be equally reactive. Counter: valency tells HOW MANY electrons not HOW EASILY — shell position determines ease. TAP5 complete: claim + config evidence + shell-distance reasoning + backing (Li Na K trend) + rebuttal response. Curriculum only.",
  },
  {
    "Sub_Title": "Alkali Metals — Rupak Modelling",
    "Objectives": "Students represent K + H2O reaction at macroscopic, submicroscopic (shell diagram), and symbolic levels",
    "Diagnostic_Question": "Your textbook shows how Na gives its electron to Cl to form NaCl (Figures 8.2-8.4). Using the SAME style of thinking, represent the reaction of potassium with water at THREE levels:\n(a) MACROSCOPIC: What would you observe in the laboratory?\n(b) SUBMICROSCOPIC: Draw or describe what the K atom does. Which electron does it give? To what? What is left behind? Use shell diagram style.\n(c) SYMBOLIC: Write the word equation. Show K configuration before and after.\nNepali: K + H2O प्रतिक्रियालाई तीन तहमा प्रतिनिधित्व गर्नुहोस्।",
    "Option_A": "A) Macroscopic only — describes observations but not particle level",
    "Option_B": "B) All three levels with correct shell diagrams and word equation",
    "Option_C": "C) Submicroscopic only — describes particles but not observations",
    "Option_D": "D) Symbolic only — writes equation without linking to observations or particle behaviour",
    "Correct_Answer": "Option_B",
    "Socratic_Tree": "[RUPAK_CONTEXT] Macro: vigorous fizzing (H2 gas), alkaline solution (litmus blue), heat, more violent than Na reaction. Submicro: K atom (2,8,8,1) gives 4th shell single electron to water molecule. K+ forms (2,8,8) — like argon, complete octet, stable. OH- forms causing alkalinity. H atoms pair to form H2 gas. SYMBOLIC: Potassium + Water → Potassium hydroxide + Hydrogen gas. K before: 2,8,8,1. K+ after: 2,8,8. Cross-level probes: fizzing = H2 gas from submicroscopic H atom pairing. Blue litmus = OH- forming from water split. Shell diagram: 4 shells before, 3 shells after, arrow from 4th shell electron. MMALE image check: 4 shells before, 3 shells after, arrow showing electron leaving, K+ label with charge.",
  },
  {
    "Sub_Title": "Alkali Metals — Sandesh Communication",
    "Objectives": "Students synthesise and communicate understanding of alkali metal reactivity bilingually using curriculum concepts",
    "Diagnostic_Question": "POST-TEST COMMUNICATION TASK:\nYou have investigated why potassium is more reactive than sodium using five AI agents. Now communicate your complete understanding.\nWrite 4-6 sentences in ENGLISH explaining: (1) what K and Na have in common; (2) what is different about their electron configurations; (3) WHY the difference causes different reactivity; (4) what you observe in the laboratory that supports this.\nThen write the SAME explanation in NEPALI.\nनेपाली: अंग्रेजी र नेपाली दुवैमा तपाईंको पूर्ण बुझाइ सञ्चार गर्नुहोस्।",
    "Option_A": "OPEN_RESPONSE",
    "Option_B": "OPEN_RESPONSE",
    "Option_C": "OPEN_RESPONSE",
    "Option_D": "OPEN_RESPONSE",
    "Correct_Answer": "OPEN_RESPONSE",
    "Socratic_Tree": "[SANDESH_CONTEXT] TYPE: Open-response — routed to sandesh_module.py. Data written to OpenResponse sheet not Assessment_Logs. English target: Both Na and K have valency 1 and Group IA membership. K has 4 electron shells (2,8,8,1) while Na has 3 (2,8,1). K outermost electron is one shell further from nucleus so nucleus holds it less strongly. K gives away valence electron more easily in reaction causing more vigorous fizzing, alkaline solution, and heat. Nepali target: Na र K दुवैको संयोजकता १ छ र दुवै समूह IA मा छन्। K मा ४ इलेक्ट्रोन कक्षाहरू (२,८,८,१) र Na मा ३ (२,८,१) छन्। K को बाहिरी इलेक्ट्रोन नाभिबाट एक कक्षा थप टाढा छ। Nepali vocab: बाहिरी इलेक्ट्रोन, इलेक्ट्रोन कक्षा, नाभिबाट टाढा, सजिलै दिन सकिन्छ, संयोजकता। COMMUNICATION_COMPLETE: English with mechanistic chain + Nepali version + lab observation linked.",
  },
]

def get_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    info = dict(st.secrets["gcp_service_account"])
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n","\n")
    return gspread.authorize(Credentials.from_service_account_info(info,scopes=scope))

st.set_page_config(page_title="Seed Modules v2", page_icon="🌱")
st.title("🌱 Seed All 6 Curriculum-Aligned Modules")
st.warning("Run this once. It adds 24 rows (6 modules × 4 groups). Delete after seeding.")

st.markdown(f"**Modules to seed:** {len(MODULES)} | **Groups:** {GROUPS} | **Total rows:** {len(MODULES)*len(GROUPS)}")
for m in MODULES:
    st.write(f"  • {m['Sub_Title']} — Correct: {m['Correct_Answer']}")

if st.button("🚀 Seed All Modules Now", type="primary"):
    try:
        client = get_client()
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.worksheet("Instructional_Materials")
        count = 0
        for mod in MODULES:
            for grp in GROUPS:
                row = [
                    datetime.now().strftime("%Y-%m-%d"),
                    "SEED_SCRIPT", grp, "Periodic Table",
                    mod["Sub_Title"], mod["Objectives"],
                    "", "",
                    mod["Diagnostic_Question"],
                    mod["Option_A"], mod["Option_B"],
                    mod["Option_C"], mod["Option_D"],
                    mod["Correct_Answer"],
                    mod["Socratic_Tree"],
                ]
                ws.append_row(row)
                count += 1
        st.success(f"✅ Seeded {count} rows successfully!")
        st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)

st.caption("Delete this file after seeding. Future modules go through the Teacher Portal.")
