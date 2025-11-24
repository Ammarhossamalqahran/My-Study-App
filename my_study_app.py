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
st.set_page_config(page_title="EduMinds - المتكامل", page_icon="🎓", layout="wide")

ADMIN_USERS = ["amarhossam0000", "mariamebrahim8888"] 

# --- 2. إعداد المفتاح والموديل (آمن) ---
# --- 2. إعداد المفتاح والموديل (آمن 100%) ---
try:
    # يجب أن يكون المفتاح في الخزنة الآن
    api_key = st.secrets["GOOGLE_API_KEY"] 
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro') 
    st.session_state.gemini_ready = True
except Exception as e:
    # لو فشل، توقف واطلب من المستخدم وضع المفتاح في الخزنة
    st.error("⚠️ فشل الاتصال بخدمة Gemini. تأكد أن المفتاح الجديد موجود في الخزنة (Secrets) باسم GOOGLE_API_KEY.")
    st.stop()

# --- 3. قواعد البيانات ---
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"
if not os.path.exists("user_data"): os.makedirs("user_data")
if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": [], "events": []}, f)

# (الدوال الأساسية)
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

def add_notification(msg):
    db = load_json(SYSTEM_DB)
    db["notifications"].insert(0, {"date": str(datetime.date.today()), "msg": msg})
    save_json(SYSTEM_DB, db)

def read_file_content(uploaded_file):
    # (تم اختصار الكود لتجنب التكرار)
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(uploaded_file)
            text += "".join([p.extract_text() or "" for p in pdf.pages])
        return text
    except Exception as e:
        return ""

# --- 4. واجهات العمل (Flow Pages) ---

def quiz_mode():
    st.title("🔴 اختبار من الملف")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب الاختبار منه:", type=['pdf', 'docx', 'txt'])
    if uploaded_file:
        st.write("سيتم انشاء الاختبار هنا...")

def summary_mode():
    st.title("🟣 ملخصات وشرح")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب تلخيصه:", type=['pdf', 'docx', 'txt'])

    if uploaded_file:
        content = read_file_content(uploaded_file)
        if st.button("تلخيص الآن"):
            with st.spinner("جاري تلخيص المحتوى..."):
                res = model.generate_content(f"لخص هذا النص التعليمي في نقاط بسيطة:\n{content[:10000]}")
                st.subheader("الملخص")
                st.write(res.text)

def chat_mode():
    st.title("🔵 أسئلة سريعة")
    uploaded_file = st.file_uploader("ارفع الملف للمحادثة عليه:", type=['pdf', 'docx', 'txt'])
    if uploaded_file:
        st.write("سيتم المحادثة على الملف هنا...")

def grades_mode(username):
    st.title("🟠 سجل الدرجات والتطور")
    user = get_user(username)
    if user['history']:
        st.subheader("نتائجك السابقة")
        df = pd.DataFrame(user['history'])
        st.line_chart(df, x='date', y='score')
        st.dataframe(df)
    else:
        st.info("لا توجد بيانات امتحانات مسجلة حتى الآن.")

def admin_mode():
    st.title("🛡️ لوحة الأدمن")
    st.markdown("---")
    st.subheader("📢 نشر إشعارات")
    msg = st.text_area("رسالة جديدة للطلاب:")
    if st.button("نشر إشعار عام"):
        add_notification(msg)
        st.success("تم النشر بنجاح!")

def dashboard_page():
    st.title("🏠 EduMinds | اختر ما تود فعله")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)

    def display_tile(col, title, emoji, page_name):
        button_clicked = col.button(f"### {emoji} {title}", key=title, use_container_width=True)
        if button_clicked:
            st.session_state.action = page_name
            st.rerun()
    
    # 📌 المربعات الملونة المطلوبة (التي كانت مفقودة)
    display_tile(col1, "اختبارات وامتحانات", "🔴", "QUIZ")
    display_tile(col2, "سؤال وجواب مباشر", "🔵", "CHAT")
    display_tile(col3, "تلخيص وشرح المواد", "🟣", "SUMMARY")
    display_tile(col4, "سجل الدرجات والتطور", "🟠", "GRADES")

    col5, col6, col7, col8 = st.columns(4)
    display_tile(col5, "إدارة المهام والتذكيرات", "🟦", "TASKS")
    display_tile(col6, "ألعاب تعلم اللغة", "🟢", "GAMES")
    
    # زر لوحة الأدمن
    if st.session_state.username in ADMIN_USERS:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🛡️ لوحة الأدمن", key="admin_dash", on_click=lambda: st.session_state.update(action="ADMIN"))

# --- 5. التحكم الرئيسي (Controller) ---

def app_controller():
    # تهيئة المتغيرات
    if "user_email" not in st.session_state: st.session_state.user_email = None
    if "username" not in st.session_state: st.session_state.username = None
    if "action" not in st.session_state: st.session_state.action = "DASHBOARD"

    # 1. صفحة الدخول
    if not st.session_state.username:
        # (كود صفحة الدخول)
        st.markdown("<h1 style='text-align:center; color:#764abc;'>🔐 تسجيل دخول سريع</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username_input = st.text_input("اسم المستخدم (Username):")
                if st.form_submit_button("دخول"):
                    username = username_input.lower().strip()
                    if not username: st.error("الرجاء إدخال اسم."); st.stop()
                    get_user(username) 
                    st.session_state.username = username
                    st.session_state.action = "DASHBOARD" 
                    st.rerun()
        return

    # 2. القائمة الجانبية (ثابتة)
    with st.sidebar:
        user = get_user(st.session_state.username)
        st.write(f"أهلاً، **{user['name']}**")
        st.markdown("---")
        
        # 📌 حقوق الملكية والتواصل
        st.subheader("💡 دعم وتواصل")
        st.info("📩 **بريد الدعم:** support@eduminds.com")
        st.info("📞 **تواصل معنا:** 011xxxxxxx")
        st.info("❓ **حل المشكلات:** اضغط هنا")
        st.markdown("---")
        st.markdown("##### جميع الحقوق محفوظة © 2025")
        
        if st.button("العودة للرئيسية"):
            st.session_state.action = "DASHBOARD"
            st.rerun()
        if st.button("تسجيل خروج"):
            st.session_state.username = None
            st.rerun()

    # 3. التحكم في الصفحة المعروضة (The Router)
    action = st.session_state.get("action", "DASHBOARD")
    
    if action == "DASHBOARD":
        dashboard_page()
    elif action == "QUIZ":
        quiz_mode()
    elif action == "SUMMARY":
        summary_mode()
    elif action == "CHAT":
        chat_mode()
    elif action == "GRADES":
        grades_mode(st.session_state.username)
    elif action == "ADMIN":
        admin_mode()
    elif action == "TASKS":
        st.title("🟦 إدارة المهام والتذكيرات")
    elif action == "GAMES":
        st.title("🟢 ألعاب تعلم اللغة")

if __name__ == "__main__":
    app_controller()


