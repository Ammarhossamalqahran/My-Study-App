import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import pandas as pd
import PyPDF2
import docx
from streamlit_option_menu import option_menu

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="EduMinds - تسجيل سريع", page_icon="🎓", layout="wide")

# قائمة الأدمن الآن تعتمد على اسم المستخدم
ADMIN_USERS = ["amarhossam0000", "mariamebrahim8888"] 

# --- 2. إعداد المفتاح والموديل (آمن) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = "YOUR_API_KEY_HERE" # استخدم المفتاح الاحتياطي هنا إذا كنت تختبر محليًا
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro') 
except Exception as e:
    st.error("⚠️ فشل الاتصال بخدمة Gemini. تأكد من المفتاح في Secrets.")
    st.stop()

# --- 3. قواعد البيانات ---
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"

if not os.path.exists("user_data"): os.makedirs("user_data")
if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)

# (دوال الـ JSON والحفظ كما هي)
def load_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def get_user(username):
    """الآن نستخدم الاسم كمفتاح أساسي"""
    db = load_json(USER_DB)
    
    if username not in db:
        db[username] = {
            "name": username, # الاسم هو المفتاح الآن
            "joined": str(datetime.date.today()),
            "history": []
        }
        save_json(USER_DB, db)
    
    # تصليح الخطأ القديم (KeyError)
    if "history" not in db[username]:
        db[username]["history"] = db[username].get("exam_history", []) 
        save_json(USER_DB, db)
    
    return db[username]

def save_score(username, score):
    db = load_json(USER_DB)
    if "history" not in db[username]: db[username]["history"] = []
    db[username]["history"].append({"date": str(datetime.date.today()), "score": score})
    save_json(USER_DB, db)

# --- 4. واجهة تسجيل الدخول الجديدة ---

if "username" not in st.session_state: st.session_state.username = None
if "action" not in st.session_state: st.session_state.action = None

def login_page():
    st.markdown("<h1 style='text-align:center; color:#764abc;'>🔐 تسجيل دخول سريع</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            # تم تغيير الإيميل إلى اسم المستخدم
            username_input = st.text_input("اسم المستخدم (Username):")
            if st.form_submit_button("دخول"):
                username = username_input.lower().strip()
                if not username:
                    st.error("الرجاء إدخال اسم.")
                    st.stop()
                
                # التحقق والتسجيل
                get_user(username) 
                st.session_state.username = username
                st.session_state.action = "DASHBOARD"
                st.rerun()
        return

# --- 5. التطبيق الرئيسي ---
def dashboard_page():
    # ... (كود لوحة التحكم) ...
    pass # سيتم استبدال هذا بكود لوحة التحكم

def quiz_mode():
    # ... (كود الاختبار) ...
    pass

def summary_mode():
    # ... (كود الملخص) ...
    pass

def chat_mode():
    # ... (كود الأسئلة) ...
    pass

def grades_mode(username):
    # ... (كود الدرجات) ...
    pass

def admin_mode():
    # ... (كود الأدمن) ...
    pass

def app_controller():
    if not st.session_state.username:
        login_page()
        return

    # التحكم في القائمة الجانبية والصفحات
    username = st.session_state.username
    user = get_user(username)
    is_admin = username in ADMIN_USERS # التحقق من الأدمن الآن بالاسم

    with st.sidebar:
        # (باقي كود القائمة الجانبية)
        st.write(f"أهلاً، **{user['name']}**")
        if st.button("تسجيل خروج"):
            st.session_state.username = None
            st.rerun()

    # (باقي كود التحكم في الصفحة المعروضة)
    st.info("تم تفعيل نظام الدخول بالاسم بنجاح!")


if __name__ == "__main__":
    app_controller()


