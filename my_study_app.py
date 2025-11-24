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
st.set_page_config(page_title="منصة عمار التعليمية", page_icon="🎓", layout="wide")

ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# --- 2. إعداد المفتاح ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = "AIzaSyCq9dJgYood8SQ9e2nPLDtxa2hc8XFJrWU"
    
    genai.configure(api_key=api_key)
    
    # !!! التصحيح النهائي: إضافة models/ لضمان عمل الموديل على السيرفر !!!
    model = genai.GenerativeModel('models/gemini-pro')

except Exception as e:
    st.error(f"⚠️ فشل الاتصال بخدمة Gemini. تأكد من المفتاح في Secrets.")
    st.stop() 

# --- 3. قواعد البيانات ---
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"

if not os.path.exists("user_data"): os.makedirs("user_data")
if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": [], "events": []}, f)

# --- 4. الدوال ---
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

def add_notification(msg):
    db = load_json(SYSTEM_DB)
    db["notifications"].insert(0, {"date": str(datetime.date.today()), "msg": msg})
    save_json(SYSTEM_DB, db)

def clear_announcements(type):
    db = load_json(SYSTEM_DB)
    db[type] = []
    save_json(SYSTEM_DB, db)

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

# --- 5. واجهات العمل (Pages) ---

def quiz_mode():
    st.title("🔴 اختبار من الملف")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب الاختبار منه:", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        content = read_file_content(uploaded_file)
        st.session_state.content = content
        
        if st.button("أنشئ 3 أسئلة الآن"):
            with st.spinner("جاري تأليف الأسئلة..."):
                try:
                    prompt = """Create 3 MCQ questions JSON format: [{"question":"..","options":[".."],"answer":".."}]"""
                    res = model.generate_content(f"{prompt}\nContext: {content[:3000]}")
                    st.session_state.quiz = json.loads(res.text.replace("```json","").replace("```","").strip())
                    st.rerun() 
                except:
                    st.error("فشل إنشاء الاختبار. حاول تصغير الملف.")
        
        if "quiz" in st.session_state:
            # (كود عرض الاختبار والتصحيح)
            st.write("عرض الاختبار هنا...")


def summary_mode():
    st.title("🟣 ملخصات وشرح")
    uploaded_file = st.file_uploader("ارفع الملف المطلوب تلخيصه:", type=['pdf', 'docx', 'txt'])

    if uploaded_file:
        content = read_file_content(uploaded_file)
        if st.button("تلخيص الآن"):
            with st.spinner("جاري تلخيص المحتوى..."):
                # الكود اللي كان بيضرب Error هنا
                res = model.generate_content(f"لخص هذا النص التعليمي في نقاط بسيطة:\n{content[:10000]}")
                st.subheader("الملخص")
                st.write(res.text)

def chat_mode():
    st.title("🔵 أسئلة سريعة")
    uploaded_file = st.file_uploader("ارفع الملف للمحادثة عليه:", type=['pdf', 'docx', 'txt'])

    if uploaded_file:
        st.session_state.chat_content = read_file_content(uploaded_file)
        st.success("تم تحليل الملف. ابدأ في طرح الأسئلة!")
        
        q = st.chat_input("اسألني أي سؤال في الملف...")
        if q:
            with st.spinner("جاري البحث عن الإجابة..."):
                res = model.generate_content(f"Context: {st.session_state.chat_content[:15000]}\nQuestion: {q}\nAnswer in Arabic.")
                st.write(f"**سؤالك:** {q}")
                st.write(f"**الإجابة:** {res.text}")

def grades_mode(user_email):
    st.title("🟠 سجل الدرجات والتطور")
    user = get_user(user_email)
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
    
    tab1, tab2 = st.tabs(["📢 الإشعارات", "👥 المستخدمين"])
    
    with tab1:
        st.subheader("نشر إشعارات")
        msg = st.text_area("رسالة جديدة للطلاب:")
        if st.button("نشر إشعار عام"):
            add_notification(msg)
            st.success("تم النشر بنجاح!")
    
    with tab2:
        st.header("إحصائيات المستخدمين")
        db = load_json(USER_DB)
        users_data_list = []
        for email, data in db.items():
            history = data.get('history', [])
            avg_score = f"{sum([x['score'] for x in history]) / len(history):.1f}%" if history else "جديد"
            
            users_data_list.append({
                "الإيميل": email,
                "الاسم": data['name'],
                "الامتحانات": len(history),
                "المستوى": avg_score
            })
        
        if users_data_list:
            df = pd.DataFrame(users_data_list)
            st.dataframe(df, use_container_width=True)

# --- 6. التنفيذ (Control Flow) ---
# ... (نفس كود التحكم في الصفحة) ...

def dashboard_page():
    st.title("🏠 EduMinds | اختر ما تود فعله")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    def display_tile(col, title, emoji, page_name):
        button_clicked = col.button(f"{emoji} {title}", key=title, use_container_width=True)
        if button_clicked:
            st.session_state.action = page_name
            st.rerun()

    display_tile(col1, "اختبارات وامتحانات", "🔴", "QUIZ") 
    display_tile(col2, "سؤال وجواب مباشر", "🔵", "CHAT")
    display_tile(col3, "تلخيص وشرح المواد", "🟣", "SUMMARY")

    col4, col5, col6 = st.columns(3)
    display_tile(col4, "مستواي الدراسي", "🟠", "GRADES")

    if st.session_state.user_email in ADMIN_EMAILS:
        display_tile(col6, "لوحة الأدمن", "🛡️", "ADMIN")

def app_controller():
    if "user_email" not in st.session_state: st.session_state.user_email = None

    if not st.session_state.user_email:
        st.markdown("<h1 style='text-align: center;'>🔐 EduMinds Login</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                email_input = st.text_input("البريد الإلكتروني:")
                if st.form_submit_button("تسجيل الدخول") and "@" in email_input:
                    st.session_state.user_email = email_input.lower().strip()
                    st.session_state.action = "DASHBOARD"
                    st.rerun()
        return

    # القائمة الجانبية
    with st.sidebar:
        user = get_user(st.session_state.user_email)
        st.write(f"أهلاً، **{user['name']}**")
        st.markdown("---")
        
        st.subheader("💡 دعم ومساعدة")
        st.info("📩 **بريد الدعم:** support@eduminds.com")
        st.info("❓ **حل المشكلات:** اضغط هنا")
        
        st.markdown("---")
        if st.button("العودة للرئيسية (لوحة التحكم)"):
            st.session_state.action = "DASHBOARD"
            st.rerun()

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
        grades_mode(st.session_state.user_email)
    elif action == "ADMIN":
        admin_mode()

if __name__ == "__main__":
    app_controller()
