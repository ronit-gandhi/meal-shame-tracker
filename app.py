# -------------------------------------------------------
# Meal Shame Tracker 🍗🔥
# Streamlit app for Ronit & his brother
# -------------------------------------------------------

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Meal Shame Tracker", page_icon="🍗", layout="centered")
st.title("🍗 Meal Shame Tracker 🔥")
st.write("Hold each other accountable (and roast each other's meals).")

# ------------------ GOOGLE SHEETS SETUP ------------------
# You'll need to create a Google Cloud service account & JSON key file
# Steps:
# 1. Go to https://console.cloud.google.com/
# 2. Create a project → Enable Google Sheets API
# 3. Create credentials → Service Account → JSON key
# 4. Share your target Google Sheet with that service account email
# 5. Save JSON key file as 'creds.json' in the same folder

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

# Create or open sheet
sheet_name = "MealShame"
try:
    sheet = client.open(sheet_name).sheet1
except:
    sh = client.create(sheet_name)
    sheet = sh.sheet1
    sheet.append_row(["Timestamp", "Name", "Meal", "Calories", "Description", "Comments"])

# Load data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ------------------ INPUT FORM ------------------
st.subheader("Log a new meal")
with st.form("meal_form"):
    name = st.selectbox("Your Name", ["Ronit", "Brother"])
    meal = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0, max_value=3000, step=10)
    desc = st.text_area("Description (optional)")
    submit = st.form_submit_button("Submit")

if submit:
    new_row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, meal, calories, desc, ""]
    sheet.append_row(new_row)
    st.success(f"{meal} logged successfully! 🔥")

# ------------------ DISPLAY FEED ------------------
st.subheader("🔥 Meal Feed")

if df.empty:
    st.info("No meals logged yet.")
else:
    df = df.sort_values("Timestamp", ascending=False)
    for _, row in df.iterrows():
        st.markdown(f"### 🍽️ {row['Meal']} ({row['Calories']} cal)")
        st.write(f"**{row['Name']}**: {row['Description']}")
        st.caption(f"Logged at {row['Timestamp']}")

        # Comments section
        with st.expander("💬 Comments / Roasts"):
            existing_comments = str(row.get("Comments", ""))
            st.write(existing_comments if existing_comments else "No comments yet.")
            new_comment = st.text_input(f"Add comment for {row['Meal']}", key=row['Timestamp'])
            if st.button(f"Post comment on {row['Meal']}", key=row['Meal']):
                updated_comment = existing_comments + f"\n{datetime.now().strftime('%H:%M')} - {new_comment}"
                cell = df.index.get_loc(_) + 2  # +2 because Google Sheets starts at row 2
                sheet.update_cell(cell, 6, updated_comment)
                st.success("Comment added!")
                st.experimental_rerun()
