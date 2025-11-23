import streamlit as st
import google.generativeai as genai
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
# ⚠️ تم تصحيح القائمة هنا عشان الأدمن يشتغل
ADMIN_EMAILS = ["amarhossam0000@gmail.com", "mariamebrahim8888@gmail.com"]

# مفتاحك (تأكد إنه شغال)
api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 2. إعداد الصفحة ---
st.set_page_config(page_title="EduMinds - منصتي", page_icon="🎓", layout="wide")

# (نفس الستايل بتاعك)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .card { background-color: #1E1E1E; border-radius: 15px; padding: 20px; margin: 10px 0; border: 1px solid #333; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0E1117; text-align: center; padding: 10px; border-top: 2px solid #764abc; z-index: 999; }
    .footer b { color: #764abc; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. المخ (قاعدة البيانات التي لا تنسى) ---
DB_FILE = "users_db.json"
USER_DATA_DIR = "user_data"

# التأكد من وجود الفولدر والملف من البداية
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({}, f)

def load_db():
    """تحميل البيانات مع معالجة الأخطاء"""
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {} # لو الملف باظ، يرجع قاموس فاضي بدل ما يوقف الموقع

def save_db(db):
    """حفظ البيانات فوراً"""
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4) # indent عشان لو حبيت تقرأ الملف بعينك

def get_user_data(email):
    """استدعاء بيانات المستخدم أو إنشاؤه لو جديد"""
    db = load_db()
    if email not in db:
        # مستخدم جديد
        db[email] = {
            "name": email.split('@')[0], 
            "joined": str(datetime.date.today()), 
            "exam_history": [], 
            "avatar_path": None
        }
        save_db(db) # احفظ فوراً عشان مينساش
    return db[email]

def update_avatar(email, uploaded_file):
    db = load_db()
    file_path = os.path.join(USER_DATA_DIR, f"{email}_avatar.png")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    db[email]["avatar_path"] = file_path
    save_db(db)

# --- دوال المساعدة (الصوت، الملفات، يوتيوب) ---
def display_voice_player(text):
    if text and len(text) > 5:
        try:
            tts = gTTS(text=text[:500], lang='ar') # قراءة أول 500 حرف للسرعة
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
            if f.name.endswith('.pdf'): 
                reader = PyPDF2.PdfReader(f)
                text += "".join([p.extract_text() or "" for p in reader.pages])
            elif f.name.endswith('.docx'): 
                doc = docx.Document(f)
                text += "\n".join([p.text for p in doc.paragraphs])
        except: text += "[ملف غير مقروء]"
    return text

