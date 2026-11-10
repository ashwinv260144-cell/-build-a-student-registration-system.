import base64
import os
import re
import sqlite3
from datetime import datetime

import streamlit as st

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
BLUE = "#024b6e"          # taken from the CAIAS logo
BLUE_DARK = "#013247"
BLUE_LIGHT = "#e6f1f6"
DB_FILE = "registrations.db"
LOGO_FILE = "logo.png"
REG_PATTERN = re.compile(r"^CAUG26-\d{4}$")   # only year 26 is accepted
PROGRAMS = ["BCA Full Stack", "BCA Data Science", "BCA AI and ML"]

st.set_page_config(page_title="CAIAS Registration", page_icon="🎓", layout="centered")


# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                likes_college TEXT,
                campus_rating INTEGER,
                teacher_rating INTEGER,
                suggestion TEXT,
                registered_at TEXT
            )
            """
        )


def reg_exists(reg_no):
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM students WHERE reg_no = ?", (reg_no,)).fetchone()
    return row is not None


def save_student(data):
    """Returns True if saved, False if the registration number already exists."""
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO students
                (reg_no, name, program, likes_college, campus_rating,
                 teacher_rating, suggestion, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["reg_no"],
                    data["name"],
                    data["program"],
                    data["likes_college"],
                    data["campus_rating"],
                    data["teacher_rating"],
                    data["suggestion"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
        return True
    except sqlite3.IntegrityError:
        return False


# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------
def logo_html():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{b64}" class="logo">'
    return '<div class="logo-text">CAIAS</div>'


def apply_style():
    st.markdown(
        f"""
        <style>
        #MainMenu, footer, header {{visibility: hidden;}}
        .block-container {{padding-top: 1rem; max-width: 640px;}}
        .banner {{
            background: linear-gradient(160deg, {BLUE} 0%, {BLUE_DARK} 100%);
            border-radius: 18px;
            padding: 8px 10px 18px 10px;
            text-align: center;
            margin-bottom: 18px;
            box-shadow: 0 6px 18px rgba(2, 75, 110, 0.35);
        }}
        .banner .logo {{width: 62%; max-width: 260px; border-radius: 12px;}}
        .logo-text {{color: white; font-size: 3rem; font-weight: 800; padding: 20px;}}
        .banner h2 {{color: white; margin: 6px 0 0 0; font-size: 1.3rem;}}
        .banner p {{color: #cfe6f1; margin: 2px 0 0 0; font-size: 0.9rem;}}
        div.stButton > button, div.stFormSubmitButton > button {{
            background: {BLUE}; color: white; border: none; border-radius: 12px;
            padding: 0.6rem 1.2rem; font-weight: 600; width: 100%;
        }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background: {BLUE_DARK}; color: white;
        }}
        .thanks {{
            background: {BLUE_LIGHT}; border: 2px solid {BLUE}; border-radius: 18px;
            padding: 26px 18px; text-align: center;
        }}
        .thanks h2 {{color: {BLUE}; margin-top: 0;}}
        .madeby {{
            margin-top: 18px; font-size: 1.2rem; font-weight: 700; color: {BLUE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(subtitle):
    st.markdown(
        f"""
        <div class="banner">
            {logo_html()}
            <h2>Student Registration</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
def clean_reg(value):
    return value.strip().upper()


def valid_name(name):
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,59}", name.strip()))


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
def page_register():
    header("Step 1 of 2: Your details")
    st.progress(0.5)

    with st.form("register_form"):
        reg_no = st.text_input("Registration number", placeholder="CAUG26-0144", max_chars=10)
        name = st.text_input("Full name", placeholder="Your name")
        program = st.selectbox("Which BCA program are you studying?", ["Select a program"] + PROGRAMS)
        next_clicked = st.form_submit_button("Next ➜")

    if next_clicked:
        reg_no = clean_reg(reg_no)
        errors = []

        if not REG_PATTERN.match(reg_no):
            errors.append(
                "Registration number must look like **CAUG26-0144** "
                "(CAUG26, a dash, then 4 digits). Only year 26 is accepted."
            )
        elif reg_exists(reg_no):
            errors.append(f"**{reg_no}** is already registered. Each number can register only once.")

        if not valid_name(name):
            errors.append("Please enter your full name (letters only).")

        if program == "Select a program":
            errors.append("Please choose your BCA program.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.student = {
                "reg_no": reg_no,
                "name": " ".join(name.split()).title(),
                "program": program,
            }
            st.session_state.step = 2
            st.rerun()


def page_feedback():
    header("Step 2 of 2: Quick feedback")
    st.progress(1.0)
    student = st.session_state.student
    st.write(f"Hi **{student['name']}** ({student['reg_no']}), just a few quick questions.")

    with st.form("feedback_form"):
        likes = st.radio("Do you like the college?", ["Yes", "Somewhat", "No"], horizontal=True)
        campus = st.slider("Rate the campus facilities (1 = poor, 5 = excellent)", 1, 5, 3)
        teachers = st.slider("Rate the teachers (1 = poor, 5 = excellent)", 1, 5, 3)
        suggestion = st.text_area("Anything you'd like to suggest? (optional)", max_chars=500)
        col1, col2 = st.columns(2)
        back = col1.form_submit_button("⬅ Back")
        submit = col2.form_submit_button("Submit ✔")

    if back:
        st.session_state.step = 1
        st.rerun()

    if submit:
        data = dict(student)
        data.update(
            likes_college=likes,
            campus_rating=campus,
            teacher_rating=teachers,
            suggestion=suggestion.strip(),
        )
        if save_student(data):
            st.session_state.step = 3
            st.rerun()
        else:
            st.error(f"**{student['reg_no']}** is already registered. Please go back and check your number.")


def page_thanks():
    header("Registration complete")
    st.balloons()
    name = st.session_state.student["name"]
    st.markdown(
        f"""
        <div class="thanks">
            <h2>Thank you, {name}! 🎉</h2>
            <p>Your registration has been saved successfully.<br>
            We appreciate your feedback and wish you a great journey at CAIAS.</p>
            <div class="madeby">Made by Ashwin</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Register another student"):
        st.session_state.step = 1
        st.session_state.pop("student", None)
        st.rerun()


def admin_section():
    import pandas as pd

    with st.expander("🔒 Admin"):
        try:
            real_password = st.secrets["ADMIN_PASSWORD"]
        except Exception:
            real_password = "caias-admin"   # change this by setting ADMIN_PASSWORD in Streamlit secrets

        password = st.text_input("Admin password", type="password", key="admin_pw")
        if not password:
            return
        if password != real_password:
            st.error("Wrong password.")
            return

        with get_conn() as conn:
            df = pd.read_sql_query(
                "SELECT reg_no AS 'Reg No', name AS 'Name', program AS 'Program', "
                "likes_college AS 'Likes college', campus_rating AS 'Campus', "
                "teacher_rating AS 'Teachers', suggestion AS 'Suggestion', "
                "registered_at AS 'Registered at' FROM students ORDER BY id DESC",
                conn,
            )
        st.success(f"Total students registered: {len(df)}")
        if len(df):
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name="caias_registrations.csv",
                mime="text/csv",
            )
        else:
            st.info("No registrations yet.")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
init_db()
apply_style()

if "step" not in st.session_state:
    st.session_state.step = 1

if st.session_state.step == 1:
    page_register()
elif st.session_state.step == 2:
    page_feedback()
else:
    page_thanks()

st.write("")
admin_section()
