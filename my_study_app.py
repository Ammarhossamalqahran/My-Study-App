import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import pandas as pd
from gtts import gTTS
import io
import PyPDF2
import docx
from streamlit_option_menu import option_menu
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="EduMinds - منصتي", page_icon="🎓", layout="wide")

# قائمة الأدمن
ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# مفتاح الـ API
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. نظام قواعد البيانات ---
USER_DB_FILE = "users_db.json"
SYSTEM_DB_FILE = "system_db.json"
USER_DATA_DIR = "user_data"

if not os.path.exists(USER_DATA_DIR): os.makedirs(USER_DATA_DIR)

# إنشاء الملفات لو مش موجودة
if not os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, 'w') as f: json.dump({}, f)

if not os.path.exists(SYSTEM_DB_FILE):
    with open(SYSTEM_DB_FILE, 'w') as f: json.dump({"notifications": [], "events": []}, f)

# --- دوال التعامل مع الداتا ---
def load_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def get_user(email):
    db = load_json(USER_DB_FILE)
    if email not in db:
        db[email] = {
            "name": email.split('@')[0],
            "joined": str(datetime.date.today()),
            "exam_history": [],
            "avatar_path": None
        }
        save_json(USER_DB_FILE, db)
    return db[email]

def save_exam_result(email, score):
    db = load_json(USER_DB_FILE)
    record = {
        "date": str(datetime.date.today()),
        "score": score
    }
    db[email]["exam_history"].append(record)
    save_json(USER_DB_FILE, db)

def add_system_announcement(type, title, message):
    db = load_json(SYSTEM_DB_FILE)
    new_item = {"date": str(datetime.date.today()), "title": title, "message": message}
    if type == "notification":
        db["notifications"].insert(0, new_item)
    else:
        db["events"].insert(0, new_item)
    save_json(SYSTEM_DB_FILE, db)

def clear_announcements(type):
    db = load_json(SYSTEM_DB_FILE)
    db[type] = []
    save_json(SYSTEM_DB_FILE, db)

# --- 3. واجهة تسجيل الدخول ---
if "user_email" not in st.session_state: st.session_state.user_email = None

def login_page():
    st.markdown("<h1 style='text-align: center; color: #764abc;'>🔐 EduMinds Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            email = st.text_input("📧 البريد الإلكتروني:")
            if st.form_submit_button("دخول") and "@" in email:
                st.session_state.user_email = email.lower().strip()
                st.rerun()

# --- 4. التطبيق الرئيسي ---
def main_app():
    email = st.session_state.user_email
    user = get_user(email)
    is_admin = email in ADMIN_EMAILS
    
    system_data = load_json(SYSTEM_DB_FILE)

    # القائمة الجانبية
    with st.sidebar:
        if user.get("avatar_path") and os.path.exists(user
