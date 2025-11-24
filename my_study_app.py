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

# --- 1. الإعدادات ---
st.set_page_config(page_title="EduMinds", layout="wide")

# مفتاح الـ API
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # حط مفتاحك هنا
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk"

genai.configure(api_key=api_key)

# !!! التغيير الجذري: استخدام النسخة المستقرة القديمة !!!
model = genai.GenerativeModel('gemini-pro')

# --- 2. الداتابيز ---
if not os.path.exists("user_data"): os.makedirs("user_data")
if not os.path.exists("users_db.json"): 
    with open("users_db.json", 'w') as f: json.dump({}, f)

def get_user(email):
    try:
        with open("users_db.json", 'r') as f: db = json.load(f)
    except: db = {}
    
    if email not in db:
        db[email] = {"name": email.split('@')[0], "exam_history": []}
        with open("users_db.json", 'w') as f: json.dump(db, f)
    return db[email]

def save_score(email, score):
    with open("users_db.json", 'r') as f: db = json.load(f)
    db[email]["exam_history"].append({"date": str(datetime.date.today()), "score": score})
    with open("users_db.json", 'w') as f: json.dump(db, f)

# --- 3. التطبيق ---
if "user_email" not in st.session_state: st.session_state.user_email = None

def main():
    if not st.session_state.user_email:
        st.title("🔐 تسجيل الدخول")
        email = st.text_input("البريد الإلكتروني:")
        if st.button("دخول") and "@" in email:
            st.session_state.user_email = email.lower().strip()
            st.rerun()
        return

    # واجهة المستخدم المسجل
    user = get_user(st.session_state.user_email)
    
    with st.sidebar:
        st.write(f"مرحباً، {user['name']}")
        selected = option_menu("القائمة", ["مذاكرة", "امتحانات", "خروج"], 
                             icons=['book', 'pencil', 'box-arrow-right'])
        
        if selected == "خروج":
            st.session_state.user_email = None
            st.rerun()

    if selected == "مذاكرة":
        st.title("🤖 المذاكرة الذكية")
        files = st.file_uploader("ارفع ملفات PDF/Word", accept_multiple_files=True)
        
        if files and st.button("تحليل"):
            text = ""
            for f in files:
                try:
                    if f.name.endswith('.pdf'):
                        reader = PyPDF2.PdfReader(f)
                        text += "".join([p.extract_text() for p in reader.pages])
                    elif f.name.endswith('.docx'):
                        doc = docx.Document(f)
                        text += "\n".join([p.text for p in doc.paragraphs])
                except: pass
            
            st.session_state.content = text
            st.success("تم الحفظ! اسأل براحتك.")

        if "content" in st.session_state:
            q = st.chat_input("اسألني في الملف...")
            if q:
                # طلب بسيط جداً عشان ميحصلش ايرور
                prompt = f"Context: {st.session_state.content[:3000]}\nQuestion: {q}\nAnswer in Arabic."
                try:
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except Exception as e:
                    st.error(f"خطأ: {e}")

    elif selected == "امتحانات":
        st.title("📝 امتحان سريع")
        if st.button("إنشاء امتحان") and "content" in st.session_state:
            try:
                # طلب JSON بسيط
                prompt = """Create 3 simple MCQ questions from context. 
                Output strict JSON: [{"question":"..", "options":[".."], "answer":".."}]"""
                res = model.generate_content(f"{prompt}\nContext: {st.session_state.content[:2000]}")
                data = json.loads(res.text.replace("```json","").replace("```","").strip())
                st.session_state.quiz = data
                st.rerun()
            except: st.error("حاول تاني")

        if "quiz" in st.session_state:
            score = 0
            for i, q in enumerate(st.session_state.quiz):
                ans = st.radio(q['question'], q['options'], key=i)
                if ans == q['answer']: score += 1
            
            if st.button("إنهاء"):
                final = (score/len(st.session_state.quiz))*100
                st.success(f"النتيجة: {final}%")
                save_score(st.session_state.user_email, final)

if __name__ == "__main__":
    main()
