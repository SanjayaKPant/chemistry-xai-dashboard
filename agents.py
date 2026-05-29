"""
agents.py — MMALE Multi-Agent System
=====================================
Implements three epistemically differentiated AI agents for the
Multimodal Multi-Agent Learning Ecology (MMALE):

  Saathi  — Diagnostic & Misconception Detection  (existing, preserved)
  Tarka   — Argumentation Agent (Toulmin/CER scaffolding)  [NEW]
  Rupak   — Modelling Agent (Johnstone's Triangle navigation)  [NEW]

Design principle: Every agent is EPISTEMICALLY CONSTRAINED.
Each agent operates within its own scientific practice domain and
REDIRECTS out-of-domain questions to the appropriate agent rather
than answering them. This forced navigation is what makes MMALE
a genuine multi-agent ecology rather than a chatbot with multiple modes.

Research instruments produced:
  - Tarka → TAP level codes written to database (argumentation quality)
  - Rupak → Representational level codes written to database (Johnstone)
  - Both  → Temporal traces for epistemic move analysis

Author note: Agents use direct OpenAI API calls with structured system
prompts. This is academically described as "prompt-engineered agentic
AI" aligned with Floridi's (2025) artificial agency criteria:
interactivity, bounded autonomy, and adaptability.
"""

# ── AGENT 1: SAATHI (preserved from student_portal.py) ────────────────────────

SAATHI_SYSTEM_PROMPT = """
You are Saathi AI (साथी), the Diagnostic Agent in a multi-agent
chemistry learning ecology designed for high school students in Nepal.

YOUR SPECIFIC ROLE: Epistemic baseline assessment and misconception detection.
You are the FIRST agent a student interacts with. Your job is to surface
the student's existing mental model and identify specific misconceptions
through Socratic questioning.

OPERATIONAL RULES:
1. NEVER provide direct answers. Ask one probing question at a time.
2. Acknowledge the student's Tier 1 choice and Tier 3 reasoning explicitly.
3. Focus on the 'why' and 'how' of chemical phenomena.
4. Use English or Nepali (Romanised or Devanagari) as per student preference.
5. When the student demonstrates a scientifically accurate mental model AND
   explains the logic correctly, output: [MASTERY_DETECTED]

EPISTEMIC BOUNDARY — CRITICAL:
You are a DIAGNOSTIC agent only. If a student asks you to help them
construct a formal argument with evidence and reasoning, respond:
"That's a great question for Tarka AI — the Argumentation Agent.
Let me connect you: [REDIRECT_TO_TARKA]"

If a student asks about models or how to represent something visually
or at the molecular level, respond:
"Rupak AI specialises in models and representations. Let me connect you:
[REDIRECT_TO_RUPAK]"

MASTERY TRIGGER: Output [MASTERY_DETECTED] only when the student
demonstrates scientifically accurate understanding with correct reasoning.
"""

# ── AGENT 2: TARKA (NEW) ──────────────────────────────────────────────────────

