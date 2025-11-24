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

# --- 2. إعداد المفتاح من الخزنة ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # استخدام أحدث موديل
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ في مشكلة في قراءة مفتاح API من الخزنة (Secrets).")
    st.stop()

# --- 3. قواعد البيانات ---
if not os.path.exists("user_data"): os.makedirs("user_data")
USER_DB = "users_db.json"
SYSTEM_DB = "system_db.json"

if not os.path.exists(USER_DB): 
    with open(USER_DB, 'w') as f: json.dump({}, f)
if not os.path.exists(SYSTEM_DB): 
    with open(SYSTEM_DB, 'w') as f: json.dump({"notifications": []}, f)

# --- 4. الدوال ---
def get_user(email):
    try:
        with open(USER_DB, 'r') as f: db = json.load(f)
    except: db = {}
    
    if email not in db:
        db[email] = {"name": email.split('@')[0], "history": []}
        with open(USER_DB, 'w') as f: json.dump(db, f)
    return db[email]

def save_score(email, score):
    with open(USER_DB, 'r') as f: db = json.load(f)
    db[email]["history"].append({"date": str(datetime.date.today()), "score": score})
    with open(USER_DB, 'w') as f: json.dump(db, f)

# --- 5. التطبيق الرئيسي ---
if "email" not in st.session_state: st.session_state.email = None

def main():
    # صفحة الدخول
    if not st.session_state.email:
        st.markdown("<h1 style='text-align:center; color:#764abc;'>🔐 تسجيل الدخول</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            email = st.text_input("البريد الإلكتروني:")
            if st.button("دخول") and "@" in email:
                st.session_state.email = email.lower().strip()
                st.rerun()
        return

    # التطبيق بعد الدخول
    user = get_user(st.session_state.email)
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.write(f"أهلاً **{user['name']}**")
        selected = option_menu("القائمة", ["مذاكرة", "امتحانات", "حسابي"], icons=['book', 'pencil', 'person'])
        if st.button("خروج"):
            st.session_state.email = None
            st.rerun()

    if selected == "مذاكرة":
        st.title("🤖 المذاكرة الذكية")
        files = st.file_uploader("ارفع ملفاتك (PDF/Word)", accept_multiple_files=True)
        
        if files and st.button("تحليل وبدء المذاكرة"):
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
            st.success("تم قراءة الملفات بنجاح!")

        if "content" in st.session_state:
            q = st.chat_input("اسألني أي سؤال في المنهج...")
            if q:
                # طلب الرد من جيميناي
                res = model.generate_content(f"Context: {st.session_state.content[:15000]}\nQuestion: {q}\nAnswer in Arabic.")
                st.write(res.text)

    elif selected == "امتحانات":
        st.title("📝 امتحان فوري")
        if st.button("أنشئ امتحان") and "content" in st.session_state:
            try:
                prompt = """Create 3 MCQ questions JSON format: [{"question":"..","options":[".."],"answer":".."}]"""
                res = model.generate_content(f"{prompt}\nContext: {st.session_state.content[:5000]}")
                st.session_state.quiz = json.loads(res.text.replace("```json","").replace("```","").strip())
                st.rerun()
            except: st.error("حاول مرة أخرى")

        if "quiz" in st.session_state:
            score = 0
            for i, q in enumerate(st.session_state.quiz):
                st.write(f"**س{i+1}: {q['question']}**")
                ans = st.radio("الإجابة:", q['options'], key=i)
                if ans == q['answer']: score += 1
            
            st.write("---")
            if st.button("تسليم الامتحان"):
                final = (score/len(st.session_state.quiz))*100
                st.balloons()
                st.success(f"النتيجة: {final:.1f}%")
                save_score(st.session_state.email, final)

    elif selected == "حسابي":
        st.title("📊 مستواك الدراسي")
        if user['history']:
            df = pd.DataFrame(user['history'])
            st.line_chart(df, x='date', y='score')
            st.write(df)
        else:
            st.info("لسه مفيش امتحانات، شد حيلك!")

if __name__ == "__main__":
    main()
