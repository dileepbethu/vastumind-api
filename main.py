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
  "temple": {
    "name": "Sri Ramalingeshwara Swamy Temple",
    "location": "Andhra Pradesh, India",
    "deity": "Lord Shiva (Sri Ramalingeshwara Swamy)",
    "estimated_age": "Approximately 1000–1100 years",
    "architecture_style": "Kalyani Chalukya Period",
    "shape": "Padma (Lotus) and Nakshatra (Star) Layout",
    "overview": "Sri Ramalingeshwara Swamy Temple is an ancient Shiva temple known for its remarkable stone architecture, intricate carvings, sculptured pillars, and historical significance. The temple preserves traditional South Indian temple architecture and contains numerous sculptures depicting Hindu deities and symbolic motifs."
  },

  "history": {
    "construction": "According to local temple tradition, the temple was constructed during the Kalyani Chalukya period around one thousand years ago.",
    "historical_events": [
      "The temple experienced damage during invasions traditionally associated with the Mughal period under Aurangzeb.",
      "Several sculptures and idols were damaged or removed.",
      "Many recovered idols were later preserved by the Archaeological Department and local villagers.",
      "Some original sculptures are now displayed in nearby temples and museums."
    ]
  },

  "architecture": {
    "layout": "Padma and Nakshatra based temple planning.",
    "makara_toranam": {
      "description": "The entrance contains a beautifully carved Makara Toranam.",
      "symbolism": "Six Rudra representations symbolize the six Indian seasons (Ritus)."
    },
    "special_features": [
      "Highly detailed granite carvings",
      "Mythological sculptures",
      "Temple architectural blueprints carved into stone",
      "Decorative floral motifs",
      "Sacred geometric design"
    ]
  },

  "pillar": {
    "title": "Historic Temple Pillar",
    "importance": "The sculptured pillar is considered one of the most important surviving architectural elements inside the temple.",
    "description": "The pillar contains detailed sculptures of Hindu deities, decorative carvings, symbolic motifs, miniature temple architecture and religious artwork carved directly into the granite.",
    "historical_significance": "According to local tradition, while several pillars inside the temple were damaged during historical invasions, this particular pillar remained largely intact and survives without major structural cracks.",
    "engineering": "The pillar demonstrates exceptional stone craftsmanship and structural stability despite its great age.",
    "research_value": "The pillar provides valuable information about medieval South Indian temple architecture, iconography, sculpture techniques and structural engineering."
  },

     "annotations": {

        "temple_blueprint": {

            "title": "Temple Blueprint Sculpture",

            "description": "Ancient Temple Blueprint",

            "knowledge": {

                "overview":
                "This sculpture carved on the temple pillar represents the architectural blueprint of the Sri Ramalingeshwara Swamy Temple. Medieval temple builders carved miniature representations of the temple onto important pillars as both decoration and documentation.",

                "architecture":
                "The sculpture represents the temple's Dravidian architecture with ornamental tiers, miniature shrines and symmetrical design inspired by the Padma and Nakshatra temple layout.",

                "importance":
                "It preserves the architectural identity of the temple and demonstrates the exceptional craftsmanship of medieval stone sculptors.",

                "engineering":
                "The blueprint carving illustrates proportional temple planning and stone engineering techniques used during construction.",

                "history":
                "Although several sculptures inside the temple were damaged during historical invasions, this blueprint carving survived and continues to preserve valuable architectural information.",

                "visitor_note":
                "Visitors are encouraged to closely observe the miniature temple carving because it closely resembles the actual temple structure."

            }
        }

    },
    

  "sculptures": {
    "deities": [
      "Parvati",
      "Lord Shiva",
      "Various Hindu deities",
      "Guardian figures",
      "Sacred animals"
    ],
    "motifs": [
      "Floral carvings",
      "Temple miniature structures",
      "Mythological figures",
      "Sacred symbols"
    ]
  },

  "visitor_information": {
    "main_attraction": "The sculptured pillar is one of the primary attractions inside the temple because of its artistic, historical and engineering significance.",
    "photography": "Visitors often study and photograph the pillar because every side contains different carvings.",
    "recommendation": "Walk around all four sides of the pillar to observe different sculptures and architectural details."
  },

  "ai_context": {
    "role": "You are HeritageLens AI.",
    "behavior": [
      "Answer only using this temple information.",
      "Explain in simple English.",
      "If asked about carvings, describe the sculptures visible on the pillar.",
      "If the user asks historical questions, answer using the history section.",
      "If the answer is unavailable, politely state that the available temple knowledge does not contain that information."
    ]
  }
}

def detect_language(text):
    hindi_chars = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
    for char in text:
        if char in hindi_chars:
            return "Hindi"
    return "English"

def ask_gemini(element_id, question, history=[]):
    annotation = tower_knowledge.get("annotations", {}).get(element_id)

    if annotation:    
        annotation_context = f"""
CURRENT ANNOTATION

Title:
{annotation['title']}

Description:
{annotation['description']}

Knowledge:
{annotation['knowledge']}
"""
    else:
        annotation_context = ""

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

    prompt = f"""You are HeritageLens AI, an intelligent virtual guide for
Sri Ramalingeshwara Swamy Temple.

You help visitors understand the temple architecture,
historical significance,
stone carvings,
sculptures,
pillars,
and Hindu iconography.

Only answer using the supplied knowledge base.
If information is unavailable,
say that it is not available in the current HeritageLens database.

TEMPLE KNOWLEDGE

Temple:
{tower_knowledge["temple"]}

History:
{tower_knowledge["history"]}

Architecture:
{tower_knowledge["architecture"]}

Pillar:
{tower_knowledge["pillar"]}

Sculptures:
{tower_knowledge["sculptures"]}

Visitor Information:
{tower_knowledge["visitor_information"]}
{annotation_context}
CONVERSATION:
{history_text}

LANGUAGE RULE: {lang_rule}
RULES: 
RULES

• Maximum 4 sentences.

• You are HeritageLens AI.

• You are the virtual guide of Sri Ramalingeshwara Swamy Temple.

• Use only the supplied knowledge.

• If the visitor asks about the current annotation,
focus on that annotation.

• If information is unavailable,
say it is not available in the HeritageLens database.

• Never invent facts.

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
        "I am the AI guide for this structure. "
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
    element_id: str = "temple"
    question: str
    history: list = []

@app.get("/")
def root():
    return {
    "status":"HeritageLens API Running",
    "model":"Gemini 2.5 Flash",
    "temple":"Sri Ramalingeshwara Swamy Temple"
}

@app.get("/temple")
def get_temple():
    return {
        "name": tower_knowledge["temple"]["name"],
        "location": tower_knowledge["temple"]["location"],
        "deity": tower_knowledge["temple"]["deity"],
        "age": tower_knowledge["temple"]["estimated_age"],
        "style": tower_knowledge["temple"]["architecture_style"]
    }
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
async def ask_unreal(element_id: str = "temple", question: str = "Tell me about this structure"):
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
