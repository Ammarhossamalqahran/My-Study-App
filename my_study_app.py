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
st.set_page_config(page_title="EduMinds - المتكامل", page_icon="🧠", layout="wide")

ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# --- 2. إعداد المفتاح والموديل (آمن) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
       
    
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

# (دوال الـ JSON والحفظ كما هي لتجنب الأخطاء)
def load_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def get_user(email):
    db = load_json(USER_DB)
    if email not in db:
        db[email] = {"name": email.split('@')[0], "joined": str(datetime.date.today()), "history": []}
        save_json(USER_DB, db)
    if "history" not in db[email]:
        db[email]["history"] = db[email].get("exam_history", []) 
        save_json(USER_DB, db)
    return db[email]

def save_score(email, score):
    db = load_json(USER_DB)
    if "history" not in db[email]: db[email]["history"] = []
    db[email]["history"].append({"date": str(datetime.date.today()), "score": score})
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
    """🔴 مربع الامتحان: يطلب الملف مباشرة"""
    st.title("🔴 اختبار من الملف")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب الاختبار منه:", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        # (باقي كود انشاء الاختبار...)
        st.write("تم رفع الملف. اضغط على زر 'إنشاء الأسئلة' أدناه.")

def summary_mode():
    """🟣 مربع الملخص: يطلب الملف مباشرة"""
    st.title("🟣 تلخيص وشرح المواد")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب تلخيصه:", type=['pdf', 'docx', 'txt'])

    if uploaded_file:
        # (باقي كود تلخيص الملف...)
        st.write("تم رفع الملف. اضغط على زر 'تلخيص الآن' أدناه.")

def games_mode():
    """🟢 مربع الألعاب: لتعلم اللغة الإنجليزية (فكرة جديدة)"""
    st.title("🟢 ألعاب اللغة الإنجليزية")
    st.info("هذا القسم قيد الإنشاء: يمكنك هنا ممارسة ألعاب مفردات وقواعد اللغة الإنجليزية بطريقة ممتعة!")
    st.write("مثال: لعبة 'تخمين الكلمة' أو 'ترتيب الجمل'.")

def grades_mode(user_email):
    """🟠 مربع الدرجات: يعرض التطور"""
    st.title("🟠 سجل الدرجات والتطور")
    user = get_user(user_email)
    # (كود عرض الرسم البياني والجداول)
    st.write("سيتم عرض الرسم البياني لتطور أدائك هنا.")

def task_management_mode():
    """🟦 مربع المهام: إدارة الأفكار والمهام (التركيز الجديد)"""
    st.title("🟦 إدارة المهام والتذكيرات")
    st.markdown("### 📝 أضف مهمة جديدة")
    
    # نموذج لإضافة مهمة
    with st.form("new_task_form"):
        title = st.text_input("عنوان المهمة (إلزامي):")
        due_date = st.date_input("موعد التسليم:", datetime.date.today())
        priority = st.selectbox("الأولوية:", ["عالية", "متوسطة", "منخفضة"])
        
        if st.form_submit_button("إضافة مهمة"):
            # (هنا يتم استخدام أداة generic_reminders لو كنا نستخدمها مباشرة)
            st.success(f"تم إضافة المهمة '{title}' بنجاح!")
            # يجب أن يتم حفظها في قاعدة بيانات محلية هنا

def dashboard_page():
    """لوحة التحكم الرئيسية"""
    st.title("🏠 لوحة التحكم")
    
    # عرض المهام اليومية في الأعلى (من باب التذكير)
    st.markdown("### 📋 مهامك الحالية (بناءً على أولوياتك)")
    st.warning("هذا الجزء يحتاج لربط بنظام الـ ToDo List الكامل.")
    st.markdown("---")
    
    # المربعات الملونة
    col1, col2, col3, col4 = st.columns(4)

    def display_tile(col, title, emoji, page_name):
        button_clicked = col.button(f"{emoji} {title}", key=title, use_container_width=True)
        if button_clicked:
            st.session_state.action = page_name
            st.rerun()

    # إنشاء المربعات الجديدة
    display_tile(col1, "إدارة المهام والتذكيرات", "🟦", "TASKS") # أزرق: المهام
    display_tile(col2, "ملخصات وشرح المواد", "🟣", "SUMMARY") # بنفسجي: الملخص
    display_tile(col3, "اختبارات وكويزات", "🔴", "QUIZ") # أحمر: الاختبار
    display_tile(col4, "سجل الدرجات والتطور", "🟠", "GRADES") # برتقالي: الدرجات

    st.markdown("<br>", unsafe_allow_html=True)
    col5, col6, col7, col8 = st.columns(4)
    display_tile(col5, "ألعاب تعلم اللغة", "🟢", "GAMES") # أخضر: الألعاب

# --- 5. التحكم في التطبيق ---

def app_controller():
    if "user_email" not in st.session_state: st.session_state.user_email = None

    if not st.session_state.user_email:
        # (كود تسجيل الدخول)
        st.markdown("<h1 style='text-align: center;'>🔐 تسجيل الدخول</h1>", unsafe_allow_html=True)
        return

    # القائمة الجانبية (ثابتة)
    with st.sidebar:
        # (كود القائمة الجانبية)
        st.subheader("💡 دعم وتواصل")
        st.info("📩 **بريد الدعم:** support@eduminds.com")
        st.info("❓ **حل المشكلات:** اضغط هنا")

    # التحكم في الصفحة المعروضة
    action = st.session_state.get("action", "DASHBOARD")
    
    if action == "DASHBOARD":
        dashboard_page()
    elif action == "QUIZ":
        quiz_mode()
    elif action == "SUMMARY":
        summary_mode()
    elif action == "GRADES":
        grades_mode(st.session_state.user_email)
    elif action == "TASKS":
        task_management_mode()
    elif action == "GAMES":
        games_mode()
    # (إضافة باقي الحالات مثل ADMIN)

if __name__ == "__main__":
    # هذا الجزء يحتاج لتعديل بسيط لإضافة صفحة تسجيل الدخول التي كانت تعمل سابقاً
    # تم حذفه مؤقتاً لتسهيل التركيز على الواجهات الجديدة
    app_controller()

