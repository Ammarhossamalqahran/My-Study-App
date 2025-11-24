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

# !!! هنا التحديث: استخدام أحدث وأسرع موديل !!!
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. نظام قواعد البيانات ---
USER_DB_FILE = "users_db.json"
SYSTEM_DB_FILE = "system_db.json"
USER_DATA_DIR = "user_data"

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# إنشاء الملفات لو مش موجودة
if not os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(SYSTEM_DB_FILE):
    with open(SYSTEM_DB_FILE, 'w') as f:
        json.dump({"notifications": [], "events": []}, f)

# --- دوال التعامل مع الداتا ---
def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

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
    new_item = {
        "date": str(datetime.date.today()),
        "title": title,
        "message": message
    }
    
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
if "user_email" not in st.session_state:
    st.session_state.user_email = None

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
        if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
            st.image(user["avatar_path"], width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        
        st.write(f"أهلاً، **{user['name']}**")
        
        if system_data.get("notifications"):
            latest = system_data["notifications"][0]
            st.info(f"🔔 {latest['message']}")

        menu = ["الرئيسية", "الفعاليات", "المكتبة", "مذاكرة", "امتحانات", "الإعدادات"]
        icons = ['house', 'trophy', 'folder', 'book', 'card-checklist', 'gear']
        
        if is_admin:
            menu.append("لوحة الأدمن")
            icons.append("shield-lock")
            
        selected = option_menu("القائمة", menu, icons=icons, styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("خروج"):
            st.session_state.user_email = None
            st.rerun()

    # الصفحات
    if selected == "الرئيسية":
        st.title(f"📊 أهلاً بك في منصتك")
        if system_data.get("notifications"):
            st.subheader("🔔 آخر التنبيهات")
            for note in system_data["notifications"][:3]:
                st.warning(f"**{note['date']}**: {note['message']}")

        exams = user['exam_history']
        col1, col2, col3 = st.columns(3)
        col1.metric("عدد الامتحانات", len(exams))
        avg = 0
        if exams:
            avg = sum([x['score'] for x in exams]) / len(exams)
        col2.metric("المستوى العام", f"{avg:.1f}%")
        col3.metric("تاريخ الانضمام", user['joined'])

    elif selected == "الفعاليات":
        st.title("🏆 الفعاليات والمسابقات")
        if not system_data.get("events"):
            st.info("لا توجد فعاليات نشطة حالياً.")
        else:
            for event in system_data["events"]:
                with st.expander(f"📌 {event['title']} ({event['date']})", expanded=True):
                    st.write(event['message'])
                    if st.button(f"شارك في {event['title']}", key=event['title']):
                        st.balloons()
                        st.success("تم تسجيل اهتمامك!")

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
                except:
                    pass
            st.session_state.file_content = text
            st.success("تم الحفظ!")

    elif selected == "مذاكرة":
        st.title("🤖 المذاكرة الذكية (Gemini 1.5 Flash)")
        if "file_content" in st.session_state:
            prompt = st.chat_input("اسألني...")
            if prompt:
                res = model.generate_content(f"Context: {st.session_state.file_content[:10000]}\nQ: {prompt}")
                st.write(res.text)
        else:
            st.warning("ارفع ملفات أولاً!")

    elif selected == "امتحانات":
        st.title("📝 اختبر نفسك")
        
        if st.button("إنشاء امتحان جديد"):
            if "file_content" in st.session_state:
                with st.spinner("جاري تأليف الأسئلة..."):
                    try:
                        prompt = """
                        Create 3 MCQ questions from the text below.
                        Output must be valid JSON only.
                        Format:
                        [
                            {"question": "Q1", "options": ["A", "B", "C"], "answer": "A"},
                            {"question": "Q2", "options": ["X", "Y", "Z"], "answer": "X"}
                        ]
                        """
                        full_prompt = f"{prompt}\nText: {st.session_state.file_content[:5000]}"
                        res = model.generate_content(full_prompt)
                        clean_json = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.quiz = json.loads(clean_json)
                        st.rerun()
                    except:
                        st.error("حدث خطأ أثناء توليد الأسئلة، حاول مرة أخرى.")
            else:
                st.error("الرجاء رفع ملفات من المكتبة أولاً!")

        if "quiz" in st.session_state:
            st.divider()
            user_answers = {}
            for i, q in enumerate(st.session_state.quiz):
                st.subheader(f"س{i+1}: {q['question']}")
                user_answers[i] = st.radio("الإجابة:", q['options'], key=i)
            
            st.markdown("---")
            
            if st.button("تسليم وإنهاء الامتحان"):
                score = 0
                for i, q in enumerate(st.session_state.quiz):
                    if user_answers[i] == q['answer']:
                        score += 1
                
                final_score = (score / len(st.session_state.quiz)) * 100
                st.balloons()
                st.success(f"نتيجتك: {final_score:.1f}%")
                
                save_exam_result(email, final_score)
                st.success("✅ تم حفظ النتيجة في سجلك!")

    elif selected == "لوحة الأدمن":
        st.title("👮‍♂️ مركز القيادة")
        
        tab1, tab2 = st.tabs(["📢 نشر إشعارات", "👥 إدارة المستخدمين"])
        
        with tab1:
            st.header("إرسال تحديثات")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔔 إرسال إشعار")
                note_msg = st.text_area("نص الإشعار:")
                if st.button("إرسال للكل"):
                    add_system_announcement("notification", "تنبيه", note_msg)
                    st.success("تم!")
                
                if st.button("مسح الإشعارات"):
                    clear_announcements("notifications")
                    st.warning("تم المسح.")

            with col2:
                st.subheader("🏆 إنشاء فعالية")
                event_title = st.text_input("عنوان الفعالية:")
                event_msg = st.text_area("تفاصيل الفعالية:")
                if st.button("نشر الفعالية"):
                    add_system_announcement("event", event_title, event_msg)
                    st.success("تم!")
                
                if st.button("مسح الفعاليات"):
                    clear_announcements("events")
                    st.warning("تم المسح.")

        with tab2:
            st.header("إحصائيات المستخدمين")
            db = load_json(USER_DB_FILE)
            
            data_rows = []
            for e, d in db.items():
                data_rows.append({
                    "Email": e,
                    "Name": d['name'],
                    "Exams": len(d['exam_history'])
                })
            
            st.dataframe(pd.DataFrame(data_rows), use_container_width=True)

# تشغيل التطبيق
if st.session_state.user_email:
    main_app()
else:
    login_page()
