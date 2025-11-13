import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time


# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Meal Shame Tracker", page_icon="🍗", layout="centered")
st.title("🍗 Meal Shame Tracker 🔥")

CENTRAL_TZ = ZoneInfo("America/Chicago")

# ===== Supabase connection =====
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== Get data =====
@st.cache_data(ttl=60)
def load_data():
    """Load meal data from Supabase safely."""
    try:
        response = supabase.table("meals").select("*").order("timestamp", desc=True).execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return pd.DataFrame(columns=["id", "timestamp", "name", "meal", "calories", "description", "comments"])
        # Convert to datetime safely
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=["id", "timestamp", "name", "meal", "calories", "description", "comments"])

df = load_data()

# ========================
# Compute today's meals (fixed timezone handling)
# ========================
if not df.empty:
    # Ensure proper timezone conversion
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["timestamp"] = df["timestamp"].dt.tz_convert(CENTRAL_TZ)

    # Normalize and filter for today's date in Central Time
    today = datetime.now(CENTRAL_TZ).date()
    df_today = df[df["timestamp"].dt.tz_localize(None).dt.date == today]
else:
    df_today = pd.DataFrame(columns=["id", "timestamp", "name", "meal", "calories", "description", "comments"])


# ========================
# Input form
# ========================
st.subheader("Log a new meal")
with st.form("meal_form"):
    name = st.selectbox("Your Name", ["Lord Ronit Gandhi", "Commoner Himanshu Gandhi"])
    meal = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0, max_value=3000, step=10)
    desc = st.text_area("Description (optional)")
    submit = st.form_submit_button("Submit")

if submit and meal.strip():
    # 🐷 Piggy Check
    limits = {"Lord Ronit Gandhi": 2000, "Commoner Himanshu Gandhi": 1850}
    limit = limits.get(name, 2000)
    if calories > limit:
        diff = calories - limit
        if diff > 500:
            st.error(f"🐷 {name}, {diff} cal over the limit?! Might as well start spending your day in the mud, baconator lookin ass. Built like a bowlinhg ball, charlottes web lookin ass. no wonder your hair is greasy with all that butter you been drinking, looking like peppa pig obtuse sidekick.")
        elif diff > 200:
            st.error(f"🐷 {name}, {diff} cal over. Maybe lay off the snacks, piggy.")
        else:
            st.error(f"🐷 {name}, you just tipped over by {diff} cal. Still counts. 🐖")


        time.sleep(3)

    # Save meal
    supabase.table("meals").insert({
        "name": name,
        "meal": meal.strip(),
        "calories": calories,
        "description": desc.strip(),
        "timestamp": datetime.now(CENTRAL_TZ).isoformat()
    }).execute()
    st.success(f"{meal} logged successfully! 🔥")
    st.cache_data.clear()
    st.rerun()


# ========================
# Today's Meals
# ========================
st.subheader("Today's Meals 🍽️")
if df_today.empty:
    st.info("No meals logged today.")
else:
    for i, row in df_today.iterrows():
        st.markdown(f"### 🍽️ {row['meal']} ({int(row['calories'])} cal)")
        st.write(f"**{row['name']}**: {row['description'] or ''}")
        st.caption(f"Logged at {row['timestamp'].strftime('%H:%M')}")

        # Comments section
        with st.expander("💬 Comments / Roasts"):
            comments = row.get("comments") or "No comments yet."
            st.write(comments)
            new_comment = st.text_input(f"Add comment for {row['meal']}", key=f"comment_input_{i}")
            if st.button(f"Post comment for {row['meal']}", key=f"comment_btn_{i}"):
                if new_comment.strip():
                    updated = (
                        comments + "\n" if comments != "No comments yet." else ""
                    ) + f"{datetime.now(CENTRAL_TZ).strftime('%H:%M')} - {new_comment.strip()}"
                    supabase.table("meals").update({"comments": updated}).eq("id", row["id"]).execute()
                    st.success("Comment added!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Comment cannot be empty!")

# ========================
# Leaderboard
# ========================
st.sidebar.header("🏆 Leaderboard of Shame (Today)")
if not df_today.empty:
    leaderboard = (
        df_today.groupby("name")["calories"]
        .agg(["sum", "count"])
        .sort_values("sum", ascending=False)
        .rename(columns={"sum": "Total Calories", "count": "Meals"})
    )
    st.sidebar.dataframe(leaderboard)


# ========================
# ========================
# 🔥 Progress Dashboard
# ========================
st.sidebar.header("🔥 Progress Dashboard")

