"""
database_manager.py — MMALE Research Database Layer (Updated)
==============================================================
All interactions with Google Sheets are managed here.

Changes from original:
  - log_assessment: hardened against IndexError for agent
    completion events (TAP_COMPLETE, TRIADIC_COMPLETE) that
    have no multiple-choice answer to evaluate
  - log_tap_event: new — records Tarka argumentation quality
    data to dedicated ArgLog sheet (TAP level per turn)
  - log_rep_event: new — records Rupak representational level
    data to dedicated RepLog sheet (Johnstone level per turn)
  - fetch_performance_learning_gap: new — returns per-student
    dataframe showing Tier1 vs Tier3 dissociation for JOST
    analysis (the core empirical finding)
  - fetch_agent_interaction_summary: new — returns cross-agent
    interaction counts and completion rates for the full paper
  - All original functions preserved and unchanged.

Google Sheets structure required (add these two worksheets):
  ArgLog   — columns: Timestamp, User_ID, Group, Module_ID,
                       TAP_Level, Turn_Number, Student_Msg,
                       Agent_Msg
  RepLog   — columns: Timestamp, User_ID, Group, Module_ID,
                       Rep_Level, Turn_Number, Student_Msg,
                       Agent_Msg
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime, timedelta

# ── Research constants ─────────────────────────────────────────────────────────

SHEET_KEY = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"

# Statuses that represent agent-completion events (no multiple-choice answer)
AGENT_COMPLETION_STATUSES = {
    "TAP_COMPLETE_TAP_1", "TAP_COMPLETE_TAP_2", "TAP_COMPLETE_TAP_3",
    "TAP_COMPLETE_TAP_4", "TAP_COMPLETE_TAP_5", "TRIADIC_COMPLETE",
    "BIADIC_COMPLETE",    "MONADIC_COMPLETE",    "TAP_COMPLETE",
}

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# ── 1. Authentication & connection (UNCHANGED) ─────────────────────────────────

def get_creds():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

# ── 2. Core login (UNCHANGED) ──────────────────────────────────────────────────

def check_login(user_id):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        df["User_ID"] = df["User_ID"].astype(str).str.upper().str.strip()
        user_id = str(user_id).upper().strip()
        match = df[df["User_ID"] == user_id]
        return match.iloc[0].to_dict() if not match.empty else None
    except:
        return None

# ── 3. Google Drive integration (UNCHANGED) ────────────────────────────────────

def upload_to_drive(uploaded_file):
    try:
        creds = get_creds()
        service = build("drive", "v3", credentials=creds)
        file_metadata = {
            "name": uploaded_file.name,
            "parents": ["1pA_yM0eW89P2nBPrK_SPrvA5m_p5zKq_"],
        }
        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type
        )
        file = service.files().create(
            body=file_metadata, media_body=media, fields="id, webViewLink"
        ).execute()
        return file.get("webViewLink")
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return None

# ── 4. Assessment logging (HARDENED) ──────────────────────────────────────────

def log_assessment(uid, group, module_id, t1, t2, t3, t4, status,
                   timestamp, t5="N/A", t6="N/A"):
    """
    Records four-tier diagnostic and agent-completion events.

    CHANGE FROM ORIGINAL:
    Agent-completion statuses (TAP_COMPLETE_*, TRIADIC_COMPLETE) do not
    have a multiple-choice answer to evaluate. The function now detects
    these statuses and logs result as 'N/A' rather than crashing with
    an IndexError on values[0].
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.worksheet("Assessment_Logs")

        # Determine result — skip answer check for agent-completion events
        if status in AGENT_COMPLETION_STATUSES:
            result = "N/A"
        else:
            try:
                m_ws = sh.worksheet("Instructional_Materials")
                m_df = pd.DataFrame(m_ws.get_all_records())
                matches = m_df[m_df["Sub_Title"] == module_id]["Correct_Answer"].values
                if len(matches) == 0:
                    result = "N/A"
                else:
                    correct_ans = matches[0]
                    check_val   = t5 if status == "POST" else t1
                    result      = (
                        "Correct"
                        if str(check_val).strip() == str(correct_ans).strip()
                        else "Incorrect"
                    )
            except Exception:
                result = "N/A"

        row = [
            timestamp,
            str(uid).upper(),
            group,
            module_id,
            t1, t2, t3, t4,
            status,
            result,
            t5, t6,
        ]
        ws.append_row(row)
        return True

    except Exception as e:
        st.error(f"Logging Error: {e}")
        return False

