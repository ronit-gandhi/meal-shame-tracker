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
else:
    df = pd.DataFrame(columns=["Timestamp", "Name", "Meal", "Calories", "Description", "Comments"])

# Input form
st.subheader("Log a new meal")
with st.form("meal_form"):
    name = st.selectbox("Your Name", ["Ronit", "Brother"])
    meal = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0, max_value=3000, step=10)
    desc = st.text_area("Description (optional)")
    submit = st.form_submit_button("Submit")

if submit and meal:
    new_row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Meal": meal,
        "Calories": calories,
        "Description": desc,
        "Comments": ""
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success(f"{meal} logged successfully! 🔥")
    st.experimental_rerun()

# Display feed
st.subheader("🔥 Meal Feed")
if df.empty:
    st.info("No meals logged yet.")
else:
    df = df.sort_values("Timestamp", ascending=False)
    for i, row in df.iterrows():
        st.markdown(f"### 🍽️ {row['Meal']} ({row['Calories']} cal)")
        st.write(f"**{row['Name']}**: {row['Description']}")
        st.caption(f"Logged at {row['Timestamp']}")
        with st.expander("💬 Comments / Roasts"):
            comments = row['Comments'] or "No comments yet."
            st.write(comments)
            new_comment = st.text_input(f"Add comment for {row['Meal']}", key=row['Timestamp'])
            if st.button(f"Post comment {i}", key=f"c{i}"):
                updated_comments = (comments + "\n" if comments != "No comments yet." else "") + f"{datetime.now().strftime('%H:%M')} - {new_comment}"
                df.at[i, "Comments"] = updated_comments
                df.to_csv(CSV_FILE, index=False)
                st.experimental_rerun()
