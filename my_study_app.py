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

# --- 1. إعدادات الأدمن والمفتاح ---
# ⚠️ هام: اكتب إيميلاتكم الحقيقية هنا عشان تظهرلكم لوحة الأدمن
ADMIN_EMAILS = ["amarhossam0000@gmail.com"] 

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 2. إعداد الصفحة وتصميم Canva ---
st.set_page_config(page_title="EduMinds - منصتي", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    .card {
        background-color: #1E1E1E; border-radius: 15px; padding: 20px;
        margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #333; transition: transform 0.3s;
    }
    .card:hover { transform: translateY(-5px); border-color: #764abc; }
    
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0E1117; color: #ffffff; text-align: center;
        padding: 10px; border-top: 2px solid #764abc; font-size: 14px; z-index: 999;
    }
    .footer b { color: #764abc; }
    
    .profile-pic {
        width: 100px; height: 100px; border-radius: 50%; object-fit: cover;
        margin-bottom: 10px; border: 3px solid #764abc;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. دوال وإعدادات النظام ---
DB_FILE = "users_db.json"
USER_DATA_DIR = "user_data"
if not os.path.exists(USER_DATA_DIR): os.makedirs(USER_DATA_DIR)

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f)

def get_user_data(email):
    db = load_db()
    if email not in db:
        db[email] = {"name": email.split('@')[0], "joined": str(datetime.date.today()), "exam_history": [], "avatar_path": None}
        save_db(db)
    return db[email]

def update_avatar(email, uploaded_file):
    db = load_db()
    file_path = os.path.join(USER_DATA_DIR, f"{email}_avatar.png")
    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
    db[email]["avatar_path"] = file_path
    save_db(db)
    return file_path

# دالة تشغيل الصوت الجديدة (تعمل في كل مكان)
def display_voice_player(text):
    if text and len(text) > 5:
        try:
            # نقرأ أول 500 حرف عشان السرعة
            tts = gTTS(text=text[:500], lang='ar')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
        except: pass

def get_youtube_text(video_url):
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([entry['text'] for entry in transcript])
    except: return None

def read_files(files):
    text = ""
    for f in files:
        text += f"\n--- {f.name} ---\n"
        try:
            if f.name.endswith('.pdf'): text += "".join([p.extract_text() for p in PyPDF2.PdfReader(f).pages])
            elif f.name.endswith('.docx'): text += "\n".join([p.text for p in docx.Document(f).paragraphs])
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
                st.session_state.user_email = email.lower().strip()
                st.rerun()

# --- 5. التطبيق الرئيسي ---
def main_app():
    user_email = st.session_state.user_email
    user = get_user_data(user_email)
    is_admin = user_email in ADMIN_EMAILS # هل المستخدم الحالي أدمن؟

    with st.sidebar:
        if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
            st.image(user["avatar_path"], width=100, output_format="PNG", use_column_width=False)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            
        st.write(f"أهلاً، **{user['name']}** 👋")
        if is_admin: st.success("✅ وضع المسؤول (Admin)")

        # قائمة الخيارات (تزيد لو أدمن)
        menu_options = ["الرئيسية", "مكتبة الملفات", "يوتيوب 📺", "مذاكرة ممتعة 🎮", "شات AI", "امتحانات", "الإعدادات"]
        menu_icons = ['house', 'folder', 'youtube', 'joystick', 'chat-dots', 'card-checklist', 'gear']
        
        if is_admin:
            menu_options.append("👨‍✈️ لوحة الأدمن")
            menu_icons.append("shield-lock")
            
        selected = option_menu("القائمة", menu_options, icons=menu_icons,
                             styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("خروج 🚪"): 
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

    # --- صفحة الأدمن الجديدة ---
    elif selected == "👨‍✈️ لوحة الأدمن":
        st.title("👮‍♂️ غرفة التحكم (للمسؤولين فقط)")
        db = load_db()
        st.metric("إجمالي المستخدمين المسجلين", len(db))
        st.divider()
        
        # تحويل قاعدة البيانات لجدول عرض
        users_list = []
        for email, data in db.items():
            avg_score = "جديد"
            if data['exam_history']:
                avg_score = f"{sum([x['score'] for x in data['exam_history']])/len(data['exam_history']):.1f}%"
            
            users_list.append({
                "البريد الإلكتروني": email,
                "الاسم": data['name'],
                "تاريخ الانضمام": data['joined'],
                "عدد الامتحانات": len(data['exam_history']),
                "متوسط المستوى": avg_score
            })
        
        if users_list:
            df = pd.DataFrame(users_list)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا يوجد مستخدمين حتى الآن.")

    elif selected == "مكتبة الملفات":
        st.title("📂 ملفاتك الدراسية")
        files = st.file_uploader("ارفع الكتب والملازم", accept_multiple_files=True)
        if files and st.button("حفظ"):
            st.session_state.file_content = read_files(files)
            st.success("تم الحفظ في الذاكرة!")
        if "file_content" in st.session_state: st.info("✅ يوجد ملفات جاهزة.")

    elif selected == "يوتيوب 📺":
        st.title("📺 تلخيص اليوتيوب (صوت وصورة)")
        url = st.text_input("رابط الفيديو:")
        if st.button("لخص") and url:
            with st.spinner("جاري العمل..."):
                text = get_youtube_text(url)
                if text:
                    res = model.generate_content(f"لخص هذا الفيديو في نقاط:\n{text}")
                    st.markdown(res.text)
                    st.session_state.file_content = f"يوتيوب:\n{res.text}\n{text}"
                    # تشغيل الصوت
                    st.write("🔊 استمع للملخص:")
                    display_voice_player(res.text)
                else: st.error("لا يوجد ترجمة للفيديو.")

    elif selected == "مذاكرة ممتعة 🎮":
        st.title("🎮 ذاكر واستمتع (مسموع)")
        if "file_content" not in st.session_state: st.warning("ارفع ملفات الأول!")
        else:
            style = st.selectbox("الطريقة:", ["🎤 أغنية راب", "😎 صاحبك الجدع", "📖 قصة", "👶 تبسيط طفل"])
            prompt = st.text_input("اسم الدرس:")
            if st.button("ابدأ 🎬") and prompt:
                with st.spinner("بيجهز العرض..."):
                    persona = ""
                    if "راب" in style: persona = "اشرح الدرس ده كأغنية راب ممتعة."
                    elif "صاحبك" in style: persona = "اشرح بالعامية المصرية كصاحب."
                    elif "قصة" in style: persona = "حول الدرس لقصة خيالية."
                    elif "طفل" in style: persona = "بسط الشرح جداً لطفل."
                    
                    res = model.generate_content(f"{persona}\nالمحتوى:\n{st.session_state.file_content}\nاشرح: {prompt}")
                    st.markdown(res.text)
                    # تشغيل الصوت
                    st.divider()
                    st.write("🔊 استمع للشرح:")
                    display_voice_player(res.text)

    elif selected == "شات AI":
        st.title("💬 المساعد الذكي (الناطق)")
        if "file_content" not in st.session_state: st.warning("ارفع ملفات")
        else:
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant": display_voice_player(msg["content"])

            if prompt := st.chat_input("اسأل..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"):
                    res = model.generate_content(f"Context:\n{st.session_state.file_content}\nQ: {prompt}")
                    st.markdown(res.text)
                    display_voice_player(res.text)
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
                db = load_db()
                db[user_email]["exam_history"].append({"score": final})
                save_db(db)

    elif selected == "الإعدادات":
        st.title("⚙️ الإعدادات")
        uploaded = st.file_uploader("تغيير الصورة", type=["jpg", "png"])
        if uploaded and st.button("حفظ"):
            update_avatar(user_email, uploaded)
            st.rerun()

# --- 6. الفوتر ---
st.markdown("""
<div class="footer">
    <p>جميع الحقوق محفوظة © 2025 | تم التطوير بواسطة <b>عمار حسام</b> 🚀</p>
    <p style="margin-top: -10px; font-size: 12px;">& <b>مريم ابراهيم</b> ✨</p>
    <p>📞 للتواصل والدعم الفني: <a href="tel:01102353779" style="color: #764abc; text-decoration: none;">01102353779</a></p>
</div>
""", unsafe_allow_html=True)

if st.session_state.user_email: main_app()
else: login_page()
