
import os
import base64
import tempfile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
from gtts import gTTS

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="VastuMind API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tower_knowledge = {
    "name": "Wooden Structural Tower Model",
    "floors": 4,
    "about": {
        "built_by": "Civil engineering students of Mahindra University",
        "location": "CSIS Research Centre, Mahindra University, Hyderabad",
        "purpose": "Demonstrate structural engineering principles",
    },
    "elements": {
        "tower_main": {
            "name": "Complete Tower Structure",
            "description": "4-storey wooden lattice tower with X-bracing, roof frame, and foundation base plate. Built by Mahindra University civil engineering students."
        },
        "x_bracing": {
            "name": "X-Bracing Members",
            "description": "Diagonal X-shaped wooden members resist lateral forces like wind and earthquakes. Work in tension and compression alternately depending on wind direction."
        },
        "base_plate": {
            "name": "Foundation Base Plate",
            "description": "Wide wooden base plate distributes tower weight to foundation. Prevents overturning under lateral loads. Widest section for maximum stability."
        },
        "floor_1": {
            "name": "Ground Floor",
            "description": "Base level, widest section for stability. Transfers all structural loads down to the foundation. Experiences highest compressive forces."
        },
        "floor_2": {
            "name": "Second Floor",
            "description": "Mid-level with full X-bracing pattern. Carries both vertical dead loads and horizontal wind loads through diagonal members."
        },
        "floor_3": {
            "name": "Third Floor",
            "description": "Upper mid-level with wire mesh infill panel demonstrating shear wall concept. Slightly narrower than lower floors."
        },
        "floor_4": {
            "name": "Fourth Floor",
            "description": "Topmost structural level before roof. Experiences maximum sway during wind loads. Lightest section of the tower."
        },
        "roof_frame": {
            "name": "Roof Frame",
            "description": "Triangular pitched roof frame at the top. Triangle is the most stable shape in structural engineering — cannot deform without changing member lengths."
        },
        "wire_mesh": {
            "name": "Wire Mesh Panel",
            "description": "Wire mesh infill on level 3 demonstrates shear wall behaviour. In real construction this represents a concrete shear wall or glass curtain wall panel."
        }
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
    prompt = f"""You are VastuMind — AR guide for wooden structural
tower at CSIS Research Centre, Mahindra University, Hyderabad.
Built by civil engineering students of Mahindra University.

ELEMENT: {element["name"]}
DETAILS: {element["description"]}

CONVERSATION:
{history_text}

LANGUAGE RULE: {lang_rule}
RULES: Max 3 sentences. If off-topic say you are VastuMind specialized
in this tower. Never make up facts.

QUESTION: {question}
ANSWER:"""
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    answer = response.text.strip()
    updated_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer}
    ]
    return answer, updated_history

def make_audio(text, lang="en"):
    tts = gTTS(text=text, lang=lang, slow=False)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tts.save(f.name)
        with open(f.name, "rb") as audio:
            return base64.b64encode(audio.read()).decode()

class Question(BaseModel):
    element_id: str = "tower_main"
    question: str
    history: list = []

@app.get("/")
def root():
    return {
        "status": "VastuMind API running!",
        "model": "Gemini 2.5 Flash",
        "building": "Mahindra University CSIS Tower"
    }

@app.get("/building")
def get_building():
    return {
        "name": tower_knowledge["name"],
        "location": tower_knowledge["about"]["location"],
        "built_by": tower_knowledge["about"]["built_by"],
        "floors": tower_knowledge["floors"],
        "elements": list(tower_knowledge["elements"].keys())
    }

@app.post("/ask")
async def ask(q: Question):
    try:
        answer, updated_history = ask_gemini(
            q.element_id, q.question, q.history
        )
        lang = detect_language(q.question)
        audio = make_audio(
            answer,
            lang="hi" if lang == "Hindi" else "en"
        )
        return {
            "answer": answer,
            "audio_base64": audio,
            "element_id": q.element_id,
            "history": updated_history,
            "language": lang
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Add this at the bottom of main.py in GitHub
import asyncio
import httpx
from contextlib import asynccontextmanager

async def self_ping():
    """Ping self every 14 minutes to prevent Render sleep"""
    await asyncio.sleep(60)  # wait 1 min after startup
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get("https://vastumind-api.onrender.com/")
                print("✅ Self-ping successful")
        except:
            pass
        await asyncio.sleep(840)  # 14 minutes

@asynccontextmanager
async def lifespan(app):
    # Start self-ping on startup
    asyncio.create_task(self_ping())
    yield

# Update your app definition to use lifespan:
app = FastAPI(title="VastuMind API", lifespan=lifespan)
