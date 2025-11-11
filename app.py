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
def load_data():
    data = supabase.table("meals").select("*").order("timestamp", desc=True).execute()
    return pd.DataFrame(data.data)

df = load_data()
if not df.empty and "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
else:
    df = pd.DataFrame(columns=["timestamp", "name", "meal", "calories", "description", "comments"])
today = datetime.now(CENTRAL_TZ).date()

# ===== Input form =====
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
        "meal": meal,
        "calories": calories,
        "description": desc
    }).execute()
    st.success(f"{meal} logged successfully! 🔥")
    st.rerun()

# ===== Today’s Meals =====
st.subheader("Today's Meals 🍽️")
df_today = df[df["timestamp"].dt.date == today]
if df_today.empty:
    st.info("No meals logged today.")
else:
    for i, row in df_today.iterrows():
        st.markdown(f"### 🍽️ {row['meal']} ({row['calories']} cal)")
        st.write(f"**{row['name']}**: {row['description'] or ''}")
        st.caption(f"Logged at {row['timestamp'].strftime('%H:%M')}")
        with st.expander("💬 Comments / Roasts"):
            comments = row["comments"] or "No comments yet."
            st.write(comments)
            new_comment = st.text_input(f"Add comment for {row['meal']}", key=row['id'])
            if st.button(f"Post {i}", key=f"comment_{i}"):
                updated = (comments + "\n" if comments != "No comments yet." else "") + \
                          f"{datetime.now(CENTRAL_TZ).strftime('%H:%M')} - {new_comment}"
                supabase.table("meals").update({"comments": updated}).eq("id", row["id"]).execute()
                st.rerun()

# ===== Leaderboard =====
st.sidebar.header("🏆 Leaderboard of Shame (Today)")
if not df_today.empty:
    leaderboard = (
        df_today.groupby("name")["calories"]
        .agg(["sum", "count"])
        .sort_values("sum", ascending=False)
        .rename(columns={"sum": "Total Calories", "count": "Meals"})
    )
    st.sidebar.dataframe(leaderboard)

# ===== History =====
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
    ax.grid(True)
    ax.legend(title="Name")
    st.pyplot(fig)