# ── 5. Temporal trace logging (UNCHANGED) ─────────────────────────────────────

def log_temporal_trace(uid, event, details):
    """Stores every interaction for micro-genetic / epistemic move analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([
            get_nepal_time(),
            str(uid).upper(),
            event,
            details,
        ])
    except:
        pass

# ── 6. TAP event logging (NEW) ────────────────────────────────────────────────

def log_tap_event(uid, group, module_id, tap_level, turn_number,
                  student_msg, agent_msg):
    """
    Records a single Tarka interaction turn with its TAP level code.

    Writes to ArgLog worksheet. This sheet provides the turn-by-turn
    TAP level distribution data needed for JOST analysis:
      - TAP level frequency distributions across pre/mid/post time points
      - Rebuttal frequency as % of total argumentation moves
      - Longitudinal progression from TAP_1 → TAP_5

    Args:
        uid         : Student User_ID
        group       : Research group (control / Exp_A / Exp_B)
        module_id   : Chemistry concept being argued (e.g. 'Alkali Metals')
        tap_level   : String code: 'TAP_1' through 'TAP_5' or None
        turn_number : Integer turn count within this Tarka session
        student_msg : Raw student message this turn
        agent_msg   : Raw Tarka AI response this turn
    """
    try:
        client = get_gspread_client()
        sh     = client.open_by_key(SHEET_KEY)

        # Create ArgLog sheet if it does not exist
        try:
            ws = sh.worksheet("ArgLog")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title="ArgLog", rows=2000, cols=8)
            ws.append_row([
                "Timestamp", "User_ID", "Group", "Module_ID",
                "TAP_Level", "Turn_Number", "Student_Msg", "Agent_Msg",
            ])

        ws.append_row([
            get_nepal_time(),
            str(uid).upper(),
            group,
            module_id,
            str(tap_level) if tap_level else "UNDETECTED",
            turn_number,
            student_msg[:500],   # truncate for sheet cell limit
            agent_msg[:500],
        ])
        return True
    except Exception as e:
        st.error(f"TAP Log Error: {e}")
        return False

# ── 7. Representational level logging (NEW) ────────────────────────────────────

def log_rep_event(uid, group, module_id, rep_level, turn_number,
                  student_msg, agent_msg):
    """
    Records a single Rupak interaction turn with its representational level.

    Writes to RepLog worksheet. This sheet provides the data for:
      - Johnstone's triangle navigation analysis
      - Representational confinement detection
        (students stuck at MONADIC across multiple turns)
      - Pre/post representational fluency comparison

    Args:
        uid         : Student User_ID
        group       : Research group
        module_id   : Chemistry concept being modelled
        rep_level   : 'MONADIC', 'BIADIC', or 'TRIADIC' (or None)
        turn_number : Integer turn count within this Rupak session
        student_msg : Raw student message this turn
        agent_msg   : Raw Rupak AI response this turn
    """
    try:
        client = get_gspread_client()
        sh     = client.open_by_key(SHEET_KEY)

        # Create RepLog sheet if it does not exist
        try:
            ws = sh.worksheet("RepLog")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title="RepLog", rows=2000, cols=8)
            ws.append_row([
                "Timestamp", "User_ID", "Group", "Module_ID",
                "Rep_Level", "Turn_Number", "Student_Msg", "Agent_Msg",
            ])

        ws.append_row([
            get_nepal_time(),
            str(uid).upper(),
            group,
            module_id,
            str(rep_level) if rep_level else "UNDETECTED",
            turn_number,
            student_msg[:500],
            agent_msg[:500],
        ])
        return True
    except Exception as e:
        st.error(f"Rep Log Error: {e}")
        return False

# ── 8. Performance-learning gap analysis (NEW) ────────────────────────────────

def fetch_performance_learning_gap(uid=None):
    """
    Returns a DataFrame quantifying the performance-learning gap
    per student per module — the core empirical claim of the JOST paper.

    The gap is operationalised as the dissociation between:
      Tier 1 (answer correctness — performance indicator)
      Tier 3 (reasoning quality — learning indicator, coded externally)

    For each student-module pair with both INITIAL and POST records,
    returns columns:
      User_ID, Group, Module_ID,
      T1_Initial (answer before AI),
      T1_Correct (bool — did they get it right initially?),
      T5_Post    (answer after AI),
      T5_Correct (bool — did they get it right post-AI?),
      T2_Conf    (initial answer confidence),
      T6_Conf    (post-AI answer confidence),
      Conf_Delta (T6 - T2 numerical — calibration measure),
      Status_Progression (INITIAL→POST path)

    Args:
        uid: If provided, filters to one student. If None, returns all.

    Returns:
        pd.DataFrame or empty DataFrame on error.
    """
    conf_map = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}

    try:
        client  = get_gspread_client()
        sh      = client.open_by_key(SHEET_KEY)
        log_df  = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if log_df.empty:
            return pd.DataFrame()

        if uid:
            log_df = log_df[
                log_df["User_ID"].astype(str).str.upper() == uid.upper()
            ]

        # Load correct answers for automated marking
        m_df = pd.DataFrame(
            sh.worksheet("Instructional_Materials").get_all_records()
        )
        correct_map = dict(zip(
            m_df["Sub_Title"].astype(str),
            m_df["Correct_Answer"].astype(str),
        ))

        records = []
        grouped = log_df.groupby(["User_ID", "Module_ID"])

        for (user, module), grp in grouped:
            initial_rows = grp[grp["Status"] == "INITIAL"]
            post_rows    = grp[grp["Status"] == "POST"]

            if initial_rows.empty or post_rows.empty:
                continue

            init = initial_rows.iloc[0]
            post = post_rows.iloc[0]
            correct_ans = correct_map.get(str(module), "")

            t1_correct = (
                str(init.get("T1", "")).strip() == correct_ans.strip()
            )
            t5_correct = (
                str(post.get("T5", "")).strip() == correct_ans.strip()
            )

            t2_num = conf_map.get(str(init.get("T2", "Guessing")), 1)
            t6_num = conf_map.get(str(post.get("T6", "Guessing")), 1)

            records.append({
                "User_ID":            str(user).upper(),
                "Group":              str(init.get("Group", "")),
                "Module_ID":          str(module),
                "T1_Initial":         init.get("T1", ""),
                "T1_Correct":         t1_correct,
                "T3_Reasoning":       init.get("T3", ""),
                "T5_Post":            post.get("T5", ""),
                "T5_Correct":         t5_correct,
                "T2_Conf":            t2_num,
                "T6_Conf":            t6_num,
                "Conf_Delta":         t6_num - t2_num,
                "Reflection":         post.get("T3", ""),
                "Status_Progression": "INITIAL→POST",
            })

        return pd.DataFrame(records)

    except Exception as e:
        st.error(f"Gap Analysis Error: {e}")
        return pd.DataFrame()

# ── 9. Agent interaction summary (NEW) ────────────────────────────────────────

def fetch_agent_interaction_summary():
    """
    Returns cross-agent interaction counts and completion rates.
    Used in researcher_portal.py for study monitoring and
    in the JOST paper's methods/findings sections.

    Returns a dict with keys:
      saathi_sessions  (int): students who completed Saathi
      tarka_sessions   (int): students who completed Tarka (TAP_3+)
      rupak_sessions   (int): students who achieved triadic fluency
      tap_distribution (dict): {TAP_1: n, TAP_2: n, ...}
      rep_distribution (dict): {MONADIC: n, BIADIC: n, TRIADIC: n}
      mean_tap_turns   (float): avg turns to reach TAP_3+
      mean_rep_turns   (float): avg turns to reach TRIADIC
    """
    summary = {
        "saathi_sessions":  0,
        "tarka_sessions":   0,
        "rupak_sessions":   0,
        "tap_distribution": {"TAP_1": 0, "TAP_2": 0, "TAP_3": 0,
                             "TAP_4": 0, "TAP_5": 0},
        "rep_distribution": {"MONADIC": 0, "BIADIC": 0, "TRIADIC": 0},
        "mean_tap_turns":   0.0,
        "mean_rep_turns":   0.0,
    }

    try:
        client = get_gspread_client()
        sh     = client.open_by_key(SHEET_KEY)
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if log_df.empty:
            return summary

        summary["saathi_sessions"] = len(
            log_df[log_df["Status"] == "POST"]["User_ID"].unique()
        )
        tap_statuses = log_df["Status"].astype(str)
        summary["tarka_sessions"] = len(
            log_df[
                tap_statuses.str.startswith("TAP_COMPLETE")
            ]["User_ID"].unique()
        )
        summary["rupak_sessions"] = len(
            log_df[
                log_df["Status"] == "TRIADIC_COMPLETE"
            ]["User_ID"].unique()
        )

        # TAP level distribution from ArgLog
        try:
            arg_df = pd.DataFrame(sh.worksheet("ArgLog").get_all_records())
            if not arg_df.empty:
                for level in ["TAP_1", "TAP_2", "TAP_3", "TAP_4", "TAP_5"]:
                    summary["tap_distribution"][level] = int(
                        (arg_df["TAP_Level"] == level).sum()
                    )
                # Mean turns to TAP_3+
                high_tap = arg_df[
                    arg_df["TAP_Level"].isin(["TAP_3", "TAP_4", "TAP_5"])
                ]
                if not high_tap.empty:
                    summary["mean_tap_turns"] = round(
                        high_tap.groupby("User_ID")["Turn_Number"].min().mean(), 1
                    )
        except Exception:
            pass

        # Representational level distribution from RepLog
        try:
            rep_df = pd.DataFrame(sh.worksheet("RepLog").get_all_records())
            if not rep_df.empty:
                for level in ["MONADIC", "BIADIC", "TRIADIC"]:
                    summary["rep_distribution"][level] = int(
                        (rep_df["Rep_Level"] == level).sum()
                    )
                triadic_rows = rep_df[rep_df["Rep_Level"] == "TRIADIC"]
                if not triadic_rows.empty:
                    summary["mean_rep_turns"] = round(
                        triadic_rows.groupby("User_ID")["Turn_Number"].min().mean(), 1
                    )
        except Exception:
            pass

        return summary

    except Exception as e:
        st.error(f"Summary Error: {e}")
        return summary

# ── 10. Chat history fetch (UNCHANGED) ────────────────────────────────────────

def fetch_chat_history(uid, module_id):
    """Enables Socratic continuity by reloading previous messages on app reload."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        if df.empty:
            return []
        mask = (
            (df["User_ID"].astype(str).str.upper() == uid.upper()) &
            (df["Event"] == "CHAT_MSG") &
            (df["Details"].str.contains(module_id, na=False))
        )
        filtered = df[mask]
        history  = []
        for _, row in filtered.iterrows():
            content = (
                row["Details"].split("| Content: ")[-1]
                if "| Content: " in row["Details"]
                else row["Details"]
            )
            history.append({"role": "user", "content": content})
        return history
    except:
        return []

# ── 11. Teacher tools (UNCHANGED) ─────────────────────────────────────────────

def save_bulk_concepts(teacher_id, group, main_title, data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.worksheet("Instructional_Materials")
        row = [
            datetime.now().strftime("%Y-%m-%d"), teacher_id, group, main_title,
            data["sub_title"], data["objectives"], data["file_link"],
            data["video_link"], data["q_text"], data["oa"], data["ob"],
            data["oc"], data["od"], data["correct"], data["socratic_tree"],
        ]
        ws.append_row(row)
        return True
    except:
        return False

def save_assignment(teacher_id, group, title, desc, file_url):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.worksheet("Assignments")
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d"),
            teacher_id, group, title, desc, file_url,
        ])
        return True
    except:
        return False
