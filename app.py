import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# Set timezone to Central Time
CENTRAL_TZ = ZoneInfo("America/Chicago")
now = datetime.now(CENTRAL_TZ)
today = now.date()

st.set_page_config(page_title="Meal Shame Tracker", page_icon="🍗", layout="centered")
st.title("🍗 Meal Shame Tracker 🔥")
st.write("Log your meals and roast your brother mercilessly.")

CSV_FILE = "meals.csv"

# Load existing data
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Timestamp"] = df["Timestamp"].dt.tz_localize("UTC").dt.tz_convert(CENTRAL_TZ)
else:
    df = pd.DataFrame(columns=["Timestamp", "Name", "Meal", "Calories", "Description", "Comments"])

name_map = {
    "Himanshu Gandhi, younger brother of ROnit Gandhi, Father of Boba, little bitchboi": "Commoner Himanshu",
    "The Ronit Gandhi": "Lord Ronit"
}
df["Name"] = df["Name"].replace(name_map)


# Input form
st.subheader("Log a new meal")
with st.form("meal_form"):
    name = st.selectbox("Your Name", [
        "Lord Ronit Gandhi",
        "Commoner Himanshu Gandhi"
    ])
    meal = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0, max_value=3000, step=10)
    desc = st.text_area("Description (optional)")
    submit = st.form_submit_button("Submit")

if submit and meal:
    new_row = {
        "Timestamp": now.isoformat(),  # store with timezone info
        "Name": name,
        "Meal": meal,
        "Calories": calories,
        "Description": desc,
        "Comments": ""
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success(f"{meal} logged successfully! 🔥")
    if submit and meal:
        new_row = {
            "Timestamp": now.isoformat(),
            "Name": name,
            "Meal": meal,
            "Calories": calories,
            "Description": desc,
            "Comments": ""
        }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    # 🐷 Piggy limit roast
    calorie_limit = {
        "Ronit": 2000,
        "Himanshu": 1800
    }

    limit = calorie_limit.get(name, 2000)
    excess = calories - limit
    if excess > 0:
        if excess > 500:
            st.error(f"🐷 {name}, {excess} cal over the limit?! Might as well start spending your day in the mud, baconator lookin ass. Built like a bowlinhg ball, charlottes web lookin ass. no wonder your hair is greasy with all that butter you been drinking, looking like peppa pig obtuse sidekick.")
        elif excess > 200:
            st.error(f"🐷 {name}, {excess} cal over. Maybe lay off the snacks, piggy.")
        else:
            st.error(f"🐷 {name}, you just tipped over by {excess} cal. Still counts. 🐖")

    st.success(f"{meal} logged successfully! 🔥")
    st.rerun()

    st.rerun()

# ----------------------------
# 🔢 Daily Calorie Tracker
# ----------------------------
st.sidebar.header("🔥 Daily Calorie Totals")
df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.tz_convert(CENTRAL_TZ)
df_today = df[df["Timestamp"].dt.date == today]

for user in df["Name"].unique():
    user_calories = df_today[df_today["Name"] == user]["Calories"].sum()
    st.sidebar.write(f"**{user}**: {int(user_calories)} cal")

# ----------------------------
# Leaderboard
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.header("🏆 Leaderboard of Shame (Today)")

leaderboard = (
    df_today.groupby("Name")["Calories"]
    .agg(["sum", "count"])
    .sort_values("sum", ascending=False)
    .rename(columns={"sum": "Total Calories", "count": "Meals Logged"})
)

# ----------------------------
# All-time tracker
# ----------------------------

st.sidebar.dataframe(leaderboard)

st.sidebar.markdown("---")
st.sidebar.header("🧮 All-Time Calorie Balance")

# Reuse name map if you have one
calorie_limit = {
    "Ronit": 2000,
    "Himanshu": 1800
}

df["Date"] = df["Timestamp"].dt.date

for user in df["Name"].unique():
    user_df = df[df["Name"] == user]
    days_logged = user_df["Date"].nunique()
    total_cals = user_df["Calories"].sum()
    daily_limit = calorie_limit.get(user, 2000)
    total_limit = days_logged * daily_limit
    balance = total_cals - total_limit
    fat_change = balance / 3500  # 1 lb fat ≈ 3500 kcal

    if balance > 0:
        emoji = "🍔"
        result = f"**+{balance}** cal surplus ({fat_change:.2f} lbs gained) {emoji}"
    else:
        emoji = "💪"
        result = f"**{balance}** cal deficit ({fat_change:.2f} lbs lost) {emoji}"

    st.sidebar.write(f"**{user}**: {total_cals:,} cal vs {total_limit:,} goal")
    st.sidebar.caption(result)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 App Usage Stats")

unique_days = df["Timestamp"].dt.date.nunique()
st.sidebar.write(f"**Days Logged:** {unique_days} total day(s)")



# ----------------------------
# 🔥 Meal Feed (Today)
# ----------------------------
st.subheader("Today's Meals 🍽️")

if df_today.empty:
    st.info("No meals logged today.")
else:
    df_today = df_today.sort_values("Timestamp", ascending=False)
    for i, row in df_today.iterrows():
        st.markdown(f"### 🍽️ {row['Meal']} ({int(row['Calories'])} cal)")
        st.write(f"**{row['Name']}**: {row['Description']}")
        st.caption(f"Logged at {row['Timestamp'].strftime('%H:%M')}")
        with st.expander("💬 Comments / Roasts"):
            comments = row['Comments'] or "No comments yet."
            st.write(comments)
            new_comment = st.text_input(f"Add comment for {row['Meal']}", key=row['Timestamp'])
            if st.button(f"Post comment {i}", key=f"c{i}"):
                comments = str(comments) if pd.notna(comments) else ""
                if comments.strip().lower() == "no comments yet.":
                    comments = ""
                updated_comments = comments + ("" if comments == "" else "\n") + f"{now.strftime('%H:%M')} - {new_comment}"
                df.at[i, "Comments"] = updated_comments
                df.to_csv(CSV_FILE, index=False)
                st.rerun()

# ----------------------------
# 📦 Archive Older Meals
# ----------------------------
with st.expander("📜 Show Previous Days"):
    df_past = df[df["Timestamp"].dt.date < today]
    if df_past.empty:
        st.write("No archived meals.")
    else:
        for i, row in df_past.sort_values("Timestamp", ascending=False).iterrows():
            st.markdown(f"### 🍽️ {row['Meal']} ({int(row['Calories'])} cal)")
            st.write(f"**{row['Name']}**: {row['Description']}")
            st.caption(f"Logged on {row['Timestamp'].strftime('%Y-%m-%d %H:%M')}")
            with st.expander("💬 Comments / Roasts", expanded=False):
                st.write(row['Comments'] or "No comments yet.")

# ----------------------------
# History
# ----------------------------

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.subheader("📈 Calorie History")

if df.empty:
    st.info("No data to plot yet.")
else:
    df["Date"] = df["Timestamp"].dt.date
    chart_data = df.groupby(["Date", "Name"])["Calories"].sum().unstack().fillna(0)

    fig, ax = plt.subplots()
    chart_data.plot(kind="line", marker="o", ax=ax)

    ax.set_title("Daily Calorie Intake")
    ax.set_ylabel("Calories")
    ax.set_xlabel("Date")

    # Format x-axis to clean date display
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))  # e.g., Nov 10
    ax.xaxis.set_major_locator(mdates.DayLocator())
    fig.autofmt_xdate()  # auto rotate labels

    ax.grid(True)
    ax.legend(title="Name")
    st.pyplot(fig)
