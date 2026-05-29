"""
researcher_portal.py — MMALE Principal Investigator Dashboard (Updated)
=========================================================================
Complete research analytics portal for the PhD study.

Changes from original:
  - Imports new DB analysis functions (fetch_performance_learning_gap,
    fetch_agent_interaction_summary)
  - Fixes column name mismatch: 'Tier_2 (Confidence_Ans)' → 'T2'
    (original produced all-zero calibration curves due to missing column)
  - Adds Tab 4: Multi-Agent Analytics (TAP + Representational levels)
  - Adds Tab 5: Performance-Learning Gap Analysis (core JOST finding)
  - Adds live study monitoring KPIs across all three agents
  - Preserves all original tabs (Calibration, Sankey, Export) unchanged
  - Adds researcher notes export for JOST paper data section

Sheet dependencies:
  Assessment_Logs  — existing (Saathi four-tier data)
  Temporal_Traces  — existing (all agent chat logs)
  ArgLog           — new (Tarka TAP-level per turn)
  RepLog           — new (Rupak representational level per turn)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import (
    get_gspread_client,
    fetch_performance_learning_gap,
    fetch_agent_interaction_summary,
)

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"

# ── Column name map: actual sheet headers → safe internal names ───────────────
# This resolves the mismatch between what log_assessment writes (T2, T4, T6)
# and what the original portal expected (Tier_2 (Confidence_Ans)).
# We rename on load so all downstream code uses short names.
COL_RENAME = {
    # Possible verbose header variants from older sheet setup
    "Tier_1 (Answer)":          "T1",
    "Tier_2 (Confidence_Ans)":  "T2",
    "Tier_3 (Reasoning)":       "T3",
    "Tier_4 (Confidence_Rea)":  "T4",
    "Tier_5 (Revised_Answer)":  "T5",
    "Tier_6 (Revised_Conf)":    "T6",
    "Module_ID":                "Module_ID",
    "Diagnostic_Result":        "Diagnostic_Result",
    "Status":                   "Status",
    "User_ID":                  "User_ID",
    "Group":                    "Group",
    "Timestamp":                "Timestamp",
}

CONF_MAP_NUM = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
CONF_MAP_INT = {"Guessing": 1,  "Unsure": 2,  "Sure": 3,  "Very Sure": 4}

TAP_ORDER = ["TAP_1", "TAP_2", "TAP_3", "TAP_4", "TAP_5"]
REP_ORDER = ["MONADIC", "BIADIC", "TRIADIC"]

# ── Main entry point ──────────────────────────────────────────────────────────

def show():
    st.title("🔬 PhD Principal Investigator Dashboard")
    st.caption("MMALE Research Analytics — Multimodal Multi-Agent Learning Ecology")

    # ── Live study monitor bar ─────────────────────────────────────────────────
    _render_live_monitor()

    try:
        client  = get_gspread_client()
        sh      = client.open_by_key(SHEET_KEY)
        logs_df = _load_and_clean(sh, "Assessment_Logs")

        if logs_df.empty:
            st.warning("⚠️ No data in Assessment_Logs yet.")
            return

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📉 Calibration & Validity",
            "🔄 Conceptual Flow (Sankey)",
            "📂 Data Export",
            "⚖️🧬 Agent Analytics",
            "🧠 Performance–Learning Gap",
        ])

        with tab1:
            render_calibration_logic(logs_df)

        with tab2:
            st.subheader("Socratic Transformation Map")
            render_dynamic_sankey(logs_df)

        with tab3:
            _render_export(logs_df, sh)

        with tab4:
            _render_agent_analytics(sh)

        with tab5:
            _render_gap_analysis()

    except Exception as e:
        st.error(f"Researcher Portal Error: {e}")
        st.exception(e)

# ── Live study monitor ────────────────────────────────────────────────────────

def _render_live_monitor():
    """Top-level KPI bar showing cross-agent completion pipeline."""
    try:
        summary = fetch_agent_interaction_summary()
        st.markdown("### 📡 Live Study Monitor")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Saathi Completed",   summary["saathi_sessions"],
                  help="Students who reached MASTERY_DETECTED")
        c2.metric("Tarka Completed",    summary["tarka_sessions"],
                  help="Students who reached TAP Level 3+")
        c3.metric("Rupak Completed",    summary["rupak_sessions"],
                  help="Students who achieved Triadic Fluency")
        c4.metric("Mean TAP Turns",     summary["mean_tap_turns"],
                  help="Average turns to reach TAP_3+")
        c5.metric("Mean Rep Turns",     summary["mean_rep_turns"],
                  help="Average turns to reach Triadic Fluency")
        top_tap = max(summary["tap_distribution"],
                      key=summary["tap_distribution"].get)
        c6.metric("Modal TAP Level",    top_tap,
                  help="Most frequent TAP level across all Tarka sessions")
        st.markdown("---")
    except Exception:
        pass   # Monitor failure should not block the rest of the portal

# ── Data loader with column normalisation ─────────────────────────────────────

def _load_and_clean(sh, worksheet_name: str) -> pd.DataFrame:
    """
    Loads a worksheet and normalises column names using COL_RENAME.
    Short names (T1-T6) pass through unchanged.
    Verbose names from older sheet versions are mapped to short names.
    """
    df = pd.DataFrame(sh.worksheet(worksheet_name).get_all_records())
    if df.empty:
        return df
    df.rename(columns=COL_RENAME, inplace=True)
    df["Status"]           = df["Status"].astype(str).str.strip().str.upper()
    df["Diagnostic_Result"] = df["Diagnostic_Result"].astype(str).str.strip()
    return df

# ── Tab 1: Calibration (FIXED) ────────────────────────────────────────────────

def render_calibration_logic(df: pd.DataFrame):
    """
    FIX: original used 'Tier_2 (Confidence_Ans)' which may not match
    actual sheet column name, producing all-zero Conf_Num values.
    Now uses normalised 'T2' column after _load_and_clean().
    """
    st.subheader("Metacognitive Calibration Analysis")
    st.caption(
        "Each point = one student response. "
        "Perfect calibration = points on the red diagonal. "
        "Points above diagonal = overconfident; below = underconfident."
    )

    df = df.copy()

    # T2 column (answer confidence) — handles both short and verbose headers
    t2_col = "T2" if "T2" in df.columns else "Tier_2 (Confidence_Ans)"
    if t2_col not in df.columns:
        st.warning("Confidence column (T2) not found in data — calibration chart unavailable.")
        return

    df["Conf_Num"] = df[t2_col].map(CONF_MAP_NUM).fillna(0)
    df["Acc_Num"]  = df["Diagnostic_Result"].apply(
        lambda x: 100 if str(x).strip() == "Correct" else 0
    )

    # Split by group for cross-condition comparison
    fig = px.scatter(
        df, x="Conf_Num", y="Acc_Num",
        color="Group" if "Group" in df.columns else None,
        trendline="ols",
        labels={"Conf_Num": "Answer Confidence (%)", "Acc_Num": "Actual Accuracy (%)"},
        title="Metacognitive Calibration Curve — All Groups",
        hover_data=["User_ID", "Module_ID"] if "Module_ID" in df.columns else None,
    )
    fig.add_shape(
        type="line", x0=0, y0=0, x1=100, y1=100,
        line=dict(color="Red", dash="dash"),
    )
    fig.add_annotation(
        x=85, y=70, text="Perfect calibration", showarrow=False,
        font=dict(color="red", size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Confidence delta: T2 vs T6 (before vs after AI interaction)
    t6_col = "T6" if "T6" in df.columns else "Tier_6 (Revised_Conf)"
    if t6_col in df.columns and not df[df["Status"] == "POST"].empty:
        st.markdown("#### Confidence Recalibration After AI Interaction")
        post = df[df["Status"] == "POST"].copy()
        post["T2_num"] = post[t2_col].map(CONF_MAP_INT).fillna(0)
        post["T6_num"] = post[t6_col].map(CONF_MAP_INT).fillna(0)
        post["Delta"]  = post["T6_num"] - post["T2_num"]

        fig2 = px.box(
            post, x="Module_ID" if "Module_ID" in post.columns else "Group",
            y="Delta", color="Group" if "Group" in post.columns else None,
            title="Confidence Delta (T6 − T2) by Concept",
            labels={"Delta": "Confidence Change (−3 to +3)"},
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="grey",
                       annotation_text="No change")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Negative delta = calibration (student became less confident after "
            "discovering misconceptions). Positive delta = consolidation. "
            "Near-zero = insufficient epistemic shift — a design concern."
        )

# ── Tab 2: Sankey (PRESERVED) ─────────────────────────────────────────────────

def render_dynamic_sankey(df: pd.DataFrame):
    n_initial_wrong = len(
        df[(df["Status"] == "INITIAL") & (df["Diagnostic_Result"] != "Correct")]
    )
    n_initial_right = len(
        df[(df["Status"] == "INITIAL") & (df["Diagnostic_Result"] == "Correct")]
    )
    n_post_mastery = len(
        df[(df["Status"] == "POST") & (df["Diagnostic_Result"] == "Correct")]
    )
    n_post_error = len(
        df[(df["Status"] == "POST") & (df["Diagnostic_Result"] != "Correct")]
    )

    labels = [
        "Initial: Incorrect", "Initial: Correct",
        "Saathi AI Chat",
        "Post: Mastery", "Post: Persistent Error",
    ]
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20, label=labels,
            color=["#d62728", "#2ca02c", "#1f77b4", "#2ca02c", "#d62728"],
        ),
        link=dict(
            source=[0, 1, 2, 2],
            target=[2, 2, 3, 4],
            value=[
                max(n_initial_wrong, 0.1), max(n_initial_right, 0.1),
                max(n_post_mastery, 0.1),  max(n_post_error,   0.1),
            ],
            color=["rgba(214,39,40,0.3)", "rgba(44,160,44,0.3)",
                   "rgba(44,160,44,0.3)", "rgba(214,39,40,0.3)"],
        ),
    )])
    fig.update_layout(title_text="Saathi AI — Conceptual Change Flow", font_size=13)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Started Incorrect → Mastery",
                n_post_mastery,
                delta=f"{round(n_post_mastery / max(n_initial_wrong,1) * 100, 1)}% conversion")
    col2.metric("Persistent Errors Remaining", n_post_error,
                delta=f"{n_post_error} students need intervention",
                delta_color="inverse")

# ── Tab 3: Export (EXTENDED) ──────────────────────────────────────────────────

def _render_export(logs_df: pd.DataFrame, sh):
    st.subheader("Raw Evidence Hub")

    c1, c2, c3 = st.columns(3)

    with c1:
        csv = logs_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Assessment_Logs CSV", csv, "assessment_logs.csv", "text/csv"
        )

    with c2:
        try:
            trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not trace_df.empty:
                st.download_button(
                    "📥 Temporal_Traces CSV",
                    trace_df.to_csv(index=False).encode("utf-8"),
                    "temporal_traces.csv", "text/csv",
                )
        except Exception:
            st.caption("Temporal_Traces not yet available.")

    with c3:
        gap_df = fetch_performance_learning_gap()
        if not gap_df.empty:
            st.download_button(
                "📥 Performance–Learning Gap CSV",
                gap_df.to_csv(index=False).encode("utf-8"),
                "gap_analysis.csv", "text/csv",
                help="Per-student Tier1 vs Tier3 dissociation data for JOST paper",
            )

    st.markdown("---")
    st.dataframe(logs_df, use_container_width=True)

# ── Tab 4: Multi-Agent Analytics (NEW) ───────────────────────────────────────

def _render_agent_analytics(sh):
    st.subheader("⚖️ Tarka AI — Argumentation Quality (TAP Levels)")

    # ── ArgLog ────────────────────────────────────────────────────────────────
    try:
        arg_df = pd.DataFrame(sh.worksheet("ArgLog").get_all_records())
        if arg_df.empty:
            st.info("ArgLog is empty — Tarka data will appear here once students "
                    "complete argumentation sessions.")
        else:
            arg_df["TAP_Level"] = pd.Categorical(
                arg_df["TAP_Level"], categories=TAP_ORDER, ordered=True
            )

            col1, col2 = st.columns(2)

            with col1:
                # TAP level frequency distribution
                tap_counts = (
                    arg_df.groupby("TAP_Level", observed=True)
                    .size().reset_index(name="Count")
                )
                fig_tap = px.bar(
                    tap_counts, x="TAP_Level", y="Count",
                    color="TAP_Level",
                    color_discrete_map={
                        "TAP_1": "#d62728", "TAP_2": "#ff7f0e",
                        "TAP_3": "#bcbd22", "TAP_4": "#2ca02c",
                        "TAP_5": "#17becf",
                    },
                    title="TAP Level Distribution Across All Tarka Sessions",
                    labels={"TAP_Level": "Toulmin Level", "Count": "Frequency"},
                )
                fig_tap.add_hline(
                    y=arg_df[arg_df["TAP_Level"].isin(["TAP_3","TAP_4","TAP_5"])]
                    .shape[0] / max(len(arg_df), 1) * 100,
                    line_dash="dot", annotation_text="TAP_3+ rate",
                    line_color="green",
                )
                st.plotly_chart(fig_tap, use_container_width=True)

            with col2:
                # Argumentation progression by student (turn-by-turn)
                if "Turn_Number" in arg_df.columns and "User_ID" in arg_df.columns:
                    tap_map = {"TAP_1": 1, "TAP_2": 2, "TAP_3": 3,
                               "TAP_4": 4, "TAP_5": 5, "UNDETECTED": 0}
                    arg_df["TAP_Num"] = arg_df["TAP_Level"].map(tap_map).fillna(0)
                    fig_prog = px.line(
                        arg_df, x="Turn_Number", y="TAP_Num",
                        color="User_ID",
                        title="Argumentation Progression by Student",
                        labels={"Turn_Number": "Interaction Turn",
                                "TAP_Num": "TAP Level (1–5)"},
                    )
                    fig_prog.update_yaxes(
                        tickmode="array",
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=TAP_ORDER,
                    )
                    st.plotly_chart(fig_prog, use_container_width=True)

            # Rebuttal rate (TAP_5 as % of total moves)
            tap5_count = len(arg_df[arg_df["TAP_Level"] == "TAP_5"])
            rebuttal_pct = round(tap5_count / max(len(arg_df), 1) * 100, 1)
            st.metric(
                "Rebuttal Rate (TAP_5 as % of all argumentation moves)",
                f"{rebuttal_pct}%",
                help="Your PhD methodology specifies this as a key quantitative measure",
            )

            # Raw ArgLog
            with st.expander("View Raw ArgLog"):
                st.dataframe(arg_df, use_container_width=True)

    except gspread_missing_error():
        st.info("ArgLog sheet not yet created — will appear after first Tarka session.")
    except Exception as e:
        st.warning(f"ArgLog load error: {e}")

    st.markdown("---")
    st.subheader("🧬 Rupak AI — Representational Fluency (Johnstone's Triangle)")

    # ── RepLog ────────────────────────────────────────────────────────────────
    try:
        rep_df = pd.DataFrame(sh.worksheet("RepLog").get_all_records())
        if rep_df.empty:
            st.info("RepLog is empty — Rupak data will appear here once students "
                    "complete modelling sessions.")
        else:
            rep_df["Rep_Level"] = pd.Categorical(
                rep_df["Rep_Level"], categories=REP_ORDER, ordered=True
            )

            col1, col2 = st.columns(2)

            with col1:
                rep_counts = (
                    rep_df.groupby("Rep_Level", observed=True)
                    .size().reset_index(name="Count")
                )
                fig_rep = px.bar(
                    rep_counts, x="Rep_Level", y="Count",
                    color="Rep_Level",
                    color_discrete_map={
                        "MONADIC":  "#d62728",
                        "BIADIC":   "#ff7f0e",
                        "TRIADIC":  "#2ca02c",
                    },
                    title="Representational Level Distribution (Johnstone's Triangle)",
                    labels={"Rep_Level": "Representational Level",
                            "Count": "Frequency"},
                )
                st.plotly_chart(fig_rep, use_container_width=True)

            with col2:
                if "Turn_Number" in rep_df.columns and "User_ID" in rep_df.columns:
                    rep_map = {"MONADIC": 1, "BIADIC": 2,
                               "TRIADIC": 3, "UNDETECTED": 0}
                    rep_df["Rep_Num"] = rep_df["Rep_Level"].map(rep_map).fillna(0)
                    fig_rprog = px.line(
                        rep_df, x="Turn_Number", y="Rep_Num",
                        color="User_ID",
                        title="Representational Navigation by Student",
                        labels={"Turn_Number": "Interaction Turn",
                                "Rep_Num": "Representational Level (1–3)"},
                    )
                    fig_rprog.update_yaxes(
                        tickmode="array", tickvals=[1, 2, 3],
                        ticktext=["Macroscopic\n(Monadic)",
                                  "Macro+Submicro\n(Biadic)",
                                  "All Three Levels\n(Triadic)"],
                    )
                    st.plotly_chart(fig_rprog, use_container_width=True)

            # Confinement rate
            monadic_rate = round(
                len(rep_df[rep_df["Rep_Level"] == "MONADIC"]) /
                max(len(rep_df), 1) * 100, 1
            )
            triadic_rate = round(
                len(rep_df[rep_df["Rep_Level"] == "TRIADIC"]) /
                max(len(rep_df), 1) * 100, 1
            )
            m1, m2 = st.columns(2)
            m1.metric(
                "Representational Confinement Rate",
                f"{monadic_rate}%",
                help="% of turns where students remained at macroscopic level only",
                delta=f"-{monadic_rate}% from ideal" if monadic_rate > 0 else "0%",
                delta_color="inverse",
            )
            m2.metric(
                "Triadic Fluency Rate",
                f"{triadic_rate}%",
                help="% of turns where students navigated all three Johnstone levels",
            )

            with st.expander("View Raw RepLog"):
                st.dataframe(rep_df, use_container_width=True)

    except Exception as e:
        st.warning(f"RepLog load error: {e}")

# ── Tab 5: Performance-Learning Gap Analysis (NEW) ────────────────────────────

def _render_gap_analysis():
    st.subheader("🧠 Performance–Learning Gap Analysis")
    st.caption(
        "Core empirical finding for JOST paper. "
        "The gap = students who answer correctly (T1) but reason incorrectly (T3). "
        "Operationalised as T1 correctness vs T3 reasoning quality dissociation."
    )

    gap_df = fetch_performance_learning_gap()

    if gap_df.empty:
        st.info("Gap analysis data unavailable — requires both INITIAL and POST "
                "records per student per module.")
        return

    # ── Key gap metrics ────────────────────────────────────────────────────────
    total        = len(gap_df)
    correct_pre  = gap_df["T1_Correct"].sum()
    correct_post = gap_df["T5_Correct"].sum()
    gain         = correct_post - correct_pre

    # The gap: correct T1 answer but incorrect reasoning (T3)
    # T3 reasoning quality requires external coding — we flag rows for analysis
    gap_df["Needs_T3_Coding"] = gap_df["T3_Reasoning"].apply(
        lambda x: len(str(x)) > 10  # has substantive reasoning text
    )
    has_reasoning = gap_df["Needs_T3_Coding"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Student-Module Pairs",    total)
    m2.metric("Correct Before AI (T1)",  int(correct_pre),
              f"{round(correct_pre/max(total,1)*100,1)}%")
    m3.metric("Correct After AI (T5)",   int(correct_post),
              delta=f"+{int(gain)} gain",
              delta_color="normal")
    m4.metric("Responses with T3 Text",  int(has_reasoning),
              help="Available for external argumentation quality coding")

    st.markdown("---")

    # ── Performance vs learning dissociation chart ─────────────────────────────
    st.markdown("#### T1 Correctness vs Confidence Calibration (Performance Side)")
    fig_pre = px.scatter(
        gap_df,
        x="T2_Conf", y="T1_Correct",
        color="Group",
        symbol="T1_Correct",
        hover_data=["User_ID", "Module_ID", "T1_Initial"],
        labels={
            "T2_Conf":    "Initial Confidence (1–4)",
            "T1_Correct": "Initial Answer Correct",
        },
        title="Pre-AI: Confidence vs Correctness (Performance Indicator)",
    )
    st.plotly_chart(fig_pre, use_container_width=True)

    # ── Confidence delta distribution ──────────────────────────────────────────
    st.markdown("#### Confidence Recalibration After AI Interaction")
    fig_delta = px.histogram(
        gap_df, x="Conf_Delta",
        color="Group" if "Group" in gap_df.columns else None,
        nbins=7,
        title="Distribution of Confidence Delta (T6 − T2)",
        labels={"Conf_Delta": "Confidence Change (negative = recalibration)"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_delta.add_vline(
        x=0, line_dash="dash", line_color="red",
        annotation_text="No change",
    )
    st.plotly_chart(fig_delta, use_container_width=True)

    st.caption(
        "**Research interpretation:** Negative confidence delta is epistemically "
        "productive — it indicates students discovered their reasoning was weaker "
        "than they thought (genuine calibration). Positive delta after a correct "
        "post-answer indicates consolidation. Near-zero delta despite answer change "
        "indicates unreflective revision — a sign of performance without learning."
    )

    # ── Per-concept breakdown ──────────────────────────────────────────────────
    st.markdown("#### Per-Concept Performance–Learning Summary")
    if "Module_ID" in gap_df.columns:
        concept_summary = gap_df.groupby("Module_ID").agg(
            N              = ("User_ID", "count"),
            Pre_Correct    = ("T1_Correct", "sum"),
            Post_Correct   = ("T5_Correct", "sum"),
            Mean_Conf_Delta= ("Conf_Delta", "mean"),
        ).reset_index()
        concept_summary["Pre_Acc_%"]  = (
            concept_summary["Pre_Correct"] /
            concept_summary["N"] * 100
        ).round(1)
        concept_summary["Post_Acc_%"] = (
            concept_summary["Post_Correct"] /
            concept_summary["N"] * 100
        ).round(1)
        concept_summary["Learning_Gain_%"] = (
            concept_summary["Post_Acc_%"] -
            concept_summary["Pre_Acc_%"]
        ).round(1)
        concept_summary["Mean_Conf_Delta"] = concept_summary["Mean_Conf_Delta"].round(2)

        st.dataframe(
            concept_summary[[
                "Module_ID", "N",
                "Pre_Acc_%", "Post_Acc_%", "Learning_Gain_%",
                "Mean_Conf_Delta",
            ]],
            use_container_width=True,
            hide_index=True,
        )

    # ── T3 Reasoning export for manual coding ─────────────────────────────────
    st.markdown("#### T3 Reasoning Corpus — Export for Argumentation Quality Coding")
    st.caption(
        "These are students' written reasoning responses (Tier 3). "
        "Export for external TAP-level coding to quantify the "
        "performance–learning gap at the reasoning level."
    )
    t3_export = gap_df[["User_ID", "Group", "Module_ID",
                         "T1_Correct", "T3_Reasoning",
                         "T5_Correct", "Reflection"]].copy()
    t3_export.columns = [
        "Student", "Group", "Concept",
        "Initial_Correct", "Initial_Reasoning",
        "Post_Correct", "Post_Reflection",
    ]
    st.dataframe(t3_export, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Export T3 Reasoning for TAP Coding",
        t3_export.to_csv(index=False).encode("utf-8"),
        "t3_reasoning_for_coding.csv", "text/csv",
    )

# ── Helper: graceful missing-sheet error ──────────────────────────────────────

def gspread_missing_error():
    """Returns the gspread exception class for missing worksheet."""
    try:
        import gspread
        return gspread.WorksheetNotFound
    except Exception:
        return Exception
