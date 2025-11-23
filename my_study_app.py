import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import docx
import json
import pandas as pd
from gtts import gTTS
import io
import graphviz
from youtube_transcript_api import YouTubeTranscriptApi
from streamlit_option_menu import option_menu
import os
import datetime

# --- 1. إعداد الصفحة وتصميم Canva ---
st.set_page_config(page_title="EduMinds - منصتي التعليمية", page_icon="🎓", layout="wide")

# Custom CSS for Canva-like Look
st.markdown("""
<style>
    /* تغيير الفونت */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    
    /* تصميم الكروت (Cards) */
    .card {
        background-color: #1E1E1E;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #333;
        transition: transform 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
        border-color: #764abc;
    }
    
    /* تصميم الزراير */
    .stButton>button {
        background: linear-gradient(90deg, #764abc 0%, #64379f 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #8a5cd1 0%, #764abc 100%);
        color: white;
    }

    /* الفوتر الجديد (حقوق عمار ومريم) */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0E1117;
        color: #ffffff;
        text-align: center;
        padding: 15px;
        border-top: 2px solid #764abc;
        font-size: 15px;
        z-index: 999;
        box-shadow: 0 -5px 10px rgba(0,0,0,0.5);
    }
    .footer b {
        color: #764abc;
    }
    .footer .sub-name {
        font-size: 13px;
        color: #bbb;
        margin-top: -10px;
        display: block;
    }
    
    /* إخفاء القوائم الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 2. إعداد المفتاح ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. دوال وإعدادات النظام ---
DB_FILE = "users_db.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f)

def get_user_data(email):
    db = load_db()
    if email not in db:
        db[email] = {"name": email.split('@')[0], "joined": str(datetime.date.today()), "exam_history": []}
        save_db(db)
    return db[email]

def update_user_progress(email, score):
    db = load_db()
    if email in db:
        db[email]["exam_history"].append({"date": str(datetime.date.today()), "score": score})
        save_db(db)

# دوال القراءة
def get_pdf_text(file):
    try: return "".join([p.extract_text() for p in PyPDF2.PdfReader(file).pages])
    except: return ""

def get_docx_text(file):
    try: return "\n".join([p.text for p in docx.Document(file).paragraphs])
    except: return ""

def read_files(files):
    text = ""
    for f in files:
        text += f"\n--- {f.name} ---\n"
        if f.name.endswith('.pdf'): text += get_pdf_text(f)
        elif f.name.endswith('.docx'): text += get_docx_text(f)
        else: text += "[ملف غير مدعوم]"
    return text

# --- 4. تسجيل الدخول ---
if "user_email" not in st.session_state: st.session_state.user_email = None

def login_page():
    st.markdown("<h1 style='text-align: center; color: #764abc;'>EduMinds Login 🔐</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            email = st.text_input("📧 البريد الإلكتروني:")
            if st.form_submit_button("دخول") and "@" in email:
                st.session_state.user_email = email
                st.rerun()

# --- 5. التطبيق الرئيسي ---
def main_app():
    user = get_user_data(st.session_state.user_email)
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
        st.write(f"أهلاً، **{user['name']}** 👋")
        selected = option_menu("القائمة", ["الرئيسية", "ملفاتي", "شات AI", "امتحانات"], 
                             icons=['house', 'folder', 'chat-dots', 'card-checklist'],
                             styles={"nav-link-selected": {"background-color": "#764abc"}})
        if st.button("خروج"): 
            st.session_state.user_email = None
            st.rerun()

    # الصفحات
    if selected == "الرئيسية":
        st.title(f"📊 لوحة تحكم {user['name']}")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='card'><h3>📅 انضممت</h3><p>{user['joined']}</p></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='card'><h3>📝 امتحانات</h3><p>{len(user['exam_history'])}</p></div>", unsafe_allow_html=True)
        avg = 0
        if user['exam_history']: avg = sum([x['score'] for x in user['exam_history']])/len(user['exam_history'])
        col3.markdown(f"<div class='card'><h3>⭐ المستوى</h3><p>{avg:.1f}%</p></div>", unsafe_allow_html=True)

    elif selected == "ملفاتي":
        st.title("📂 مكتبة الملفات")
        files = st.file_uploader("ارفع الملفات", accept_multiple_files=True)
        if files and st.button("حفظ"):
            st.session_state.file_content = read_files(files)
            st.success("تم الحفظ!")

    elif selected == "شات AI":
        st.title("💬 المساعد الذكي")
        if "file_content" not in st.session_state: st.warning("ارفع ملفات الأول")
        else:
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
            if prompt := st.chat_input("اسأل..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"):
                    res = model.generate_content(f"Context:\n{st.session_state.file_content}\nQ: {prompt}")
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    elif selected == "امتحانات":
        st.title("📝 الاختبارات")
        if st.button("امتحان جديد") and "file_content" in st.session_state:
            try:
                res = model.generate_content(f"Create 5 MCQ JSON from: {st.session_state.file_content[:4000]} Format: [{{'question':'','options':[],'answer':''}}]")
                st.session_state.quiz = json.loads(res.text.replace("```json","").replace("```","").strip())
            except: pass
        
        if "quiz" in st.session_state:
            ans = {}
            for i, q in enumerate(st.session_state.quiz):
                st.write(f"**{q['question']}**")
                ans[i] = st.radio("", q['options'], key=i)
            if st.button("تصحيح"):
                score = sum([1 for i, q in enumerate(st.session_state.quiz) if ans[i] == q['answer']])
                final = (score/5)*100
                st.success(f"النتيجة: {final}%")
                update_user_progress(st.session_state.user_email, final)

# --- 6. الفوتر (تم التعديل حسب طلبك) ---
st.markdown("""
<div class="footer">
    <p>جميع الحقوق محفوظة © 2025 | تم التطوير بواسطة <b>عمار حسام</b> 🚀</p>
    <p class="sub-name"><b>& مريم ابراهيم</b> ✨</p>
    <p>📞 للتواصل والدعم الفني: <a href="tel:01102353779" style="color: #764abc; text-decoration: none;">01102353779</a></p>
</div>
""", unsafe_allow_html=True)

# تشغيل
if st.session_state.user_email: main_app()
else: login_page()

