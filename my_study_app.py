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

# قائمة الأدمن الآن تعتمد على اسم المستخدم
ADMIN_USERS = ["amarhossam0000", "mariamebrahim8888"] 

# --- 2. إعداد المفتاح والموديل (آمن) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = "YOUR_NEW_API_KEY_HERE" # استخدم المفتاح الاحتياطي هنا إذا كنت تختبر محليًا
    
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
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": [], "events": []}, f)

# (دوال الـ JSON والحفظ كما هي)
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
        st.write("سيتم تلخيص المحتوى هنا...")

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
    st.warning("هنا تظهر أدوات الإدارة.")
    
def dashboard_page():
    st.title("🏠 لوحة التحكم | اختر ما تود فعله")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)

    def display_tile(col, title, emoji, page_name):
        button_clicked = col.button(f"{emoji} {title}", key=title, use_container_width=True)
        if button_clicked:
            st.session_state.action = page_name
            st.rerun()

    # إنشاء المربعات المطلوبة
    display_tile(col1, "اختبارات وكويزات", "🔴", "QUIZ")        # أحمر
    display_tile(col2, "سؤال وجواب مباشر", "🔵", "CHAT")        # أزرق
    display_tile(col3, "تلخيص وشرح المواد", "🟣", "SUMMARY")      # بنفسجي
    display_tile(col4, "سجل الدرجات والتطور", "🟠", "GRADES")    # برتقالي

    col5, col6, col7, col8 = st.columns(4)
    display_tile(col5, "إدارة المهام والتذكيرات", "🟦", "TASKS") # أزرق: المهام (جديد)
    display_tile(col6, "ألعاب تعلم اللغة", "🟢", "GAMES")        # أخضر: الألعاب (فكرة مستقبلية)

    # زر لوحة الأدمن (يظهر فقط إذا كان المستخدم أدمن)
    if st.session_state.username in ADMIN_USERS:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🛡️ لوحة الأدمن", key="admin_dash", on_click=lambda: st.session_state.update(action="ADMIN"))

# --- 5. التحكم في التطبيق ---

def app_controller():
    # التحقق من تسجيل الدخول
    if not st.session_state.username:
        login_page()
        return

    # التحكم في القائمة الجانبية
    username = st.session_state.username
    user = get_user(username)
    
    with st.sidebar:
        st.write(f"أهلاً، **{user['name']}**")
        st.markdown("---")
        
        st.subheader("💡 دعم وتواصل")
        st.info("📩 **بريد الدعم:** support@eduminds.com")
        st.info("❓ **حل المشكلات:** اضغط هنا")
        
        st.markdown("---")
        if st.button("العودة للرئيسية (لوحة التحكم)"):
            st.session_state.action = "DASHBOARD"
            st.rerun()
        if st.button("تسجيل خروج"):
            st.session_state.username = None
            st.rerun()

    # التحكم في الصفحة المعروضة
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
        grades_mode(username)
    elif action == "ADMIN":
        admin_mode()
    elif action == "TASKS":
        st.title("🟦 إدارة المهام والتذكيرات")
        st.info("هنا ستكون لوحة المهام.")
    elif action == "GAMES":
        st.title("🟢 ألعاب اللغة")
        st.info("هنا سيتم إنشاء ألعاب اللغة الإنجليزية.")


if __name__ == "__main__":
    app_controller()

