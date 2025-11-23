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

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="المدرس الشامل (Unlimited)", page_icon="🛡️", layout="wide")

# --- 2. إعداد المفتاح ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. دوال القراءة الذكية (Smart Readers) ---

def get_pdf_text(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except: return "[حدث خطأ أثناء قراءة ملف PDF]"

def get_docx_text(uploaded_file):
    try:
        doc = docx.Document(uploaded_file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except: return "[حدث خطأ أثناء قراءة ملف Word]"

def get_excel_csv_text(uploaded_file):
    try:
        # لو اكسيل أو CSV بنحوله لنص
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df.to_string() # تحويل الجدول لنص عشان الموديل يفهمه
    except: return "[حدث خطأ أثناء قراءة ملف البيانات]"

def read_any_text_file(uploaded_file):
    # دي الدالة السحرية لأي ملف نصي (كود، txt، json، srt...)
    try:
        # بنحاول نفك تشفير الملف حتى لو فيه رموز غريبة (errors='ignore')
        return uploaded_file.getvalue().decode("utf-8", errors='ignore')
    except: return "[ملف غير قابل للقراءة النصية]"

def clean_text(text):
    return text.replace("```json", "").replace("```graphviz", "").replace("```", "").strip()

def text_to_speech_html(text, lang='ar'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def get_youtube_text(video_url):
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        full_text = " ".join([entry['text'] for entry in transcript])
        return full_text
    except: return None

# --- 4. Session State ---
if "messages" not in st.session_state: st.session_state.messages = []
if "file_content" not in st.session_state: st.session_state.file_content = ""
if "exam_history" not in st.session_state: st.session_state.exam_history = []
if "current_quiz" not in st.session_state: st.session_state.current_quiz = None
if "flashcards" not in st.session_state: st.session_state.flashcards = []

# --- 5. القائمة الجانبية (تم إلغاء القيود على نوع الملفات) ---
with st.sidebar:
    st.header("🛡️ لوحة التحكم")
    mode = st.radio("الوضع:", 
                    ["💬 المذاكرة والشات", "📺 يوتيوب", "🧠 خرائط", "🃏 بطاقات", "📝 اختبار", "📊 تقييم"])
    
    st.divider()
    
    if mode != "📺 يوتيوب":
        st.subheader("📂 ارفع أي ملف في الدنيا")
        # التعديل السحري: شلنا type=... عشان يقبل كله
        uploaded_files = st.file_uploader("Drop any file here", accept_multiple_files=True)
        
        if uploaded_files and st.button("تحليل الملفات 🚀"):
            with st.spinner("جاري فك شفرة الملفات..."):
                combined_text = ""
                file_count = 0
                
                # حلقة تكرارية ذكية بتشوف نوع الملف وتختار الأداة المناسبة
                for file in uploaded_files:
                    try:
                        file_text = ""
                        fname = file.name.lower()
                        combined_text += f"\n\n--- ملف: {file.name} ---\n"
                        
                        # توجيه الملفات للأدوات المناسبة
                        if fname.endswith('.pdf'):
                            file_text = get_pdf_text(file)
                        elif fname.endswith('.docx'):
                            file_text = get_docx_text(file)
                        elif fname.endswith(('.xlsx', '.xls', '.csv')):
                            file_text = get_excel_csv_text(file)
                        elif fname.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            try:
                                image = Image.open(file)
                                res = model.generate_content(["استخرج كل النصوص المكتوبة في الصورة", image])
                                file_text = res.text
                            except: file_text = "[صورة غير صالحة]"
                        else:
                            # لأي ملف تاني (txt, py, java, html, json...)
                            file_text = read_any_text_file(file)
                        
                        combined_text += file_text
                        file_count += 1
                        
                    except Exception as e:
                        # لو ملف ضرب، نكتب اسمه ونكمل عادي من غير ما البرنامج يقع
                        combined_text += f"\n[فشل قراءة هذا الملف: {str(e)}]\n"
                
                st.session_state.file_content = combined_text
                if file_count > 0:
                    st.success(f"تمت قراءة {file_count} ملفات بنجاح! مهما كان نوعهم.")
                else:
                    st.warning("لم يتم استخراج نصوص مفيدة.")

# --- 6. باقي الأوضاع (زي ما هي) ---

if mode == "💬 المذاكرة والشات":
    st.title("💬 الشات المدرع")
    if not st.session_state.file_content: st.info("ارفع أي ملف (Excel, Word, Code...) 👈")
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("اكتب سؤالك..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("بيحلل..."):
                    # نظام أمان عشان لو النص كبير جداً
                    content_snippet = st.session_state.file_content[:30000] 
                    full_prompt = f"المحتوى:\n{content_snippet}\n\nسؤال: {prompt}\nجاوب باحترافية."
                    try:
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error("الذكاء الاصطناعي واجه مشكلة بسيطة، حاول تسأل بصيغة تانية.")

elif mode == "📺 يوتيوب":
    st.title("📺 يوتيوب")
    url = st.text_input("الرابط:")
    if st.button("لخص") and url:
        yt_text = get_youtube_text(url)
        if yt_text:
            res = model.generate_content(f"لخص: {yt_text}")
            st.write(res.text)
            st.session_state.file_content = yt_text
        else: st.error("فيديو بدون ترجمة أو رابط خطأ")

elif mode == "🧠 خرائط":
    st.title("🧠 خرائط")
    if st.button("رسم") and st.session_state.file_content:
        res = model.generate_content(f"Create Graphviz DOT code for: {st.session_state.file_content[:5000]} inside graphviz block")
        try: st.graphviz_chart(clean_text(res.text))
        except: st.error("تعذر الرسم")

elif mode == "🃏 بطاقات":
    st.title("🃏 بطاقات")
    if st.button("إنشاء") and st.session_state.file_content:
        try:
            res = model.generate_content(f"Extract 5 terms JSON from: {st.session_state.file_content[:4000]} as [{{'term':'','definition':''}}]")
            st.session_state.flashcards = json.loads(clean_text(res.text))
        except: pass
    for c in st.session_state.flashcards: st.info(f"{c['term']}: {c['definition']}")

elif mode == "📝 اختبار":
    st.title("📝 اختبار")
    if st.button("جديد") and st.session_state.file_content:
        try:
            res = model.generate_content(f"Create 5 MCQ JSON from: {st.session_state.file_content[:5000]} as [{{'question':'','options':[],'answer':''}}]")
            st.session_state.current_quiz = json.loads(clean_text(res.text))
            st.rerun()
        except: pass
    if st.session_state.current_quiz:
        with st.form("q"):
            ans = {}
            for i,q in enumerate(st.session_state.current_quiz):
                st.write(q['question'])
                ans[i] = st.radio("", q['options'], key=i)
            if st.form_submit_button("تصحيح"):
                sc = sum([1 for i,q in enumerate(st.session_state.current_quiz) if ans[i]==q['answer']])
                st.write(f"{sc}/5")
                st.session_state.exam_history.append({"Score": sc*20})

elif mode == "📊 تقييم":
    st.title("📊 تقييم")
    if st.session_state.exam_history: st.line_chart(pd.DataFrame(st.session_state.exam_history)['Score'])