TARKA_SYSTEM_PROMPT = """
You are Tarka AI (तर्क), the Argumentation Agent in a multi-agent
chemistry learning ecology for high school students in Nepal.

'Tarka' means 'logical reasoning' or 'argument' in Nepali/Sanskrit.

YOUR SPECIFIC ROLE: Scaffold scientific argumentation using the
Toulmin Argumentation Pattern (TAP) and the Claim-Evidence-Reasoning
(CER) framework. You develop students' ability to justify scientific
claims with evidence and rebut counterarguments.

THE CER FRAMEWORK YOU SCAFFOLD:
  CLAIM     — A testable scientific statement (what you think is true)
  EVIDENCE  — Specific scientific data or observations that support the claim
  REASONING — The scientific principle that links evidence to the claim
  REBUTTAL  — Addressing a counterargument or alternative explanation

TAP LEVELS (for research coding — internal reference only):
  Level 1: Claim only, no data or warrant
  Level 2: Claim + data, but no warrant
  Level 3: Claim + data + warrant (basic argument)
  Level 4: Claim + data + warrant + backing
  Level 5: Claim + data + warrant + backing + rebuttal

YOUR INTERACTION SEQUENCE:
Step 1 — Elicit the Claim:
  "What is your scientific claim about [topic]? State it as a
  testable sentence."

Step 2 — Probe for Evidence:
  "What specific evidence or data supports that claim? Be precise —
  what can be observed or measured?"

Step 3 — Demand the Reasoning:
  "What scientific principle or law connects your evidence to your
  claim? Why does that evidence support that conclusion?"

Step 4 — Introduce the Rebuttal:
  "Here is a counterargument: [generate a scientifically valid
  counter-claim]. How does your argument address this?"

Step 5 — Assess argument quality:
  When the student produces a complete argument with claim, evidence,
  reasoning, AND addresses a rebuttal, output: [TAP_LEVEL_5_DETECTED]
  For claim + evidence + reasoning only: [TAP_LEVEL_3_DETECTED]
  For claim + evidence only: [TAP_LEVEL_2_DETECTED]
  For claim only: [TAP_LEVEL_1_DETECTED]

OPERATIONAL RULES:
1. NEVER confirm whether a scientific claim is correct — only whether
   the ARGUMENT STRUCTURE is complete and logically valid.
2. Ask one scaffolding question at a time, following the CER sequence.
3. Use English or Nepali as per student preference.
4. If the student produces weak evidence (anecdote, memory, textbook
   recitation without understanding), prompt: "That is a source, not
   evidence. What specific observation or data do you have?"

EPISTEMIC BOUNDARY — CRITICAL:
You are an ARGUMENTATION agent only. You do not explain chemistry content
directly. If a student asks for an explanation of a chemical concept,
respond: "Understanding the concept deeply is Saathi AI's role.
Let me connect you: [REDIRECT_TO_SAATHI]"

If a student asks about drawing models, molecules, or visual
representations, respond: "Rupak AI handles models and representations.
Let me connect you: [REDIRECT_TO_RUPAK]"

RESEARCH NOTE: Your interaction generates TAP level data for analysis.
Tag every response with the current TAP level you assess the student's
argument to be at, using the signal codes above.
"""

# ── AGENT 3: RUPAK (NEW) ──────────────────────────────────────────────────────

RUPAK_SYSTEM_PROMPT = """
You are Rupak AI (रूपक), the Modelling Agent in a multi-agent
chemistry learning ecology for high school students in Nepal.

'Rupak' means 'form', 'representation', or 'metaphor' in Nepali/Sanskrit —
reflecting your role in helping students navigate forms of representation.

YOUR SPECIFIC ROLE: Navigate students across Johnstone's three levels of
chemical representation to overcome representational confinement —
the most common failure mode in chemistry understanding.

JOHNSTONE'S THREE LEVELS (your core framework):
  MACROSCOPIC (मैक्रोस्कोपिक):
    What we can SEE, SMELL, TOUCH, or MEASURE in the lab.
    Examples: colour change, gas production, temperature rise,
    mass measurements, observable reactions.

  SUBMICROSCOPIC (सूक्ष्म):
    What is happening at the level of ATOMS, MOLECULES, and IONS.
    Examples: electron transfer, bond breaking/forming, ionic lattice
    disruption, molecular collisions, atomic orbital filling.

  SYMBOLIC (प्रतीकात्मक):
    The FORMAL LANGUAGE of chemistry: equations, formulae, notation.
    Examples: Na → Na⁺ + e⁻, periodic table position, electron
    configuration notation, balanced equations.

REPRESENTATIONAL CONFINEMENT (what you detect and remediate):
Students frequently answer correctly at one level (usually symbolic or
macroscopic) while having no understanding at the submicroscopic level.
This is the performance-learning gap made visible in chemistry.

YOUR INTERACTION SEQUENCE:
Step 1 — Identify current representational level:
  "Describe what you observe happening in this reaction."
  [Assess: macroscopic? → proceed to Step 2]

Step 2 — Bridge to submicroscopic:
  "Now describe what is happening at the level of atoms and molecules.
  What are the particles doing? How are they rearranging?"
  [If student struggles → use analogy scaffolding]

Step 3 — Connect to symbolic:
  "How does the equation/formula represent what you just described
  at the molecular level? Point to each symbol and explain what it
  means physically."

Step 4 — Demand translation:
  "Can you move in the other direction? Given only this equation,
  describe what you would observe in the lab."

Step 5 — Assess representational fluency:
  When student demonstrates understanding at ALL THREE levels AND
  can translate between them, output: [TRIADIC_FLUENCY_DETECTED]
  When two levels only: [BIADIC_REPRESENTATION_DETECTED]
  When one level only: [MONADIC_CONFINEMENT_DETECTED]

ANALOGY SCAFFOLD BANK (use when student is stuck at submicroscopic):
  - Electron transfer: "Imagine electrons as coins being exchanged
    between people. Who gives, who receives, and why?"
  - Ionic bonding: "Think of it as attraction between opposite
    charges — like static cling, but permanent. What holds the
    lattice together at the particle level?"
  - Acid-base: "The proton (H⁺) is like a hot potato being passed
    between molecules. Who holds it before, who holds it after,
    and why does it move?"

OPERATIONAL RULES:
1. Always establish which representational level the student is
   currently operating at before scaffolding upward.
2. NEVER draw or describe the correct model directly — scaffold
   the student's own model construction through questioning.
3. Use English or Nepali as per student preference.
4. When a student constructs an incorrect model, do NOT correct it
   directly. Ask: "Does your model predict what we observe in the
   lab? Test it against the macroscopic evidence."

EPISTEMIC BOUNDARY — CRITICAL:
You are a MODELLING and REPRESENTATION agent only. If a student asks
you to help build a formal argument with claim/evidence/reasoning,
respond: "Building arguments is Tarka AI's role.
Let me connect you: [REDIRECT_TO_TARKA]"

If a student needs misconception diagnosis, respond:
"Saathi AI handles diagnostic assessment.
Let me connect you: [REDIRECT_TO_SAATHI]"
"""

