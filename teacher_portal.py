"""
teacher_portal.py — MMALE Teacher Research Orchestration Portal (Updated)
==========================================================================
Changes from original:
  - BUG FIX Tab 2: 'Tier_2 (Confidence_Ans)' → 'T2' (column mismatch
    caused blank analytics charts — teachers could not see student data)
  - BUG FIX Tab 2: 'Result' → 'Diagnostic_Result' (same issue)
  - ADDITION Tab 2: Multi-agent progress view showing Saathi/Tarka/Rupak
    completion rates per student so teachers can monitor epistemic practice
    progression, not just Saathi diagnostic outcomes
  - ADDITION Tab 1: Tarka argumentation context field added to module
    deployment form so teachers can provide topic-specific argumentation
    prompts for Tarka AI to use
  - All original functionality (Drive upload, assignment deploy,
    content management) preserved exactly

Column normalisation applied on load — handles both short (T2) and
verbose (Tier_2 (Confidence_Ans)) header variants from Google Sheets.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import (
    save_bulk_concepts, upload_to_drive,
    get_gspread_client, save_assignment,
)
from datetime import datetime

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"

# Column name normalisation — same map as researcher_portal
COL_RENAME = {
    "Tier_1 (Answer)":         "T1",
    "Tier_2 (Confidence_Ans)": "T2",
    "Tier_3 (Reasoning)":      "T3",
    "Tier_4 (Confidence_Rea)": "T4",
    "Tier_5 (Revised_Answer)": "T5",
    "Tier_6 (Revised_Conf)":   "T6",
    "Result":                  "Diagnostic_Result",
}

CONF_MAP = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
TAP_ORDER = ["TAP_1", "TAP_2", "TAP_3", "TAP_4", "TAP_5"]


def _load_logs(sh) -> pd.DataFrame:
    """Load and normalise Assessment_Logs column names."""
    df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    if df.empty:
        return df
    df.rename(columns=COL_RENAME, inplace=True)
    df["Status"]            = df["Status"].astype(str).str.strip().str.upper()
    df["Diagnostic_Result"] = df["Diagnostic_Result"].astype(str).str.strip()
    return df


def show():
    if "user" not in st.session_state:
        st.error("Please login first.")
        st.stop()

    user = st.session_state.user
    st.title("🧑‍🏫 Research Orchestration & Analytics")
    st.info(
        f"Teacher: **{user.get('Name')}** | "
        f"ID: {user.get('User_ID')} | "
        f"Group: {user.get('Group', '—')}"
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Deploy Socratic Module",
        "📊 Student Analytics",
        "📑 Assignments",
        "⚙️ Manage Content",
    ])

    # ── Tab 1: Module Deployment ───────────────────────────────────────────────
    with tab1:
        st.subheader("Create New Socratic Learning Module")
        st.caption(
            "This module deploys to all three agents: Saathi (diagnostic), "
            "Tarka (argumentation), and Rupak (modelling). "
            "Fill in all sections for full multi-agent coverage."
        )

        with st.form("full_deploy_form"):
            col1, col2 = st.columns(2)
            main_t = col1.text_input(
                "Chapter Name (Main Title)",
                placeholder="e.g., Chemical Bonding",
            )
            sub_t = col2.text_input(
                "Specific Concept (Sub Title)",
                placeholder="e.g., Ionic Bonding",
            )
            group = st.selectbox(
                "Assign To Research Group",
                ["School A", "School B", "Control Group"],
            )
            objectives = st.text_area(
                "Learning Objectives (PhD Requirement)",
                placeholder="Describe what the student should be able to explain...",
            )

            st.markdown("---")
            st.subheader("📖 Pedagogical Materials")
            up_files = st.file_uploader(
                "Upload Lesson Materials (PDF/Images)", accept_multiple_files=True
            )
            vid_url = st.text_input("Video Resource URL (YouTube/Google Drive Link)")

            st.markdown("---")
            st.subheader("🔬 Saathi AI — 4-Tier Diagnostic")
            tree = st.text_area(
                "Socratic Logic (Context for Saathi AI)",
                placeholder=(
                    "Describe the key misconceptions for this concept and the "
                    "correct scientific explanation. Example: Students often think "
                    "electrons are inside the nucleus. The correct explanation is..."
                ),
            )
            q_text = st.text_area("Diagnostic Question Text")
            c1, c2 = st.columns(2)
            oa = c1.text_input("Option A (Correct/Distractor)")
            ob = c2.text_input("Option B (Distractor)")
            oc = c1.text_input("Option C (Distractor)")
            od = c2.text_input("Option D (Distractor)")
            correct = st.selectbox("Correct Answer Key", ["A", "B", "C", "D"])

            st.markdown("---")
            st.subheader("⚖️ Tarka AI — Argumentation Context")
            st.caption(
                "Tarka will use this to generate relevant counterarguments "
                "and evidence prompts for this specific concept."
            )
            tarka_context = st.text_area(
                "Key Claim, Evidence, and Counterargument for This Concept",
                placeholder=(
                    "Main scientific claim: [e.g., ionic bonds form because...]\n"
                    "Key evidence students should use: [e.g., electronegativity "
                    "difference, electron transfer data]\n"
                    "Counterargument Tarka should raise: [e.g., some students "
                    "claim covalent bonds are always stronger — challenge this]"
                ),
            )

            st.markdown("---")
            st.subheader("🧬 Rupak AI — Modelling Guidance")
            st.caption(
                "Rupak will use this to prompt students toward the correct "
                "submicroscopic representation for this concept."
            )
            rupak_context = st.text_area(
                "Macroscopic → Submicroscopic → Symbolic Pathway",
                placeholder=(
                    "Macroscopic observation: [e.g., NaCl dissolves in water]\n"
                    "Submicroscopic explanation: [e.g., Na⁺ and Cl⁻ ions "
                    "surrounded by water molecules]\n"
                    "Symbolic representation: [e.g., NaCl → Na⁺(aq) + Cl⁻(aq)]"
                ),
            )

            submit = st.form_submit_button("🚀 Deploy to Student Portals")

            if submit:
                with st.spinner("Uploading materials and syncing database..."):
                    links = []
                    if up_files:
                        for f in up_files:
                            link = upload_to_drive(f)
                            if link:
                                links.append(link)

                    # Combine Socratic tree with Tarka and Rupak contexts
                    combined_tree = (
                        f"[SAATHI] {tree}\n\n"
                        f"[TARKA_CONTEXT] {tarka_context}\n\n"
                        f"[RUPAK_CONTEXT] {rupak_context}"
                    )

                    data = {
                        "sub_title":    sub_t,
                        "objectives":   objectives,
                        "file_link":    ", ".join(links),
                        "video_link":   vid_url,
                        "q_text":       q_text,
                        "oa": oa, "ob": ob, "oc": oc, "od": od,
                        "correct":      correct,
                        "socratic_tree": combined_tree,
                    }

                    success = save_bulk_concepts(user["User_ID"], group, main_t, data)
                    if success:
                        st.success(
                            f"✅ Module '{sub_t}' deployed to {group} "
                            f"with {len(links)} attachment(s)."
                        )
                        st.balloons()

    # ── Tab 2: Student Analytics (FIXED + EXTENDED) ───────────────────────────
    with tab2:
        st.header("📊 Student Progress Analytics")

        try:
            client = get_gspread_client()
            sh = client.open_by_key(SHEET_KEY)
            df = _load_logs(sh)

            if df.empty:
                st.info("Waiting for students to submit diagnostic data...")
            else:
                # ── Section A: Saathi diagnostic analytics ─────────────────────
                st.subheader("🔬 Saathi AI — Diagnostic & Metacognitive Data")

                col_a, col_b = st.columns(2)

                with col_a:
                    st.write("**Confidence Levels by Group**")
                    # FIXED: was 'Tier_2 (Confidence_Ans)' — now normalised to 'T2'
                    t2_col = "T2" if "T2" in df.columns else "Tier_2 (Confidence_Ans)"
                    if t2_col in df.columns:
                        fig1 = px.histogram(
                            df, x=t2_col,
                            color="Group" if "Group" in df.columns else None,
                            barmode="group",
                            category_orders={t2_col: [
                                "Guessing", "Unsure", "Sure", "Very Sure"
                            ]},
                            title="Answer Confidence Distribution",
                            labels={t2_col: "Confidence Level"},
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.warning("T2 confidence column not found in data.")

                with col_b:
                    st.write("**Correctness vs Confidence (Calibration)**")
                    # FIXED: was 'Result' — now normalised to 'Diagnostic_Result'
                    if "Diagnostic_Result" in df.columns and t2_col in df.columns:
                        df["Conf_Num"] = df[t2_col].map(CONF_MAP).fillna(0)
                        df["Acc_Num"]  = df["Diagnostic_Result"].apply(
                            lambda x: 1 if str(x).strip() == "Correct" else 0
                        )
                        fig2 = px.scatter(
                            df, x="Conf_Num", y="Acc_Num",
                            color="Group" if "Group" in df.columns else None,
                            hover_data=["User_ID"],
                            labels={
                                "Conf_Num": "Confidence (1–4)",
                                "Acc_Num":  "Correct (1) / Incorrect (0)",
                            },
                            title="Calibration: Confidence vs Accuracy",
                        )
                        st.plotly_chart(fig2, use_container_width=True)

                # ── Section B: Multi-agent progress tracker (NEW) ──────────────
                st.markdown("---")
                st.subheader("🤖 Multi-Agent Learning Progress")
                st.caption(
                    "Shows each student's progression through the agent ecology. "
                    "Use this to identify students who have completed Saathi but "
                    "have not yet begun Tarka or Rupak."
                )

                # Build per-student progress matrix
                students = df["User_ID"].unique().tolist()
                progress_rows = []

                # Saathi: Status == 'POST' means mastery reached
                saathi_done = set(
                    df[df["Status"] == "POST"]["User_ID"].astype(str).str.upper()
                )

                # Tarka: Status starts with 'TAP_COMPLETE'
                tarka_done = set(
                    df[df["Status"].str.startswith("TAP_COMPLETE", na=False)]
                    ["User_ID"].astype(str).str.upper()
                )

                # Rupak: Status == 'TRIADIC_COMPLETE'
                rupak_done = set(
                    df[df["Status"] == "TRIADIC_COMPLETE"]
                    ["User_ID"].astype(str).str.upper()
                )

                # Highest TAP level per student
                tap_rows = df[df["Status"].str.startswith("TAP_COMPLETE", na=False)].copy()
                tap_level_map = {}
                if not tap_rows.empty:
                    for uid in tap_rows["User_ID"].astype(str).str.upper().unique():
                        statuses = tap_rows[
                            tap_rows["User_ID"].astype(str).str.upper() == uid
                        ]["Status"].tolist()
                        levels = [s.replace("TAP_COMPLETE_", "") for s in statuses]
                        tap_level_map[uid] = max(levels, key=lambda x: TAP_ORDER.index(x)
                                                  if x in TAP_ORDER else -1)

                for uid in students:
                    uid_str = str(uid).upper()
                    progress_rows.append({
                        "Student":        uid_str,
                        "Saathi ✅":      "✅" if uid_str in saathi_done  else "⬜",
                        "Tarka ⚖️":       "✅" if uid_str in tarka_done  else "⬜",
                        "Best TAP Level": tap_level_map.get(uid_str, "—"),
                        "Rupak 🧬":       "✅" if uid_str in rupak_done  else "⬜",
                        "Full Ecology":   (
                            "🎓 Complete"
                            if uid_str in saathi_done
                            and uid_str in tarka_done
                            and uid_str in rupak_done
                            else "In Progress"
                        ),
                    })

                progress_df = pd.DataFrame(progress_rows)
                if not progress_df.empty:
                    completed_count = len(
                        progress_df[progress_df["Full Ecology"] == "🎓 Complete"]
                    )
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Students",       len(progress_df))
                    m2.metric("Completed Saathi",     len(saathi_done))
                    m3.metric("Completed Tarka",      len(tarka_done))
                    m4.metric("Full Ecology Complete", completed_count)

                    st.dataframe(
                        progress_df, use_container_width=True, hide_index=True
                    )

                    # Students needing intervention (completed Saathi, stuck)
                    needs_tarka = [
                        r["Student"] for _, r in progress_df.iterrows()
                        if r["Saathi ✅"] == "✅" and r["Tarka ⚖️"] == "⬜"
                    ]
                    if needs_tarka:
                        st.warning(
                            f"⚠️ **{len(needs_tarka)} student(s) completed Saathi "
                            f"but have not started Tarka:** "
                            f"{', '.join(needs_tarka)}"
                        )

                st.markdown("---")

                # ── Section C: TAP level distribution from ArgLog ──────────────
                st.subheader("⚖️ Argumentation Quality (Tarka AI — ArgLog)")
                try:
                    arg_df = pd.DataFrame(sh.worksheet("ArgLog").get_all_records())
                    if not arg_df.empty:
                        tap_counts = (
                            arg_df.groupby("TAP_Level")
                            .size().reset_index(name="Count")
                        )
                        fig_tap = px.bar(
                            tap_counts, x="TAP_Level", y="Count",
                            color="TAP_Level",
                            title="TAP Level Distribution — Your Students",
                            category_orders={"TAP_Level": TAP_ORDER},
                        )
                        st.plotly_chart(fig_tap, use_container_width=True)
                    else:
                        st.info("No Tarka argumentation data yet.")
                except Exception:
                    st.info("ArgLog not yet created — appears after first Tarka session.")

                # ── Section D: Raw data ────────────────────────────────────────
                st.markdown("---")
                st.subheader("Raw Research Data")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Could not load analytics: {e}")
            st.exception(e)

    # ── Tab 3: Assignments (UNCHANGED) ────────────────────────────────────────
    with tab3:
        st.subheader("Deploy Homework or Post-Tests")
        with st.form("assignment_form"):
            a_title = st.text_input("Assignment Title")
            a_desc  = st.text_area("Instructions")
            a_group = st.selectbox(
                "Target Group", ["School A", "School B"], key="assign_group"
            )
            a_file = st.file_uploader("Upload Worksheet (Optional)", key="assign_file")

            if st.form_submit_button("Post Assignment"):
                file_url = upload_to_drive(a_file) if a_file else ""
                if save_assignment(user["User_ID"], a_group, a_title, a_desc, file_url):
                    st.success(f"✅ Assignment '{a_title}' posted to {a_group}.")

    # ── Tab 4: Content Management (UNCHANGED LOGIC, column safe) ─────────────
    with tab4:
        st.subheader("Active Modules")
        try:
            client = get_gspread_client()
            sh = client.open_by_key(SHEET_KEY)
            m_df = pd.DataFrame(
                sh.worksheet("Instructional_Materials").get_all_records()
            )
            if not m_df.empty:
                # Show only columns that exist in the sheet
                display_cols = [
                    c for c in ["Group", "Main_Title", "Sub_Title", "Date"]
                    if c in m_df.columns
                ]
                st.dataframe(
                    m_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No modules deployed yet.")
        except Exception:
            st.info("No modules found.")
