# 🏠 Hostel Room Allocation System
### Hostel Warden Committee, Goa Institute of Management

---

## What This System Does

| Action | What happens |
|--------|-------------|
| **Allocate room** | Enter one or more GIM IDs — student details are pulled from the Students sheet automatically |
| **Vacate room** | Enter GIM IDs of students leaving — their rooms are freed instantly |
| **View allocations** | See every student and their current room, with filters and CSV export |
| **View room status** | See which rooms are Full, Partial, or Vacant with colour coding |
| **View vacancy summary** | Quick overview of available beds by room type and gender |

All changes are **automatically saved back to `hostel_data.xlsx`** — no formulas, no macros needed.

---

## Files in This Package

```
hostel_system/
│
├── hostel_data.xlsx          ← Your data file (Students, Rooms, Allocation sheets)
├── hostel_engine.py          ← Core logic (allocation rules, Excel read/write)
├── streamlit_app.py          ← Web application (recommended — runs in browser)
├── hostel_app.py             ← Terminal application (fallback, no browser needed)
├── requirements.txt          ← Python dependencies
├── test_hostel.py            ← Automated tests (for technical staff)
└── README.md                 ← This file
```

---

## Excel Data Format

Your `hostel_data.xlsx` must have exactly these three sheets:

### Students Sheet
| Column | Description | Example |
|--------|-------------|---------|
| GIM ID | Unique student ID | GIM001 |
| Name | Full name | Amit Sharma |
| Gender | Male or Female | Male |
| AC Preference | AC or Non-AC | AC |

### Rooms Sheet
| Column | Description | Example |
|--------|-------------|---------|
| Room No | Unique room number | 101 |
| Room Type | AC or Non-AC | AC |
| Gender Allowed | Male or Female | Male |

### Allocation Sheet
*Managed automatically by the system. Do not edit it manually.*

---

## Business Rules (built-in, automatic)

1. **Gender separation** — Male students only go to Male rooms; Female to Female
2. **AC matching** — AC students only go to AC rooms; Non-AC to Non-AC rooms
3. **Double occupancy** — Each room holds exactly 2 students
4. **First-come-first-served** — The lowest available room number is always assigned first
5. **No duplicates** — A student already allocated a room cannot be allocated twice
6. **Instant vacating** — Vacated rooms are immediately available for new students
7. **Bulk input** — Multiple GIM IDs can be entered separated by spaces in all functions

---

## Option A — Deploy via Streamlit Community Cloud (Recommended)

This makes the app accessible from any browser, on any device, with no installation required for wardens.

### Step 1 — Prepare your GitHub repository

1. Create a free account at [github.com](https://github.com) if you don't have one
2. Click **New repository** → name it (e.g. `hostel-allocation`) → set to **Private** → click **Create repository**
3. Upload all files from this folder into the repository:
   - `hostel_engine.py`
   - `streamlit_app.py`
   - `hostel_data.xlsx`
   - `requirements.txt`
   - `README.md`

   To upload: open your repository on GitHub → click **Add file** → **Upload files** → drag and drop all files → click **Commit changes**

> ⚠️ **Important:** Every time you update `hostel_data.xlsx` locally, you must re-upload it to GitHub for the deployed app to reflect the latest data. See the note on data persistence below.

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account
2. Click **New app**
3. Fill in the form:
   - **Repository:** select your `hostel-allocation` repo
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Click **Deploy**

Streamlit will build and launch your app in about a minute. You'll get a public URL like:
```
https://your-name-hostel-allocation.streamlit.app
```

Share this link with all wardens — no installation needed on their end.

### Step 3 — Update the app later

Whenever you need to update the code or re-upload a fresh `hostel_data.xlsx`:
1. Go to your GitHub repository
2. Click the file → **Edit** (pencil icon) for code, or **Upload files** for the Excel file
3. Commit the change
4. Streamlit Cloud automatically redeploys within seconds

---

## ⚠️ Important Note on Data Persistence

Streamlit Community Cloud **does not permanently save file changes** made through the app. This means:

- Allocations made through the web app are written to `hostel_data.xlsx` on the server, but **reset whenever the app redeploys or restarts**
- This is fine for **demonstration or read-only viewing**
- For **live production use** (where allocations must be permanently saved), use one of these approaches:

| Approach | Complexity | Best for |
|----------|-----------|----------|
| **Run locally** (see Option B below) | Low | Single-computer use in the warden's office |
| **Google Sheets backend** | Medium | Multi-user, always-on web access |
| **Cloud storage (AWS S3 / Google Drive API)** | High | Full cloud deployment with persistence |

For most college hostel scenarios, **running locally** is the simplest and most reliable option.

---

## Option B — Run Locally (Terminal or Browser)

Use this if you want changes saved permanently to your Excel file on your own computer.

### Step 1 — Install Python
Download from [python.org/downloads](https://www.python.org/downloads/) — version 3.9 or later.

### Step 2 — Install required libraries
Open a terminal / command prompt in this folder and run:
```
pip install -r requirements.txt
```

### Step 3 — Place your Excel file
Put your `hostel_data.xlsx` (with Students, Rooms, and Allocation sheets) in the same folder as the scripts.

### Step 4 — Run the web app (recommended)
```
streamlit run streamlit_app.py
```
Opens automatically in your browser at `http://localhost:8501`.

### Or run the terminal app (no browser needed)
```
python hostel_app.py
```

---

## Entering GIM IDs

All input fields across both the web app and terminal app accept:
- A **single** GIM ID: `GIM001`
- **Multiple** GIM IDs separated by **spaces**: `GIM001 GIM003 GIM005`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Data file not found" | Ensure `hostel_data.xlsx` is in the same folder as the scripts |
| "GIM ID not found in Students sheet" | Add the student to the Students sheet in Excel first, then try again |
| "No room available" | All matching rooms are full; a student must vacate first |
| Changes not saving locally | Close Excel before running the app, then re-open after |
| App won't start | Run `pip install -r requirements.txt` to install dependencies |
| Streamlit app resets allocations | This is expected on cloud — use local mode for permanent saves |

---

## Adding More Rooms

1. Open `hostel_data.xlsx` in Excel
2. Go to the **Rooms** sheet
3. Add new rows with Room No, Room Type (AC/Non-AC), Gender Allowed (Male/Female)
4. Save and close
5. New rooms are available immediately on the next app run

---

## For IT Staff — Architecture

```
streamlit_app.py       (Web UI — Streamlit)
hostel_app.py          (Terminal UI — fallback)
       │
       └── HostelSystem class  (hostel_engine.py)
                │
                ├── allocate(gim_id, name, gender, ac_pref)
                ├── vacate(list_of_gim_ids)
                ├── lookup_student(gim_id)
                ├── get_vacancy_summary()
                ├── get_current_allocation()
                └── get_room_detail()
                         │
                         └── hostel_data.xlsx
                              ├── Students   (read — source of truth for student details)
                              ├── Rooms      (read — source of truth for room configuration)
                              └── Allocation (read + write — managed by the system)
```

The engine has zero UI dependencies — any frontend (Streamlit, Flask, Django) can be built on top of it by importing `HostelSystem` directly.

---

*Built for the Hostel Warden Committee, Goa Institute of Management. No SQL, no macros, no formulas required.*