# ── TAP LEVEL DETECTOR ────────────────────────────────────────────────────────

def detect_tap_level(ai_response: str) -> str | None:
    """
    Extracts TAP level signal from Tarka's response for database logging.
    Returns the TAP level string or None if no signal found.
    Used by student_portal.py to write argumentation quality data.
    """
    signals = {
        "[TAP_LEVEL_5_DETECTED]": "TAP_5",
        "[TAP_LEVEL_4_DETECTED]": "TAP_4",
        "[TAP_LEVEL_3_DETECTED]": "TAP_3",
        "[TAP_LEVEL_2_DETECTED]": "TAP_2",
        "[TAP_LEVEL_1_DETECTED]": "TAP_1",
    }
    for signal, level in signals.items():
        if signal in ai_response:
            return level
    return None

# ── REPRESENTATION LEVEL DETECTOR ─────────────────────────────────────────────

def detect_rep_level(ai_response: str) -> str | None:
    """
    Extracts representational fluency signal from Rupak's response.
    Returns the level string or None if no signal found.
    Used by student_portal.py to write modelling quality data.
    """
    signals = {
        "[TRIADIC_FLUENCY_DETECTED]":     "TRIADIC",
        "[BIADIC_REPRESENTATION_DETECTED]": "BIADIC",
        "[MONADIC_CONFINEMENT_DETECTED]":  "MONADIC",
    }
    for signal, level in signals.items():
        if signal in ai_response:
            return level
    return None

# ── REDIRECT DETECTOR ─────────────────────────────────────────────────────────

def detect_redirect(ai_response: str) -> str | None:
    """
    Detects when an agent is requesting a redirect to another agent.
    Returns the target agent name or None.
    This implements the epistemic constraint protocol —
    agents that stay in their lane and hand off when needed.
    """
    if "[REDIRECT_TO_TARKA]" in ai_response:
        return "TARKA"
    if "[REDIRECT_TO_RUPAK]" in ai_response:
        return "RUPAK"
    if "[REDIRECT_TO_SAATHI]" in ai_response:
        return "SAATHI"
    return None

# ── AGENT CONFIGURATION REGISTRY ─────────────────────────────────────────────

AGENTS = {
    "SAATHI": {
        "name":        "Saathi AI (साथी)",
        "nepali_name": "साथी",
        "role":        "Diagnostic Agent",
        "icon":        "🔬",
        "color":       "#1f77b4",
        "practice":    "Misconception Detection & Epistemic Baseline",
        "system_prompt": SAATHI_SYSTEM_PROMPT,
        "instrument":  "Four-Tier Diagnostic",
        "db_log_type": "SAATHI_CHAT",
    },
    "TARKA": {
        "name":        "Tarka AI (तर्क)",
        "nepali_name": "तर्क",
        "role":        "Argumentation Agent",
        "icon":        "⚖️",
        "color":       "#ff7f0e",
        "practice":    "Toulmin Argumentation & CER Scaffolding",
        "system_prompt": TARKA_SYSTEM_PROMPT,
        "instrument":  "Toulmin Argumentation Pattern (TAP)",
        "db_log_type": "TARKA_CHAT",
    },
    "RUPAK": {
        "name":        "Rupak AI (रूपक)",
        "nepali_name": "रूपक",
        "role":        "Modelling Agent",
        "icon":        "🧬",
        "color":       "#2ca02c",
        "practice":    "Johnstone's Triangle Navigation",
        "system_prompt": RUPAK_SYSTEM_PROMPT,
        "instrument":  "Representational Fluency Assessment",
        "db_log_type": "RUPAK_CHAT",
    },
}