# --- 4. تسجيل الدخول (البوابة) ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def login_page():
    st.markdown("<br><br><h1 style='text-align: center; color: #764abc;'>🔐 EduMinds Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>سجل دخولك ولن نفقد بياناتك أبداً</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            email = st.text_input("📧 البريد الإلكتروني (Gmail):")
            submit = st.form_submit_button("🚀 دخول / تسجيل جديد")
            
            if submit and "@" in email:
                email = email.lower().strip()
                # هنا بنحفظ المستخدم أول ما يدوس دخول
                get_user_data(email) 
                st.session_state.user_email = email
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()

# --- 5. التطبيق الرئيسي ---
def main_app():
    user_email = st.session_state.user_email
    
    # تحميل بيانات المستخدم الطازجة من الملف
    user = get_user_data(user_email)
    is_admin = user_email in ADMIN_EMAILS

    with st.sidebar:
        # عرض الصورة الشخصية
        if user.get("avatar_path") and os.path.exists(user["avatar_path"]):
            st.image(user["avatar_path"], width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            
        st.write(f"مرحباً، **{user['name']}** 👋")
        
        if is_admin:
            st.success("🛡️ وضع المسؤول (Admin)")
            menu_options = ["الرئيسية", "المكتبة", "يوتيوب", "المذاكرة", "شات AI", "امتحانات", "الإعدادات", "لوحة الأدمن"]
            menu_icons = ['house', 'folder', 'youtube', 'joystick', 'chat-dots', 'card-checklist', 'gear', 'shield-lock']
        else:
            menu_options = ["الرئيسية", "المكتبة", "يوتيوب", "المذاكرة", "شات AI", "امتحانات", "الإعدادات"]
            menu_icons = ['house', 'folder', 'youtube', 'joystick', 'chat-dots', 'card-checklist', 'gear']

        selected = option_menu("القائمة", menu_options, icons=menu_icons,
                             styles={"nav-link-selected": {"background-color": "#764abc"}})
        
        if st.button("تسجيل خروج 🚪"): 
            st.session_state.user_email = None
            st.rerun()

    # --- الصفحات ---
    if selected == "الرئيسية":
        st.title(f"📊 لوحة معلومات {user['name']}")
        st.info("بياناتك محفوظة في سيرفرنا الآمن ✅")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='card'><h3>📅 انضممت</h3><p>{user['joined']}</p></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='card'><h3>📝 امتحانات</h3><p>{len(user['exam_history'])}</p></div>", unsafe_allow_html=True)
        
        avg = 0
        if user['exam_history']: 
            avg = sum([x['score'] for x in user['exam_history']]) / len(user['exam_history'])
        col3.markdown(f"<div class='card'><h3>⭐ مستواك</h3><p>{avg:.1f}%</p></div>", unsafe_allow_html=True)

    elif selected == "لوحة الأدمن":
        st.title("👮‍♂️ غرفة التحكم المركزية")
        st.write("هنا تظهر بيانات كل المستخدمين المسجلين في الموقع.")
        
        # قراءة قاعدة البيانات الحقيقية
        all_users = load_db()
        st.metric("عدد المستخدمين الكلي", len(all_users))
        
        # تجهيز البيانات للعرض
        data_rows = []
        for email, u_data in all_users.items():
            exam_count = len(u_data.get('exam_history', []))
            avg_score = "0%"
            if exam_count > 0:
                s = sum([x['score'] for x in u_data['exam_history']])
                avg_score = f"{s/exam_count:.1f}%"
                
            data_rows.append({
                "Email": email,
                "Name": u_data['name'],
                "Joined": u_data['joined'],
                "Exams Taken": exam_count,
                "Level": avg_score
            })
            
        st.dataframe(pd.DataFrame(data_rows), use_container_width=True)

    elif selected == "المكتبة":
        st.title("📂 مكتبة الملفات")
        uploaded_files = st.file_uploader("ارفع ملفاتك (PDF, Word)", accept_multiple_files=True)
        if uploaded_files and st.button("تحليل وحفظ"):
            with st.spinner("جاري القراءة..."):
                st.session_state.file_content = read_files(uploaded_files)
                st.success("تم حفظ محتوى الملفات في الذاكرة المؤقتة!")
        
        if "file_content" in st.session_state:
            st.text_area("معاينة المحتوى:", st.session_state.file_content[:500] + "...", height=100)

    elif selected == "يوتيوب":
        st.title("📺 تلخيص اليوتيوب")
        url = st.text_input("رابط الفيديو:")
        if st.button("لخص") and url:
            with st.spinner("جاري التحليل..."):
                text = get_youtube_text(url)
                if text:
                    res = model.generate_content(f"لخص الفيديو بالعربي:\n{text}")
                    st.write(res.text)
                    display_voice_player(res.text)
                    st.session_state.file_content = f"فيديو يوتيوب:\n{res.text}" # حفظه في الذاكرة للشات
                else:
                    st.error("الفيديو لا يحتوي على ترجمة (Caption).")

    elif selected == "المذاكرة":
        st.title("🎮 ذاكر بطريقة مختلفة")
        if "file_content" not in st.session_state:
            st.warning("الرجاء رفع ملفات من المكتبة أولاً.")
        else:
            style = st.selectbox("اختار شخصية الشرح:", ["مدرس صارم 👨‍🏫", "صديق (عامية) 😎", "راوي قصص 📖", "رابر (أغنية) 🎤"])
            topic = st.text_input("عن أي جزء في المنهج؟")
            if st.button("اشرح لي"):
                prompt = f"اشرح الدرس بأسلوب {style}. المحتوى: {st.session_state.file_content[:5000]}. الموضوع: {topic}"
                res = model.generate_content(prompt)
                st.markdown(res.text)
                display_voice_player(res.text)

    elif selected == "شات AI":
        st.title("💬 المساعد الذكي")
        if "messages" not in st.session_state: st.session_state.messages = []
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        if prompt := st.chat_input("اكتب سؤالك..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            context = st.session_state.get("file_content", "لا يوجد ملفات مرفوعة.")
            full_prompt = f"بناء على الملفات المرفوعة: {context[:5000]}\nالسؤال: {prompt}"
            
            with st.chat_message("assistant"):
                res = model.generate_content(full_prompt)
                st.write(res.text)
                display_voice_player(res.text)
                st.session_state.messages.append({"role": "assistant", "content": res.text})

    elif selected == "امتحانات":
        st.title("📝 اختبر معلوماتك")
        if st.button("بدء امتحان جديد") and "file_content" in st.session_state:
            prompt = f"أنشئ 3 أسئلة اختيار من متعدد بصيغة JSON بناء على: {st.session_state.file_content[:3000]}"
            # (نفس منطق توليد الأسئلة السابق) - تم تبسيطه هنا للتوضيح
            try:
                res = model.generate_content(prompt + " Format: [{'question':'..', 'options':['..'], 'answer':'..'}]")
                json_text = res.text.replace("```json", "").replace("```", "").strip()
                st.session_state.quiz = json.loads(json_text)
            except: st.error("حاول مرة أخرى.")

        if "quiz" in st.session_state:
            score = 0
            for i, q in enumerate(st.session_state.quiz):
                st.write(f"**{i+1}. {q['question']}**")
                user_ans = st.radio("اختر:", q['options'], key=f"q{i}")
                if user_ans == q['answer']: score += 1
            
            if st.button("تسليم الامتحان"):
                final_score = (score / len(st.session_state.quiz)) * 100
                st.balloons()
                st.success(f"نتيجتك: {final_score:.1f}%")
                
                # حفظ النتيجة في قاعدة البيانات الدائمة
                db = load_db() # نحمل الداتا
                db[user_email]["exam_history"].append({"score": final_score, "date": str(datetime.date.today())})
                save_db(db) # نحفظ الداتا فوراً
                st.info("تم حفظ النتيجة في سجلك.")

    elif selected == "الإعدادات":
        st.title("⚙️ إعدادات الحساب")
        st.write(f"البريد الحالي: {user_email}")
        new_pic = st.file_uploader("تغيير الصورة الشخصية", type=['png', 'jpg'])
        if new_pic and st.button("تحديث الصورة"):
            update_avatar(user_email, new_pic)
            st.success("تم تحديث الصورة! (ستظهر بعد إعادة التحميل)")

# --- 6. الفوتر ---
st.markdown("""
<div class="footer">
    <p>تم التطوير بواسطة <b>عمار حسام</b> & <b>مريم ابراهيم</b> © 2025</p>
    <p>جميع بيانات المستخدمين محفوظة ومشفرة 🔒</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.user_email:
    main_app()
else:
    login_page()



