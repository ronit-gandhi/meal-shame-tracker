import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Meal Shame Tracker", page_icon="🍗", layout="centered")
st.title("🍗 Meal Shame Tracker 🔥")
st.write("Log your meals and roast your brother mercilessly.")

CSV_FILE = "meals.csv"

# Load existing data
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
else:
    df = pd.DataFrame(columns=["Timestamp", "Name", "Meal", "Calories", "Description", "Comments"])

# Get today's date
today = datetime.now().date()

# Input form
st.subheader("Log a new meal")
with st.form("meal_form"):
    name = st.selectbox("Your Name", ["The Ronit Gandhi", "Himanshu Gandhi, younger brother of ROnit Gandhi, Father of Boba, little bitchboi"])
    meal = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0, max_value=3000, step=10)
    desc = st.text_area("Description (optional)")
    submit = st.form_submit_button("Submit")

if submit and meal:
    new_row = {
        "Timestamp": datetime.now(),
        "Name": name,
        "Meal": meal,
        "Calories": calories,
        "Description": desc,
        "Comments": ""
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success(f"{meal} logged successfully! 🔥")
    st.rerun()

# ----------------------------
# 🔢 Daily Calorie Tracker
# ----------------------------
st.sidebar.header("🔥 Daily Calorie Totals")
df_today = df[df["Timestamp"].dt.date == today]

for user in df["Name"].unique():
    user_calories = df_today[df_today["Name"] == user]["Calories"].sum()
    st.sidebar.write(f"**{user}**: {int(user_calories)} cal")

# ----------------------------
# 🔥 Meal Feed
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
                updated_comments = comments + ("" if comments == "" else "\n") + f"{datetime.now().strftime('%H:%M')} - {new_comment}"
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