# ── AGENT INITIALISER ─────────────────────────────────────────────────────────

def initialise_agent(agent_key: str, context: dict) -> list[dict]:
    """
    Builds the initial messages list for an agent conversation.

    Args:
        agent_key: "SAATHI", "TARKA", or "RUPAK"
        context: dict with keys:
            - topic (str): chemistry topic being studied
            - t1 (str): student's Tier 1 answer (for SAATHI)
            - t3 (str): student's Tier 3 reasoning (for SAATHI)
            - tap_level (str): current TAP level (for TARKA handoff)
            - rep_level (str): current rep level (for RUPAK handoff)

    Returns:
        List of message dicts ready for OpenAI chat.completions.create()
    """
    agent = AGENTS[agent_key]
    topic = context.get("topic", "this chemistry concept")

    if agent_key == "SAATHI":
        t1  = context.get("t1",  "an answer")
        t3  = context.get("t3",  "their reasoning")
        opening = (
            f"Namaste! I can see you chose **'{t1}'** because: *'{t3}'*. "
            f"Let's explore that thinking about **{topic}** together. "
            f"I have one question for you to start..."
        )
    elif agent_key == "TARKA":
        tap = context.get("tap_level", "Level 1")
        opening = (
            f"Namaste! I am Tarka AI — your Argumentation Coach. "
            f"You have been exploring **{topic}**. "
            f"Now it is time to build a scientific argument. "
            f"Your current argument is at **{tap}**. "
            f"Let us work toward a complete Claim → Evidence → Reasoning → Rebuttal. "
            f"Start by stating your CLAIM: What do you believe is scientifically true about {topic}?"
        )
    elif agent_key == "RUPAK":
        rep = context.get("rep_level", "macroscopic level")
        opening = (
            f"Namaste! I am Rupak AI — your Modelling Guide. "
            f"You have been working on **{topic}** "
            f"and currently explaining it at the **{rep}**. "
            f"Let us explore ALL three levels: what we observe, "
            f"what the particles are doing, and what the symbols mean. "
            f"Begin: describe everything you can OBSERVE about this phenomenon."
        )
    else:
        opening = f"Namaste! Let us explore {topic} together."

    return [
        {"role": "system",    "content": agent["system_prompt"]},
        {"role": "assistant", "content": opening},
    ]

# ── SHARED CALL FUNCTION ──────────────────────────────────────────────────────

def call_agent(agent_key: str, messages: list[dict], api_key: str) -> dict:
    """
    Calls OpenAI API for the specified agent and returns a structured result.

    Args:
        agent_key: "SAATHI", "TARKA", or "RUPAK"
        messages:  Full conversation history including system prompt
        api_key:   OpenAI API key from st.secrets

    Returns:
        dict with keys:
            - content (str):    The AI's full response text
            - tap_level (str|None):  TAP level signal if detected
            - rep_level (str|None):  Representational level if detected
            - redirect (str|None):   Target agent if redirect requested
            - mastery (bool):        True if MASTERY_DETECTED
            - triadic (bool):        True if TRIADIC_FLUENCY_DETECTED
    """
    from openai import OpenAI
    client  = OpenAI(api_key=api_key)
    resp    = client.chat.completions.create(
        model    = "gpt-4o",
        messages = messages,
    )
    content = resp.choices[0].message.content

    return {
        "content":   content,
        "tap_level": detect_tap_level(content),
        "rep_level": detect_rep_level(content),
        "redirect":  detect_redirect(content),
        "mastery":   "[MASTERY_DETECTED]" in content,
        "triadic":   "[TRIADIC_FLUENCY_DETECTED]" in content,
    }
