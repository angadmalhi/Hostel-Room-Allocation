"""
streamlit_app.py
================
Streamlit web UI for the Hostel Room Allocation System.

Run:
    streamlit run streamlit_app.py

Requirements:
    pip install streamlit pandas openpyxl
"""

import streamlit as st
import pandas as pd
from hostel_engine import HostelSystem

DATA_FILE = "hostel_data.xlsx"

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Hostel Room Allocation",
    page_icon="🏠",
    layout="wide",
)

# ── shared style ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── engine (cached so Excel isn't re-read on every widget interaction) ────────

@st.cache_resource
def get_engine():
    return HostelSystem(DATA_FILE)

def refresh():
    """Clear cache so the next call re-reads fresh data from Excel."""
    st.cache_resource.clear()

hs = get_engine()

# ── sidebar navigation ────────────────────────────────────────────────────────

st.sidebar.title("🏠 Hostel System")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "➕ Allocate Room", "🚪 Vacate Room", "📋 All Allocations", "🏨 Room Status"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Changes are saved to `hostel_data.xlsx` automatically.")


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

        # ── top-level metrics ─────────────────────────────────────────────────
        total_beds      = int(summary["Total_Beds"].sum())
        occupied_beds   = int(summary["Occupied_Beds"].sum())
        available_beds  = int(summary["Available_Beds"].sum())
        total_students  = len(alloc)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Beds",      total_beds)
        c2.metric("Occupied",        occupied_beds)
        c3.metric("Available",       available_beds)
        c4.metric("Students Housed", total_students)

        st.markdown("---")

        # ── vacancy breakdown table ───────────────────────────────────────────
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
            refresh()
            hs = get_engine()
            gim_ids = raw.split()

            for gim_id in gim_ids:
                student = hs.lookup_student(gim_id)
                if student is None:
                    st.error(f"**{gim_id}** — not found in the Students sheet. Add them to Excel first.")
                    continue

                name    = student["Name"]
                gender  = student["Gender"]
                ac_pref = student["AC Preference"]

                result = hs.allocate(gim_id, name, gender, ac_pref)

                if result["status"] == "success":
                    st.success(f"**{gim_id} — {name}** → {result['message']}")
                elif result["status"] == "already_allocated":
                    st.warning(f"**{gim_id} — {name}** → Already in Room {result['room']}. No change made.")
                elif result["status"] == "no_room":
                    st.error(f"**{gim_id} — {name}** → {result['message']}")
                else:
                    st.error(f"**{gim_id}** → {result['message']}")

            # show a live preview of the allocation sheet after changes
            st.markdown("---")
            st.subheader("Updated Allocations")
            refresh()
            hs = get_engine()
            st.dataframe(hs.get_current_allocation(), use_container_width=True, hide_index=True)


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
            refresh()
            hs = get_engine()
            gim_ids = raw.split()
            result  = hs.vacate(gim_ids)

            if result["vacated"]:
                st.success(f"✅ Vacated: **{', '.join(result['vacated'])}**")
            if result["not_found"]:
                st.warning(f"⚠️ Not found in allocations (no change): **{', '.join(result['not_found'])}**")

            st.markdown("---")
            st.subheader("Updated Allocations")
            refresh()
            hs = get_engine()
            df = hs.get_current_allocation()
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
        # filter controls
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

        # download button
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

    # colour the Status column
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
