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
st.set_page_config(page_title="EduMinds - الإصدار النهائي", page_icon="💡", layout="wide")

ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# إعداد المفتاح من الخزنة (الآمن)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        # إذا لم يتم العثور عليه، ضع المفتاح القديم كاحتياطي أخير
        api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro') 
except Exception as e:
    st.error("⚠️ فشل الاتصال بخدمة Gemini. تأكد من مفتاح API في Secrets.")
    st.stop()

# --- 2. قواعد البيانات ---
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"
if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": []}, f)

# --- الدوال الأساسية (معالجة الملفات) ---
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

def get_user(email):
    db = load_json(USER_DB)
    if email not in db:
        db[email] = {"name": email.split('@')[0], "history": []}
        save_json(USER_DB, db)
    # لضمان وجود مفتاح 'history' من أي كود سابق
    if "history" not in db[email]:
        db[email]["history"] = db[email].get("exam_history", []) 
        save_json(USER_DB, db)
    return db[email]

def load_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def save_score(email, score):
    db = load_json(USER_DB)
    db[email]["history"].append({"date": str(datetime.date.today()), "score": score})
    save_json(USER_DB, db)

# --- 3. واجهات المربعات (Flow Pages) ---

def quiz_mode():
    """مربع أحمر: إنشاء امتحان سريع."""
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
                    st.rerun() # إعادة تحميل لعرض الاختبار
                except:
                    st.error("فشل إنشاء الاختبار. حاول تصغير الملف.")

        if "quiz" in st.session_state:
            score = 0
            # [كود عرض وتصحيح الامتحان]

def summary_mode():
    """مربع بنفسجي: تلخيص وشرح المواد."""
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
    """مربع أزرق: سؤال وجواب مباشر (Q&A)."""
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
    """مربع برتقالي: عرض التطور والدرجات."""
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
    """لوحة الأدمن (مختصرة)."""
    st.title("🛡️ لوحة الأدمن")
    st.markdown("---")
    st.subheader("📢 نشر إشعارات")
    msg = st.text_area("رسالة جديدة للطلاب:")
    if st.button("نشر إشعار عام"):
        add_notification(msg)
        st.success("تم النشر!")
        
# --- 4. واجهة المربعات الرئيسية ---

def dashboard_page():
    st.title("🏠 EduMinds | اختر ما تود فعله")
    st.markdown("---")

    # تحديد 3 أعمدة
    col1, col2, col3 = st.columns(3)

    # دالة لرسم المربع (Tile) باستخدام HTML
    def display_tile(col, title, emoji, color, page_name):
        # استخدام st.button داخل عمود لإعطاء تأثير المربع
        button_clicked = col.button(f"{emoji} {title}", key=title, use_container_width=True)
        # تخصيص لون الزرار عبر CSS (حل مؤقت لعدم وجود خاصية لون للزرار في ستريملت)
        col.markdown(
            f"""
            <style>
            div[data-testid*="stButton"] > button[kind="primary"] {{
                background-color: #764abc; /* اللون الأساسي للقائمة */
            }}
            div[data-testid*="stButton"] > button[kind="primary"]:hover {{
                background-color: #5d3d92;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        if button_clicked:
            st.session_state.action = page_name
            st.rerun()

    # إنشاء المربعات المطلوبة
    display_tile(col1, "اختبارات وامتحانات", "🔴", "#FF6347", "QUIZ") # أحمر
    display_tile(col2, "سؤال وجواب مباشر", "🔵", "#4682B4", "CHAT")  # أزرق
    display_tile(col3, "تلخيص وشرح المواد", "🟣", "#8A2BE2", "SUMMARY") # بنفسجي

    col4, col5, col6 = st.columns(3)
    display_tile(col4, "مستواي الدراسي", "🟠", "#FFA500", "GRADES") # برتقالي

    # زر لوحة الأدمن (يظهر فقط إذا كان المستخدم أدمن)
    if st.session_state.user_email in ADMIN_EMAILS:
        display_tile(col6, "لوحة الأدمن", "🛡️", "#008080", "ADMIN")

# --- 5. التنفيذ (Control Flow) ---

def app_controller():
    # التحقق من تسجيل الدخول
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    if not st.session_state.user_email:
        # عرض صفحة الدخول
        st.markdown("<h1 style='text-align: center;'>🔐 EduMinds Login</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                email_input = st.text_input("البريد الإلكتروني:")
                if st.form_submit_button("تسجيل الدخول") and "@" in email_input:
                    st.session_state.user_email = email_input.lower().strip()
                    st.session_state.action = "DASHBOARD" # بعد الدخول يروح للرئيسية
                    st.rerun()
        return

    # القائمة الجانبية (ثابتة)
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
        grades_mode(st.session_state.user_email)
    elif action == "ADMIN":
        admin_mode()

if __name__ == "__main__":
    app_controller()
