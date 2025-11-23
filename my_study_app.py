import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import docx
import json
import pandas as pd
from gtts import gTTS
import io
import os
import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from streamlit_option_menu import option_menu

# --- 1. إعداد الصفحة وتصميم Canva ---
st.set_page_config(page_title="EduMinds - منصتي", page_icon="🎓", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    /* تصميم الكروت */
    .card {
        background-color: #1E1E1E;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #333;
        transition: transform 0.3s;
    }
    .card:hover { transform: translateY(-5px); border-color: #764abc; }
    
    /* الفوتر */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0E1117; color: #ffffff;
        text-align: center; padding: 10px;
        border-top: 2px solid #764abc; font-size: 14px; z-index: 999;
    }
    .footer b { color: #764abc; }
    
    /* صورة البروفايل المدورة */
    .profile-pic {
        width: 100px; height: 100px;
        border-radius: 50%; object-fit: cover;
        margin-bottom: 10px; border: 3px solid #764abc;
    }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
USER_DATA_DIR = "user_data" # فولدر لحفظ صور المستخدمين

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f)

def get_user_data(email):
    db = load_db()
    if email not in db:
        db[email] = {
            "name": email.split('@')[0], 
            "joined": str(datetime.date.today()), 
            "exam_history": [],
            "avatar_path": None # مسار الصورة
        }
        save_db(db)
    return db[email]

def update_avatar(email, uploaded_file):
    db = load_db()
    # حفظ الصورة في الفولدر
    file_path = os.path.join(USER_DATA_DIR, f"{email}_avatar.png")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    db[email]["avatar_path"] = file_path
    save_db(db)
    return file_path

def get_youtube_text(video_url):
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        full_text = " ".join([entry['text'] for entry in transcript])
        return full_text
    except: return None

# دوال القراءة
def read_files(files):
    text = ""
    for f in files:
        text += f"\n--- {f.name} ---\n"
        try:
            if f.name.endswith('.pdf'): 
                text += "".join([p.extract_text() for p in PyPDF2.PdfReader(f).pages])
            elif f.name.endswith('.docx'): 
                text += "\n".join([p.text for p in docx.Document(f).paragraphs])
        except: text += "[ملف غير مقروء]"
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
        # عرض صورة البروفايل
        if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
            st.image(user["avatar_path"], width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            
        st.write(f"أهلاً، **{user['name']}** 👋")
        
        selected = option_menu("القائمة", 
                             ["الرئيسية", "مكتبة الملفات", "يوتيوب 📺", "مذاكرة ممتعة 🎮", "امتحانات", "الإعدادات"], 
                             icons=['house', 'folder', 'youtube', 'joystick', 'card-checklist', 'gear'],
                             styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("خروج"): 
            st.session_state.user_email = None
            st.rerun()

    # --- الصفحات ---
    if selected == "الرئيسية":
        st.title(f"📊 لوحة تحكم {user['name']}")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='card'><h3>📅 انضممت</h3><p>{user['joined']}</p></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='card'><h3>📝 امتحانات</h3><p>{len(user['exam_history'])}</p></div>", unsafe_allow_html=True)
        avg = 0
        if user['exam_history']: avg = sum([x['score'] for x in user['exam_history']])/len(user['exam_history'])
        col3.markdown(f"<div class='card'><h3>⭐ المستوى</h3><p>{avg:.1f}%</p></div>", unsafe_allow_html=True)

    elif selected == "مكتبة الملفات":
        st.title("📂 ملفاتك الدراسية")
        files = st.file_uploader("ارفع الكتب والملازم", accept_multiple_files=True)
        if files and st.button("حفظ"):
            st.session_state.file_content = read_files(files)
            st.success("تم الحفظ في الذاكرة!")
        if "file_content" in st.session_state:
            st.info("✅ يوجد ملفات محملة وجاهزة.")

    elif selected == "يوتيوب 📺":
        st.title("📺 تلخيص اليوتيوب")
        url = st.text_input("ضع رابط الفيديو هنا:")
        if st.button("لخص الفيديو") and url:
            with st.spinner("جاري المشاهدة والتلخيص..."):
                text = get_youtube_text(url)
                if text:
                    res = model.generate_content(f"لخص هذا الفيديو في نقاط تعليمية واضحة:\n{text}")
                    st.markdown(res.text)
                    # دمج المحتوى مع الذاكرة عشان نسأل فيه
                    st.session_state.file_content = f"محتوى فيديو يوتيوب:\n{res.text}\n{text}"
                    st.success("تمت إضافة الفيديو للمذاكرة!")
                else:
                    st.error("تأكد أن الفيديو يحتوي على ترجمة (Captions).")

    elif selected == "مذاكرة ممتعة 🎮":
        st.title("🎮 ذاكر واستمتع")
        if "file_content" not in st.session_state: st.warning("ارفع ملفات الأول!")
        else:
            style = st.selectbox("اختار طريقة الشرح:", 
                               ["🎤 اشرحلي بأغنية راب", 
                                "😎 اشرحلي زي صاحبك الجدع (عامية)", 
                                "📖 اشرحلي كقصة خيال علمي", 
                                "👶 اشرحلي كأني عندي 5 سنين"])
            
            prompt = st.text_input("عايزني أشرحلك إيه بظبط؟ (اكتب اسم الدرس)")
            
            if st.button("ابدأ العرض 🎬") and prompt:
                with st.spinner("بيتقمص الشخصية..."):
                    persona = ""
                    if "راب" in style: persona = "أنت مغني راب محترف. اشرح الدرس ده بكلمات مقفاة وإيقاع سريع وممتع."
                    elif "صاحبك" in style: persona = "أنت صاحب الطالب الانتيم. اشرح بالعامية المصرية وبخفة دم واستخدم أمثلة من حياتنا اليومية."
                    elif "قصة" in style: persona = "أنت راوي قصص خيالية. حول الدرس ده لقصة ملحمية فيها أبطال وأشرار."
                    elif "5 سنين" in style: persona = "اشرح بتبسيط شديد جداً كأنك بتكلم طفل، استخدم تشبيهات بسيطة."
                    
                    full_prompt = f"{persona}\n\nالمحتوى:\n{st.session_state.file_content}\n\nاشرح: {prompt}"
                    res = model.generate_content(full_prompt)
                    st.markdown(res.text)

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
                
                # تحديث قاعدة البيانات
                db = load_db()
                db[st.session_state.user_email]["exam_history"].append({"score": final})
                save_db(db)

    elif selected == "الإعدادات":
        st.title("⚙️ الإعدادات")
        st.write("تغيير الصورة الشخصية")
        uploaded_avatar = st.file_uploader("ارفع صورة بروفايل جديدة", type=["jpg", "png"])
        if uploaded_avatar:
            if st.button("حفظ الصورة"):
                path = update_avatar(st.session_state.user_email, uploaded_avatar)
                st.success("تم تحديث الصورة! ستظهر بعد التحديث.")
                st.rerun()

# --- 6. الفوتر ---
st.markdown("""
<div class="footer">
    <p>جميع الحقوق محفوظة © 2025 | تم التطوير بواسطة <b>عمار حسام</b> 🚀</p>
    <p style="margin-top: -10px; font-size: 12px;">& <b>مريم ابراهيم</b> ✨</p>
    <p>📞 للتواصل والدعم الفني: <a href="tel:01102353779" style="color: #764abc; text-decoration: none;">01102353779</a></p>
</div>
""", unsafe_allow_html=True)

# تشغيل
if st.session_state.user_email: main_app()
else: login_page()
