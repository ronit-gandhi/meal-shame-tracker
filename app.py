import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
# Compute today's meals
# ========================
today = datetime.now(CENTRAL_TZ).date()
if not df.empty:
    df_today = df[df["timestamp"].dt.date == today]
else:
    df_today = pd.DataFrame(columns=df.columns)

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
# Calorie Goals & Progress
# ========================
st.sidebar.header("🔥 Progress Tracker")

# --- personal limits ---
calorie_limit = {
    "Lord Ronit Gandhi": 2000,
    "Commoner Himanshu Gandhi": 1800
}

if not df.empty:
    # total calories by person
    totals = df.groupby("name")["calories"].sum()

    for person, total in totals.items():
        limit = calorie_limit.get(person, 2000)
        diff = total - limit * len(df["timestamp"].dt.date.unique())  # expected over all days logged
        lbs_change = diff / 3500.0  # rough 1 lb per 3500 cal rule
        color = "green" if diff < 0 else "red"

        st.sidebar.subheader(person)
        st.sidebar.progress(min(total / (limit * len(df["timestamp"].dt.date.unique())), 1.0))
        st.sidebar.write(f"**Total eaten:** {int(total)} cal")
        st.sidebar.write(f"**Expected:** {limit * len(df['timestamp'].dt.date.unique())} cal")
        st.sidebar.markdown(
            f"**Difference:** <span style='color:{color}'>{int(diff)} cal</span>", unsafe_allow_html=True
        )
        st.sidebar.markdown(f"**≈ {lbs_change:.2f} lb {'lost' if diff < 0 else 'gained'}**")
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

