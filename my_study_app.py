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

# قائمة الأدمن (عدل الإيميلات هنا)
ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# مفتاح الـ API
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. نظام قواعد البيانات (المستخدمين + الإشعارات) ---
USER_DB_FILE = "users_db.json"
SYSTEM_DB_FILE = "system_db.json"  # ملف جديد للإشعارات والفعاليات
USER_DATA_DIR = "user_data"

if not os.path.exists(USER_DATA_DIR): os.makedirs(USER_DATA_DIR)

# إنشاء ملفات الداتا لو مش موجودة
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

def add_system_announcement(type, title, message):
    """دالة للأدمن لنشر خبر جديد"""
    db = load_json(SYSTEM_DB_FILE)
    new_item = {
        "date": str(datetime.date.today()),
        "title": title,
        "message": message
    }
    if type == "notification":
        db["notifications"].insert(0, new_item) # الأحدث يظهر أولاً
    else:
        db["events"].insert(0, new_item)
    save_json(SYSTEM_DB_FILE, db)

def clear_announcements(type):
    """دالة لمسح الإشعارات القديمة"""
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
    
    # تحميل الإشعارات
    system_data = load_json(SYSTEM_DB_FILE)

    # --- القائمة الجانبية ---
    with st.sidebar:
        if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
            st.image(user["avatar_path"], width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        
        st.write(f"أهلاً، **{user['name']}**")
        
        # عرض أحدث إشعار في القائمة الجانبية (تنبيه سريع)
        if system_data["notifications"]:
            latest = system_data["notifications"][0]
            st.info(f"🔔 **تنبيه:** {latest['message']}")

        menu = ["الرئيسية", "الفعاليات", "المكتبة", "مذاكرة", "امتحانات", "الإعدادات"]
        icons = ['house', 'trophy', 'folder', 'book', 'card-checklist', 'gear']
        
        if is_admin:
            menu.append("لوحة الأدمن")
            icons.append("shield-lock")
            
        selected = option_menu("القائمة", menu, icons=icons, styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("خروج"):
            st.session_state.user_email = None
            st.rerun()

    # --- الصفحات ---
    if selected == "الرئيسية":
        st.title(f"📊 أهلاً بك في منصتك")
        
        # عرض الإشعارات العامة هنا بشكل واضح
        if system_data["notifications"]:
            st.subheader("🔔 آخر التنبيهات")
            for note in system_data["notifications"][:3]: # عرض آخر 3 فقط
                st.warning(f"**{note['date']}**: {note['message']}")

        # الإحصائيات
        exams = user['exam_history']
        col1, col2, col3 = st.columns(3)
        col1.metric("عدد الامتحانات", len(exams))
        avg = 0
        if exams: avg = sum([x['score'] for x in exams]) / len(exams)
        col2.metric("المستوى العام", f"{avg:.1f}%")
        col3.metric("تاريخ الانضمام", user['joined'])

    elif selected == "الفعاليات":
        st.title("🏆 الفعاليات والمسابقات")
        st.write("هنا ستجد الامتحانات العامة والمسابقات التي يحددها الأدمن.")
        
        if not system_data["events"]:
            st.info("لا توجد فعاليات نشطة حالياً. انتظر جديد الأدمن! 😉")
        else:
            for event in system_data["events"]:
                with st.expander(f"📌 {event['title']} ({event['date']})", expanded=True):
                    st.write(event['message'])
                    if st.button(f"شارك في {event['title']}", key=event['title']):
                        st.balloons()
                        st.success("تم تسجيل اهتمامك! (سيتم تفعيل الرابط قريباً)")

    elif selected == "المكتبة":
        st.title("📂 ملفاتك")
        files = st.file_uploader("ارفع ملفات (PDF/Word)", accept_multiple_files=True)
        if files and st.button("حفظ وتحليل"):
            text = ""
            for f in files:
                try:
                    if f.name.endswith('.pdf'):
                        reader = PyPDF2.PdfReader(f)
                        text += "".join([p.extract_text() or "" for p in reader.pages])
                    elif f.name.endswith('.docx'):
                        doc = docx.Document(f)
                        text += "\n".join([p.text for p in doc.paragraphs])
                except: pass
            st.session_state.file_content = text
            st.success("تم الحفظ!")

    elif selected == "مذاكرة":
        st.title("🤖 المذاكرة الذكية")
        if "file_content" in st.session_state:
            prompt = st.chat_input("اسألني...")
            if prompt:
                res = model.generate_content(f"Context: {st.session_state.file_content[:5000]}\nQ: {prompt}")
                st.write(res.text)
        else:
            st.warning("ارفع ملفات أولاً!")

    elif selected == "امتحانات":
        st.title("📝 اختبر نفسك")
        # (نفس كود الامتحانات السابق)
        if st.button("امتحان سريع") and "file_content" in st.session_state:
             st.info("جاري إنشاء الامتحان...")
             # (كود توليد الأسئلة هنا...)

    elif selected == "لوحة الأدمن":
        st.title("👮‍♂️ مركز القيادة")
        
        tab1, tab2 = st.tabs(["📢 نشر إشعارات وفعاليات", "👥 إدارة المستخدمين"])
        
        with tab1:
            st.header("إرسال تحديثات للمستخدمين")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔔 إرسال إشعار عام")
                note_msg = st.text_area("نص الإشعار:", placeholder="مثال: تم إضافة مادة الفيزياء...")
                if st.button("إ


