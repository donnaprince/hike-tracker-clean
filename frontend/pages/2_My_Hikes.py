import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

API_BASE = "https://hike-tracker-clean.onrender.com"

st.set_page_config(page_title="My Hikes", layout="wide")

# --------------------------------------------------
# Header with Export button (RIGHT-ALIGNED)
# --------------------------------------------------
title_col, export_col = st.columns([6, 1], vertical_alignment="center")

with title_col:
    st.markdown("## Completed Hikes")
    st.caption("Your logged adventures")

with export_col:
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    export_placeholder = st.empty()

# --------------------------------------------------
# Fetch hikes
# --------------------------------------------------
try:
    r = requests.get(f"{API_BASE}/api/my-hikes", timeout=5)
    r.raise_for_status()
    hikes = r.json()
except Exception:
    st.error("Could not load hikes from backend")
    st.stop()

if not hikes:
    st.info("No hikes logged yet. Explore trails and log your first hike!")
    st.stop()

# --------------------------------------------------
# Normalize data
# --------------------------------------------------
df = pd.DataFrame(hikes)

df["date"] = pd.to_datetime(df["completed_at"])
df["month"] = df["date"].dt.strftime("%Y-%m")
df["miles"] = (df["length_km"] * 0.621371).round(2)

with export_placeholder:
    st.download_button(
        "⬇️ Export CSV",
        df.to_csv(index=False),
        file_name="my_hikes.csv",
        mime="text/csv",
        width="stretch"
    )

# --------------------------------------------------
# Summary stats
# --------------------------------------------------
total_hikes = len(df)
total_miles = df["miles"].sum().round(2)
total_hours = df.get("time_hours", pd.Series([0])).sum().round(2)

c1, c2, c3 = st.columns(3)
c1.metric("Total Hikes", total_hikes)
c2.metric("Total Miles", total_miles)
c3.metric("Total Hours", total_hours)

st.markdown("---")

# --------------------------------------------------
# Activity Overview
# --------------------------------------------------
st.subheader("Activity Overview")
col1, col2 = st.columns(2)

# ---- Hikes per Month ----
with col1:
    hikes_month = (
        df.groupby("month")
        .size()
        .reset_index(name="count")
        .sort_values("month")
    )

    fig = px.bar(
        hikes_month,
        x="month",
        y="count",
        title="Hikes per Month",
        color_discrete_sequence=["#22c55e"]
    )

    fig.update_layout(
        xaxis=dict(type="category"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        dragmode=False
    )

    st.plotly_chart(fig, width="stretch", config={"staticPlot": True})

# ---- Miles per Month ----
with col2:
    miles_month = (
        df.groupby("month")["miles"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    ymax = max(1, miles_month["miles"].max() * 1.2)

    fig = px.line(
        miles_month,
        x="month",
        y="miles",
        markers=True,
        title="Miles per Month",
        color_discrete_sequence=["#38bdf8"]
    )

    fig.update_layout(
        xaxis=dict(type="category"),
        yaxis=dict(range=[0, ymax], tickformat=".2f"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        dragmode=False
    )

    st.plotly_chart(fig, width="stretch", config={"staticPlot": True})

# --------------------------------------------------
# 🎯 Goal Progress (Animated + Messaging)
# --------------------------------------------------
st.markdown("---")
st.subheader("Progress Toward Goal")

goal = st.slider("Goal (miles)", 5, 100, 30)

progress_ratio = min(total_miles / goal, 1.0)
progress_pct = int(progress_ratio * 100)

goal_hit = total_miles >= goal
bar_color = "#22c55e" if goal_hit else "#38bdf8"

st.markdown(
    f"""
    <style>
    div[data-testid="stProgress"] > div > div {{
        background-color: {bar_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

progress_placeholder = st.empty()
progress = 0.0

while progress < progress_ratio:
    progress += 0.01
    progress_placeholder.progress(min(progress, progress_ratio))
    time.sleep(0.01)

progress_placeholder.progress(progress_ratio)

if goal_hit:
    st.success(f"🎉 Goal achieved! {total_miles:.2f} / {goal} miles")
else:
    st.caption(f"🚶 You’re **{progress_pct}% there** — {total_miles:.2f} of {goal} miles")

# --------------------------------------------------
# 🗑️ Completed Hike Cards + DELETE
# --------------------------------------------------
st.markdown("---")
st.subheader("Completed Hikes")

for hike in hikes:
    miles = round(hike["length_km"] * 0.621371, 2)
    date = hike["completed_at"][:10]
    hours = hike.get("time_hours", "—")
    hike_id = hike.get("_id")

    card_col, delete_col = st.columns([6, 1], vertical_alignment="center")

    with card_col:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0f172a, #022c22);
                border-radius: 16px;
                padding: 18px 22px;
                margin-bottom: 14px;
                border: 1px solid #14532d;
            ">
                <h3 style="margin:0; color:#e5f9f0;">🥾 {hike['trail_name']}</h3>
                <div style="opacity:.8; margin-top:6px;">
                    📏 {miles} miles &nbsp; • &nbsp;
                    ⏱ {hours} hrs &nbsp; • &nbsp;
                    📅 {date}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with delete_col:
        confirm_key = f"confirm_delete_{hike_id}"

        if st.button("🗑️", key=f"delete_{hike_id}"):
            st.session_state[confirm_key] = True

        if st.session_state.get(confirm_key):
            st.warning("Delete this hike?")

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button("Confirm", key=f"yes_{hike_id}"):
                    try:
                        requests.delete(
                            f"{API_BASE}/api/my-hikes/{hike_id}",
                            timeout=5
                        )
                        st.session_state.pop(confirm_key, None)
                        st.success("Hike deleted")
                        st.rerun()
                    except Exception:
                        st.error("Failed to delete hike")

            with cancel_col:
                if st.button("Cancel", key=f"no_{hike_id}"):
                    st.session_state.pop(confirm_key, None)
