import streamlit as st
import requests
from collections import defaultdict
import re
import math

API_BASE = "https://hike-tracker-clean.onrender.com"

st.set_page_config(page_title="Trails Explorer", layout="wide")

# --------------------------------------------------
# Styles
# --------------------------------------------------
st.markdown(
    """
    <style>
    .trail-card {
        background: linear-gradient(135deg, #0f172a, #022c22);
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 14px;
        border: 1px solid #14532d;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .trail-left {
        max-width: 75%;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: #1f2937;
        color: #e5e7eb;
        margin-right: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("## 🥾 Trails Explorer")
st.caption("Browse National Park Service trails and log your hikes.")

# --------------------------------------------------
# Name normalization
# --------------------------------------------------
def normalize_name(name: str) -> str:
    """
    Normalize NPS segment names into a clean trail name.
    """
    if not name:
        return ""

    n = name.strip()

    # Remove leading separators (/ - —)
    n = re.sub(r"^[\/\-–—]+\s*", "", n)

    # Remove leading campsite / segment codes (1A3, 12B, 3C2, etc.)
    n = re.sub(r"^[0-9]+[A-Z]+[0-9]*\s+", "", n)

    # Remove trailing maintenance codes (HS-46D, TR-12A, etc.)
    n = re.sub(r"\s+-\s*[A-Z]{1,4}-?\d+[A-Z]?$", "", n)

    # Remove trailing "Section ..." labels
    n = re.sub(r"\s+Section.*$", "", n, flags=re.IGNORECASE)

    # Collapse extra spaces
    n = re.sub(r"\s{2,}", " ", n)

    return n.strip()

def km_to_miles(km: float) -> float:
    return km * 0.621371

def safe(val):
    return val if val not in [None, "", "null"] else None

def trail_category(name: str) -> str:
    n = name.lower()
    if "spur" in n:
        return "🏕️ Spur"
    if "loop" in n:
        return "🔁 Loop"
    if "connector" in n or "conn" in n:
        return "🔗 Connector"
    return "🥾 Trail"

# --------------------------------------------------
# Cached loader
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_trails():
    resp = requests.get(f"{API_BASE}/trails", timeout=15)
    resp.raise_for_status()
    return resp.json()

# --------------------------------------------------
# Load data
# --------------------------------------------------
with st.spinner("⏳ Loading trails…"):
    segments = load_trails()

if not segments:
    st.warning("No trails available.")
    st.stop()

# --------------------------------------------------
# Collapse segments into trails
# --------------------------------------------------
trails = defaultdict(lambda: {
    "length_km": 0.0,
    "segment_count": 0,
    "designation": None,
    "surface": None,
    "notes": None,
})

for seg in segments:
    raw_name = seg.get("name")
    if not raw_name:
        continue

    name = normalize_name(raw_name)
    if not name:
        continue

    # 🔥 NEW RULE: only keep things that are explicitly trails
    if "trail" not in name.lower():
        continue

    trails[name]["length_km"] += seg.get("length_km", 0) or 0
    trails[name]["segment_count"] += 1

    for field in ["designation", "surface", "notes"]:
        if not trails[name][field]:
            trails[name][field] = safe(seg.get(field))

# --------------------------------------------------
# Search + pagination
# --------------------------------------------------
c1, c2 = st.columns([4, 1])
with c1:
    search = st.text_input("🔎 Search trails", placeholder="Start typing a trail name…")
with c2:
    page_size = st.selectbox("Per page", [10, 20, 30], index=1)

trail_items = sorted(trails.items(), key=lambda x: x[0].lower())

if search:
    trail_items = [(n, d) for n, d in trail_items if search.lower() in n.lower()]

total = len(trail_items)
if total == 0:
    st.info("🌲 No trails found.")
    st.stop()

total_pages = max(1, math.ceil(total / page_size))
page = st.number_input("Page", 1, total_pages, 1)

start = (page - 1) * page_size
end = start + page_size

st.markdown(f"**Showing {start + 1}–{min(end, total)} of {total} trails**")
st.markdown("---")

# --------------------------------------------------
# Trail Cards
# --------------------------------------------------
for name, data in trail_items[start:end]:
    miles = km_to_miles(data["length_km"])
    category = trail_category(name)

    col_card, col_btn = st.columns([6, 1], vertical_alignment="center")

    with col_card:
        st.markdown(
            f"""
            <div class="trail-card">
                <div class="trail-left">
                    <h3 style="margin:0;">🥾 {name}</h3>
                    <div style="margin-top:6px;">
                        <span class="badge">📏 {miles:.2f} mi</span>
                        <span class="badge">{category}</span>
                        <span class="badge">🔢 {data['segment_count']} segments</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_btn:
        if st.button("➕ Log Hike", key=name):
            try:
                requests.post(
                    f"{API_BASE}/api/my-hikes",
                    json={
                        "trail_name": name,
                        "length_km": data["length_km"],
                        "time_hours": round(data["length_km"] * 0.6, 2),
                    },
                    timeout=5,
                )
                st.switch_page("pages/2_My_Hikes.py")
            except Exception as e:
                st.error(f"Failed to log hike: {e}")
