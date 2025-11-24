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

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="منصة عمار التعليمية", page_icon="🎓", layout="wide")

# قائمة الأدمن
ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# --- 2. إعداد المفتاح ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error("⚠️ لم يتم العثور على مفتاح API في الخزنة (Secrets).")
    st.stop() 

# --- 3. قواعد البيانات ---
if not os.path.exists("user_data"): os.makedirs("user_data")
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"

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
        db[email] = {
            "name": email.split('@')[0],
            "joined": str(datetime.date.today()),
            "history": []
        }
        save_json(USER_DB, db)
    
    # تصليح الخطأ القديم (KeyError)
    if "history" not in db[email]:
        if "exam_history" in db[email]: db[email]["history"] = db[email]["exam_history"]
        else: db[email]["history"] = []
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

# --- 5. التطبيق الرئيسي ---
if "email" not in st.session_state: st.session_state.email = None

def main():
    if not st.session_state.email:
        st.markdown("<h1 style='text-align:center; color:#764abc;'>🔐 EduMinds Login</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                email_input = st.text_input("البريد الإلكتروني:")
                if st.form_submit_button("تسجيل الدخول") and "@" in email_input:
                    st.session_state.email = email_input.lower().strip()
                    st.rerun()
        return

    user_email = st.session_state.email
    user = get_user(user_email)
    is_admin = user_email in ADMIN_EMAILS
    sys_data = load_json(SYSTEM_DB)

    # القائمة الجانبية
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.write(f"أهلاً **{user['name']}**")
        
        if sys_data.get("notifications"):
            st.info(f"🔔 {sys_data['notifications'][0]['msg']}")

        menu = ["الرئيسية", "مذاكرة", "امتحانات", "حسابي"]
        icons = ['house', 'book', 'pencil', 'person']
        
        if is_admin:
            menu.append("لوحة الأدمن")
            icons.append("shield-lock")

        selected = option_menu("القائمة", menu, icons=icons, styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("تسجيل خروج"):
            st.session_state.email = None
            st.rerun()

    # --- الصفحات ---
    if selected == "الرئيسية":
        st.title("🏠 الرئيسية")
        st.write("أهلاً بك في منصتك التعليمية الذكية.")
        
        col1, col2 = st.columns(2)
        col1.metric("عدد الامتحانات", len(user['history']))
        
        if user['history']:
            avg = sum([x['score'] for x in user['history']]) / len(user['history'])
            col2.metric("مستواك العام", f"{avg:.1f}%")
        
        if user['history']:
            st.subheader("📈 منحنى التطور")
            df = pd.DataFrame(user['history'])
            st.line_chart(df, x='date', y='score')

        if sys_data.get("notifications"):
            st.subheader("📢 آخر الأخبار")
            for n in sys_data["notifications"][:3]:
                st.warning(f"{n['date']}: {n['msg']}")

    elif selected == "مذاكرة":
        st.title("🤖 المذاكرة الذكية")
        files = st.file_uploader("ارفع ملفات (PDF/Word)", accept_multiple_files=True)
        
        if files and st.button("تحليل الملفات"):
            text = ""
            for f in files:
                try:
                    if f.name.endswith('.pdf'):
                        pdf = PyPDF2.PdfReader(f)
                        text += "".join([p.extract_text() for p in pdf.pages])
                    elif f.name.endswith('.docx'):
                        doc = docx.Document(f)
                        text += "\n".join([p.text for p in doc.paragraphs])
                except: pass
            st.session_state.content = text
            st.success("تم الحفظ!")

        if "content" in st.session_state:
            q = st.chat_input("اسألني...")
            if q:
                prompt = f"Context: {st.session_state.content[:10000]}\nQuestion: {q}\nAnswer in Arabic."
                try:
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except Exception as e:
                    st.error("حدث خطأ في الاتصال.")

    elif selected == "امتحانات":
        st.title("📝 امتحان فوري")
        if st.button("أنشئ امتحان") and "content" in st.session_state:
            try:
                prompt = """Create 3 MCQ questions JSON format: [{"question":"..","options":[".."],"answer":".."}]"""
                res = model.generate_content(f"{prompt}\nContext: {st.session_state.content[:3000]}")
                clean_json = res.text.replace("```json","").replace("```","").strip()
                st.session_state.quiz = json.loads(clean_json)
                st.rerun()
            except: st.error("حاول مرة أخرى")

        if "quiz" in st.session_state:
            score = 0
            for i, q in enumerate(st.session_state.quiz):
                st.write(f"**س{i+1}: {q['question']}**")
                ans = st.radio("الإجابة:", q['options'], key=i)
                if ans == q['answer']: score += 1
            
            st.markdown("---")
            if st.button("تسليم"):
                final = (score/len(st.session_state.quiz))*100
                st.balloons()
                st.success(f"النتيجة: {final:.1f}%")
                save_score(user_email, final)

    elif selected == "حسابي":
        st.title("📊 التطور الدراسي")
        if user['history']:
            df = pd.DataFrame(user['history'])
            st.line_chart(df, x='date', y='score')
            st.dataframe(df)
        else:
            st.info("لا توجد بيانات بعد.")

    elif selected == "لوحة الأدمن":
        st.title("👮‍♂️ لوحة التحكم")
        
        tab1, tab2 = st.tabs(["📢 الإشعارات", "👥 المستخدمين"])
        
        with tab1:
            msg = st.text_input("رسالة جديدة للطلاب:")
            if st.button("نشر"):
                add_notification(msg)
                st.success("تم النشر!")
        
        with tab2:
            st.header("إحصائيات المستخدمين")
            db = load_json(USER_DB)
            
            # --- التصحيح هنا: تحويل JSON لجدول منظم ---
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
            else:
                st.info("لا يوجد مستخدمين مسجلين بعد.")


if __name__ == "__main__":
    main()
