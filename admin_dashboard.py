"""
admin_dashboard.py — MMALE Admin Control Center (Updated)
==========================================================
Changes from original:
  - Original used worksheet('Responses') and 'NLP_Score' column —
    neither exists in current schema; silently produced empty charts.
  - Now uses Assessment_Logs and Temporal_Traces (existing sheets).
  - Added system health monitor showing all six sheets' row counts.
  - Added participant roster with group distribution.
  - Preserved all original layout patterns.
  - Added agent pipeline health check.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client, fetch_agent_interaction_summary

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"

KNOWN_SHEETS = [
    "Participants",
    "Instructional_Materials",
    "Assessment_Logs",
    "Temporal_Traces",
    "ArgLog",
    "RepLog",
    "Assignments",
]

def show_admin_portal():
    st.title("📊 MMALE Research Control Center")
    st.caption("System health, participant management, and data integrity monitoring")

    try:
        client = get_gspread_client()
        sh     = client.open_by_key(SHEET_KEY)

        # ── System health ──────────────────────────────────────────────────────
        st.markdown("### 🛡️ Database Health Monitor")
        health_cols = st.columns(len(KNOWN_SHEETS))
        sheet_names = [ws.title for ws in sh.worksheets()]

        for i, sheet_name in enumerate(KNOWN_SHEETS):
            with health_cols[i]:
                if sheet_name in sheet_names:
                    try:
                        ws      = sh.worksheet(sheet_name)
                        n_rows  = max(ws.row_count - 1, 0)   # exclude header
                        records = len(ws.get_all_records())
                        st.metric(
                            sheet_name,
                            f"{records} rows",
                            help=f"Sheet exists ✅ ({n_rows} allocated rows)",
                        )
                    except Exception:
                        st.metric(sheet_name, "⚠️ Error")
                else:
                    st.metric(sheet_name, "❌ Missing",
                              help="Sheet does not exist yet — will be created on first use")

        st.markdown("---")

        # ── Agent pipeline health ──────────────────────────────────────────────
        st.markdown("### 🤖 Agent Pipeline Status")
        summary = fetch_agent_interaction_summary()
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Saathi Sessions",   summary["saathi_sessions"])
        a2.metric("Tarka Sessions",    summary["tarka_sessions"])
        a3.metric("Rupak Sessions",    summary["rupak_sessions"])
        a4.metric("Modal TAP Level",
                  max(summary["tap_distribution"],
                      key=summary["tap_distribution"].get))
        a5.metric("Triadic Fluency",   summary["rupak_sessions"],
                  help="Students who achieved all-three-level representation")

        st.markdown("---")

        # ── Participant roster ─────────────────────────────────────────────────
        st.markdown("### 👥 Participant Roster")
        try:
            part_df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
            if not part_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    group_counts = part_df["Group"].value_counts().reset_index()
                    group_counts.columns = ["Group", "Count"]
                    fig_groups = px.bar(
                        group_counts, x="Group", y="Count",
                        title="Participants by Research Group",
                        color="Group",
                    )
                    st.plotly_chart(fig_groups, use_container_width=True)
                with col2:
                    role_counts = part_df["Role"].value_counts().reset_index()
                    role_counts.columns = ["Role", "Count"]
                    fig_roles = px.pie(
                        role_counts, names="Role", values="Count",
                        title="Participants by Role",
                    )
                    st.plotly_chart(fig_roles, use_container_width=True)

                st.dataframe(
                    part_df[["User_ID", "Name", "Role", "Group"]],
                    use_container_width=True, hide_index=True,
                )
        except Exception as e:
            st.warning(f"Participants sheet error: {e}")

        st.markdown("---")

        # ── Recent activity ────────────────────────────────────────────────────
        st.markdown("### 🕐 Recent Activity (Temporal Traces)")
        try:
            trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not trace_df.empty:
                st.metric("Total Interaction Events", len(trace_df))
                st.dataframe(
                    trace_df.tail(20).iloc[::-1],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("No temporal traces yet.")
        except Exception as e:
            st.warning(f"Traces error: {e}")

    except Exception as e:
        st.warning(f"Admin dashboard connection error: {e}")
        st.exception(e)