# --- CONFIG ---
calorie_goal = {
    "Lord Ronit Gandhi": 2000,   # personal target
    "Commoner Himanshu Gandhi": 1850
}

TDEE = {
    "Lord Ronit Gandhi": 2500,   # estimated maintenance
    "Commoner Himanshu Gandhi": 2400
}

if not df.empty:
    df["date"] = df["timestamp"].dt.date
    days_logged = df["date"].nunique()

    totals = df.groupby("name")["calories"].sum()
    daily_avg = df.groupby("name")["calories"].mean()

    for person in totals.index:
        total = totals[person]
        avg_per_day = daily_avg[person]
        days = len(df[df["name"] == person]["date"].unique())
        goal = calorie_goal.get(person, 2000)
        tdee = TDEE.get(person, 2500)

        # --- 1️⃣ Goal-based progress ---
        goal_expected = goal * days
        goal_diff = total - goal_expected
        goal_lbs = goal_diff / 3500.0

        # --- 2️⃣ TDEE-based progress ---
        tdee_expected = tdee * days
        tdee_diff = total - tdee_expected
        tdee_lbs = tdee_diff / 3500.0

        # --- Display ---
        st.sidebar.subheader(person)

        st.sidebar.markdown("**🎯 Calorie Goal Comparison**")
        st.sidebar.progress(min(total / goal_expected, 1.0))
        st.sidebar.write(f"**Total eaten:** {int(total)} cal")
        st.sidebar.write(f"**Goal (×{days} days):** {goal_expected} cal")
        st.sidebar.markdown(
            f"**Δ from Goal:** <span style='color:{'red' if goal_diff>0 else 'green'}'>{goal_diff:+,} cal</span>",
            unsafe_allow_html=True
        )
    #    st.sidebar.markdown(
    #        f"**≈ {abs(goal_lbs):.2f} lb {'gained' if goal_diff>0 else 'lost'} vs goal**"
    #    )

        st.sidebar.markdown("**💪 TDEE Comparison**")
        st.sidebar.progress(min(avg_per_day / tdee, 1.0))
        st.sidebar.write(f"**Avg per day:** {avg_per_day:.0f} cal")
        st.sidebar.write(f"**TDEE:** {tdee} cal/day")
        st.sidebar.markdown(
            f"**Δ from TDEE:** <span style='color:{'red' if tdee_diff>0 else 'green'}'>{tdee_diff:+,} cal</span>",
            unsafe_allow_html=True
        )
        st.sidebar.markdown(
            f"**≈ {abs(tdee_lbs):.2f} lb {'gained' if tdee_diff>0 else 'lost'} vs TDEE**"
        )

        st.sidebar.divider()
else:
    st.sidebar.info("No data yet to calculate progress.")

# ========================
# History Chart
# ========================
st.subheader("📈 Calorie History")
if not df.empty:
    df["date"] = df["timestamp"].dt.date
    chart_data = df.groupby(["date", "name"])["calories"].sum().unstack().fillna(0)

    fig, ax = plt.subplots()
    chart_data.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Daily Calorie Intake")
    ax.set_ylabel("Calories")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(title="Name")
    st.pyplot(fig)
else:
    st.info("No meal data yet — log a meal to start tracking!")






# ========================
# 📅 Archive & History Viewer
# ========================
st.subheader("📅 Archive & History")

if not df.empty:
    all_dates = sorted(df["timestamp"].dt.date.unique(), reverse=True)
    selected_date = st.date_input("Select a date to view meals:", value=today, min_value=min(all_dates), max_value=max(all_dates))
    
    df_selected = df[df["timestamp"].dt.date == selected_date]
    if df_selected.empty:
        st.info(f"No meals logged on {selected_date}.")
    else:
        st.markdown(f"### Meals on {selected_date.strftime('%b %d, %Y')}")
        for i, row in df_selected.iterrows():
            st.markdown(f"#### 🍴 {row['meal']} ({int(row['calories'])} cal)")
            st.write(f"**{row['name']}**: {row['description'] or ''}")
            st.caption(f"Logged at {row['timestamp'].strftime('%H:%M')}")

        # optional summary per person
        st.write("#### Daily Summary")
        day_summary = (
            df_selected.groupby("name")["calories"]
            .agg(["sum", "count"])
            .rename(columns={"sum": "Total Calories", "count": "Meals"})
            .sort_values("Total Calories", ascending=False)
        )
        st.dataframe(day_summary)

else:
    st.info("No archived data yet — log a meal first!")

