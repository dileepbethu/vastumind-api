import os
import base64
import asyncio
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from gtts import gTTS
import httpx
from google import genai

# ── Config ──
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

# ── Models to try in order (fallback chain) ──
MODELS = [
    "gemini-2.5-flash",
]

# ── Self-ping ──
async def self_ping():
    await asyncio.sleep(60)
    while True:
        try:
            async with httpx.AsyncClient() as c:
                await c.get("https://vastumind-api.onrender.com/")
                print("✅ Self-ping successful")
        except:
            pass
        await asyncio.sleep(840)

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(self_ping())
    yield

app = FastAPI(title="VastuMind API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

tower_knowledge = {
    "name": "Wooden Structural Tower Model",
    "floors": 4,
    "about": {
        "built_by": "Civil engineering students of Mahindra University",
        "location": "CSIS Research Centre, Mahindra University, Hyderabad",
        "purpose": "Demonstrate structural engineering principles",
    },
    "elements": {
        "tower_main": {"name": "Complete Tower Structure", "description": "4-storey wooden lattice tower with X-bracing, roof frame, and foundation base plate. Built by Mahindra University civil engineering students at CSIS Research Centre, Hyderabad."},
        "x_bracing": {"name": "X-Bracing Members", "description": "Diagonal X-shaped wooden members resist lateral forces like wind and earthquakes. Work in tension and compression alternately depending on wind direction."},
        "base_plate": {"name": "Foundation Base Plate", "description": "Wide wooden base plate distributes tower weight to foundation. Prevents overturning under lateral loads."},
        "floor_1": {"name": "Ground Floor", "description": "Base level, widest section for stability. Transfers all structural loads to foundation."},
        "floor_2": {"name": "Second Floor", "description": "Mid-level with full X-bracing. Carries vertical and horizontal wind loads."},
        "floor_3": {"name": "Third Floor", "description": "Upper mid-level with wire mesh infill panel demonstrating shear wall concept."},
        "floor_4": {"name": "Fourth Floor", "description": "Topmost level before roof. Experiences maximum sway during wind loads."},
        "roof_frame": {"name": "Roof Frame", "description": "Triangular pitched roof frame. Triangle is most stable shape in structural engineering."},
        "wire_mesh": {"name": "Wire Mesh Panel", "description": "Wire mesh infill on level 3 demonstrates shear wall behaviour in real construction."}
    }
}

def detect_language(text):
    hindi_chars = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
    for char in text:
        if char in hindi_chars:
            return "Hindi"
    return "English"

def ask_gemini(element_id, question, history=[]):
    element = tower_knowledge["elements"].get(
        element_id,
        tower_knowledge["elements"]["tower_main"]
    )

    lang = detect_language(question)
    lang_rule = (
        "Reply in Hindi ONLY."
        if lang == "Hindi"
        else "Reply in English ONLY. No Hindi words at all."
    )

    history_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in history
    ])

    prompt = f"""You are an intelligent VR/AR guide for the wooden structural 
tower model built by civil engineering students of Mahindra University, 
CSIS Research Centre, Hyderabad.

ELEMENT: {element['name']}
DETAILS: {element['description']}

BUILDING:
- 4-storey wooden lattice tower with X-bracing
- Roof: Triangular pitched roof frame
- Base: Wooden foundation plate
- Built by: Mahindra University students

CONVERSATION:
{history_text}

LANGUAGE RULE: {lang_rule}
RULES: 
- Max 3 clear sentences
- Who are you → say you are the AI guide for this tower
- Off-topic → say you specialize in this tower
- Never make up facts

QUESTION: {question}
ANSWER:"""

    import time
    last_error = None

    # Try gemini-2.5-flash AND gemini-1.5-flash as real backup
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-flash"]

    for attempt, model_name in enumerate(models_to_try):
        try:
            print(f"Attempt {attempt + 1} with {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            answer = response.text.strip()
            print(f"✅ Success with {model_name}")

            updated_history = history + [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ]
            return answer, updated_history

        except Exception as e:
            print(f"❌ {model_name} failed: {str(e)[:150]}")
            last_error = e
            time.sleep(3)  # wait 3 full seconds before next try
            continue

    # All attempts genuinely failed — return graceful fallback
    print(f"⚠️ All models failed, using fallback. Last error: {last_error}")
    fallback_answer = (
        "I am the AI guide for this structural tower at Mahindra University CSIS. "
        "The AI service is experiencing high demand right now. Please try asking again in a few seconds."
    )
    updated_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": fallback_answer}
    ]
    return fallback_answer, updated_history
def make_audio(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            with open(f.name, "rb") as audio:
                return base64.b64encode(audio.read()).decode()
    except Exception as e:
        print(f"TTS error: {e}")
        return ""

class Question(BaseModel):
    element_id: str = "tower_main"
    question: str
    history: list = []

@app.get("/")
def root():
    return {"status": "VastuMind API running!", "model": "Gemini 2.0 Flash (with fallback)", "building": "Mahindra University CSIS Tower"}

@app.get("/building")
def get_building():
    return {"name": tower_knowledge["name"], "location": tower_knowledge["about"]["location"], "built_by": tower_knowledge["about"]["built_by"], "floors": tower_knowledge["floors"], "elements": list(tower_knowledge["elements"].keys())}

@app.post("/ask")
async def ask(q: Question):
    try:
        answer, updated_history = ask_gemini(q.element_id, q.question, q.history)
        lang = detect_language(q.question)
        audio = make_audio(answer, lang="hi" if lang == "Hindi" else "en")
        return {"answer": answer, "audio_base64": audio, "element_id": q.element_id, "history": updated_history, "language": lang}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/ask_unreal")
async def ask_unreal(element_id: str = "tower_main", question: str = "Tell me about this structure"):
    try:
        answer, _ = ask_gemini(element_id, question, [])
        lang = detect_language(question)
        audio = make_audio(answer, lang="hi" if lang == "Hindi" else "en")
        return {"answer": answer, "audio_base64": audio, "element_id": element_id, "language": lang}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
def health():
    return {"status": "ok", "api": "vastumind-api.onrender.com", "models": MODELS}
