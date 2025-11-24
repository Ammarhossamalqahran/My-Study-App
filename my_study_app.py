import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import pandas as pd
import PyPDF2
import docx
from streamlit_option_menu import option_menu

# --- 1. الإعدادات الأساسية والمفاتيح ---
st.set_page_config(page_title="EduMinds - المتكامل", page_icon="🎓", layout="wide")

ADMIN_USERS = ["amarhossam0000", "mariamebrahim8888"] 

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = "YOUR_API_KEY_HERE"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro') 
except Exception as e:
    st.error("⚠️ فشل الاتصال بخدمة Gemini. تأكد من المفتاح في Secrets.")
    st.stop()

# --- 2. قواعد البيانات والدوال المساعدة ---
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"
if not os.path.exists("user_data"): os.makedirs("user_data")
if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": [], "events": []}, f)

def load_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def get_user(username):
    db = load_json(USER_DB)
    if username not in db:
        db[username] = {"name": username, "joined": str(datetime.date.today()), "history": []}
        save_json(USER_DB, db)
    if "history" not in db[username]:
        db[username]["history"] = db[username].get("exam_history", []) 
        save_json(USER_DB, db)
    return db[username]

def save_score(username, score):
    db = load_json(USER_DB)
    if "history" not in db[username]: db[username]["history"] = []
    db[username]["history"].append({"date": str(datetime.date.today()), "score": score})
    save_json(USER_DB, db)

def read_file_content(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(uploaded_file)
            text += "".join([p.extract_text() or "" for p in pdf.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            text += "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8')
        return text
    except Exception as e:
        st.error(f"فشل قراءة الملف: {e}")
        return ""

# --- 3. تعريف واجهات العمل (ALL FUNCTION DEFINITIONS AT TOP) ---

def login_page():
    """✅ صفحة تسجيل الدخول (يجب أن تظهر أولاً)"""
    st.markdown("<h1 style='text-align:center; color:#764abc;'>🔐 تسجيل دخول سريع</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username_input = st.text_input("اسم المستخدم (Username):")
            if st.form_submit_button("دخول"):
                username = username_input.lower().strip()
                if not username:
                    st.error("الرجاء إدخال اسم.")
                    st.stop()
                
                get_user(username) 
                st.session_state.username = username
                st.session_state.action = "DASHBOARD"
                st.rerun()

def dashboard_page():
    st.title("🏠 لوحة التحكم")
    # (كود عرض المربعات الملونة)
    st.warning("هنا ستظهر المربعات الملونة لبدء العمل.")

def quiz_mode():
    st.title("🔴 اختبار من الملف")
    st.write("سيتم انشاء الاختبار هنا...")

# (باقي الدوال: summary_mode, chat_mode, grades_mode, admin_mode...)
# تم حذف باقي الدوال هنا لتجنب التكرار الهائل، ولكن يجب أن تكون معرفة في الكود الأصلي.

# --- 4. التحكم الرئيسي (Controller) ---

def app_controller():
    # تهيئة المتغيرات (لتجنب AttributeError)
    if "username" not in st.session_state: 
        st.session_state.username = None
    if "action" not in st.session_state: 
        st.session_state.action = "DASHBOARD" # القيمة الافتراضية

    # 1. إذا لم يسجل دخول: اعرض صفحة الدخول
    if not st.session_state.username:
        login_page()
        return

    # 2. إذا سجل دخول: اعرض القائمة الجانبية والصفحة المطلوبة
    username = st.session_state.username
    user = get_user(username)
    
    with st.sidebar:
        st.write(f"أهلاً، **{user['name']}**")
        # (باقي كود القائمة الجانبية)
        if st.button("العودة للرئيسية"): st.session_state.action = "DASHBOARD"; st.rerun()

    # التحكم في الصفحة المعروضة
    action = st.session_state.get("action", "DASHBOARD")
    
    if action == "DASHBOARD":
        dashboard_page()
    elif action == "QUIZ":
        quiz_mode()
    # ... (باقي حالات التحكم)

# --- 5. التشغيل (EXECUTION) ---

if __name__ == "__main__":
    app_controller()


