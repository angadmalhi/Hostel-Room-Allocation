"""
streamlit_app.py
================
Streamlit web UI for the Hostel Room Allocation System.
After every allocation or vacate, the updated hostel_data.xlsx is
automatically committed back to GitHub so changes are permanent.

Run locally:
    streamlit run streamlit_app.py

Deploy: push to GitHub, connect on share.streamlit.io
"""

import streamlit as st
import pandas as pd
import base64
import requests
from hostel_engine import HostelSystem

DATA_FILE = "hostel_data.xlsx"

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Hostel Room Allocation",
    page_icon="🏠",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── GitHub sync ───────────────────────────────────────────────────────────────

GITHUB_TIMEOUT = 10  # seconds — all GitHub API calls must complete within this

def _github_cfg():
    """Return (token, repo, branch, path) from secrets, or None if not configured."""
    try:
        token  = st.secrets["github"]["token"]
        repo   = st.secrets["github"]["repo"]
        branch = st.secrets["github"].get("branch", "main")
        path   = st.secrets["github"].get("file_path", "hostel_data.xlsx")
        return token, repo, branch, path
    except (KeyError, FileNotFoundError):
        return None


def push_excel_to_github():
    """
    Commits the updated hostel_data.xlsx back to GitHub.
    Skips silently if secrets are not configured (local dev).
    Shows a warning if the push fails — never crashes the app.
    """
    cfg = _github_cfg()
    if cfg is None:
        return
    token, repo, branch, path = cfg

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    try:
        sha_resp = requests.get(api_url, headers=headers,
                                params={"ref": branch}, timeout=GITHUB_TIMEOUT)
        if sha_resp.status_code != 200:
            st.warning(f"⚠️ GitHub sync failed (could not read file SHA: {sha_resp.status_code}). Allocation saved locally.")
            return
        sha = sha_resp.json()["sha"]

        with open(DATA_FILE, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "message": "Auto-update: hostel allocation changed via web app",
            "content": content_b64,
            "sha":     sha,
            "branch":  branch,
        }
        put_resp = requests.put(api_url, headers=headers,
                                json=payload, timeout=GITHUB_TIMEOUT)
        if put_resp.status_code not in (200, 201):
            st.warning(f"⚠️ GitHub sync failed ({put_resp.status_code}). Allocation saved locally.")

    except requests.exceptions.Timeout:
        st.warning("⚠️ GitHub sync timed out. Allocation saved locally — will sync on next action.")
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ GitHub sync error: {e}. Allocation saved locally.")


def pull_excel_from_github():
    """
    Downloads the latest hostel_data.xlsx from GitHub on startup.
    Skips silently if secrets are not configured.
    Never crashes the app — if the pull fails, the existing local file is used.
    """
    cfg = _github_cfg()
    if cfg is None:
        return
    token, repo, branch, path = cfg

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    try:
        resp = requests.get(api_url, headers=headers,
                            params={"ref": branch}, timeout=GITHUB_TIMEOUT)
        if resp.status_code != 200:
            return  # fall back to local file silently

        file_bytes = base64.b64decode(resp.json()["content"])
        with open(DATA_FILE, "wb") as f:
            f.write(file_bytes)

    except requests.exceptions.Timeout:
        pass  # cold start pull timed out — use local file, app still loads
    except requests.exceptions.RequestException:
        pass  # any network error — use local file, app still loads


# Pull latest Excel from GitHub on every fresh page load
pull_excel_from_github()

# ── engine ────────────────────────────────────────────────────────────────────

def get_engine():
    return HostelSystem(DATA_FILE)

hs = get_engine()

# ── sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🏠 Hostel System")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "➕ Allocate Room", "🚪 Vacate Room", "📋 All Allocations", "🏨 Room Status"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Changes are saved to `hostel_data.xlsx` and synced to GitHub automatically.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.caption("Hostel Warden Committee, Goa Institute of Management")
    st.markdown("Overview of current hostel occupancy.")

    try:
        summary = hs.get_vacancy_summary()
        alloc   = hs.get_current_allocation()

        total_beds     = int(summary["Total_Beds"].sum())
        occupied_beds  = int(summary["Occupied_Beds"].sum())
        available_beds = int(summary["Available_Beds"].sum())
        total_students = len(alloc)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Beds",      total_beds)
        c2.metric("Occupied",        occupied_beds)
        c3.metric("Available",       available_beds)
        c4.metric("Students Housed", total_students)

        st.markdown("---")
        st.subheader("Vacancy Breakdown")

        display = summary.rename(columns={
            "Total_Rooms":    "Total Rooms",
            "Total_Beds":     "Total Beds",
            "Occupied_Beds":  "Occupied Beds",
            "Available_Beds": "Available Beds",
        })

        def colour_available(val):
            if isinstance(val, (int, float)):
                return "color: green; font-weight: bold" if val > 0 else "color: red"
            return ""

        st.dataframe(
            display.style.applymap(colour_available, subset=["Available Beds"]),
            use_container_width=True,
            hide_index=True,
        )

    except Exception as e:
        st.error(f"Could not load data: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Allocate Room
# ══════════════════════════════════════════════════════════════════════════════

elif page == "➕ Allocate Room":
    st.title("➕ Allocate Room")
    st.markdown("Enter one or more GIM IDs. Student details are pulled from the Students sheet automatically.")

    raw = st.text_input("GIM ID(s)")

    if st.button("Allocate", type="primary"):
        if not raw.strip():
            st.warning("Please enter at least one GIM ID.")
        else:
            hs      = get_engine()
            gim_ids = raw.split()
            any_change = False

            for gim_id in gim_ids:
                student = hs.lookup_student(gim_id)
                if student is None:
                    st.error(f"**{gim_id}** — not found in the Students sheet. Add them to Excel first.")
                    continue

                name    = student["Name"]
                gender  = student["Gender"]
                ac_pref = student["AC Preference"]
                result  = hs.allocate(gim_id, name, gender, ac_pref)

                if result["status"] == "success":
                    st.success(f"**{gim_id} — {name}** → {result['message']}")
                    any_change = True
                elif result["status"] == "already_allocated":
                    st.warning(f"**{gim_id} — {name}** → Already in Room {result['room']}. No change made.")
                elif result["status"] == "no_room":
                    st.error(f"**{gim_id} — {name}** → {result['message']}")
                else:
                    st.error(f"**{gim_id}** → {result['message']}")

            if any_change:
                with st.spinner("Saving to GitHub..."):
                    push_excel_to_github()

            st.markdown("---")
            st.subheader("Updated Allocations")
            st.dataframe(get_engine().get_current_allocation(), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Vacate Room
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🚪 Vacate Room":
    st.title("🚪 Vacate Room")
    st.markdown("Enter the GIM IDs of students who have left. Their rooms will be freed immediately.")

    raw = st.text_input("GIM ID(s) to vacate")

    if st.button("Vacate", type="primary"):
        if not raw.strip():
            st.warning("Please enter at least one GIM ID.")
        else:
            hs      = get_engine()
            gim_ids = raw.split()
            result  = hs.vacate(gim_ids)

            if result["vacated"]:
                st.success(f"✅ Vacated: **{', '.join(result['vacated'])}**")
                with st.spinner("Saving to GitHub..."):
                    push_excel_to_github()
            if result["not_found"]:
                st.warning(f"⚠️ Not found in allocations (no change): **{', '.join(result['not_found'])}**")

            st.markdown("---")
            st.subheader("Updated Allocations")
            df = get_engine().get_current_allocation()
            if df.empty:
                st.info("No students are currently allocated.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: All Allocations
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📋 All Allocations":
    st.title("📋 All Allocations")

    df = hs.get_current_allocation()

    if df.empty:
        st.info("No students are currently allocated.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            gender_filter = st.selectbox("Filter by Gender", ["All", "Male", "Female"])
        with col2:
            ac_filter = st.selectbox("Filter by AC Preference", ["All", "AC", "Non-AC"])
        with col3:
            search = st.text_input("Search by Name or GIM ID")

        filtered = df.copy()
        if gender_filter != "All":
            filtered = filtered[filtered["Gender"] == gender_filter]
        if ac_filter != "All":
            filtered = filtered[filtered["AC Preference"] == ac_filter]
        if search:
            mask = (
                filtered["GIM ID"].str.contains(search, case=False, na=False) |
                filtered["Student Name"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]

        st.caption(f"Showing {len(filtered)} of {len(df)} records")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download as CSV",
            data=csv,
            file_name="allocations.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Room Status
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🏨 Room Status":
    st.title("🏨 Room Status")
    st.markdown("Per-room occupancy at a glance.")

    df = hs.get_room_detail()

    def colour_status(val):
        if val == "Full":    return "background-color: #f28b82; color: black"
        if val == "Partial": return "background-color: #fdd663; color: black"
        if val == "Vacant":  return "background-color: #81c995; color: black"
        return ""

    col1, col2 = st.columns(2)
    with col1:
        gender_filter = st.selectbox("Filter by Gender", ["All", "Male", "Female"], key="rs_gender")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Vacant", "Partial", "Full"], key="rs_status")

    filtered = df.copy()
    if gender_filter != "All":
        filtered = filtered[filtered["Gender Allowed"] == gender_filter]
    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    st.dataframe(
        filtered.style.applymap(colour_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )
