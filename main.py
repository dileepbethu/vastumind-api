import os
import base64
import asyncio
import tempfile
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from gtts import gTTS
import httpx

from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# MODELS
# ============================================================

MODELS = [
    "gemini-2.5-flash",
]


# ============================================================
# SELF-PING
# ============================================================

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


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# HERITAGE KNOWLEDGE BASE
# ============================================================

heritage_knowledge = {
    # ========================================================
    # TEMPLE
    # ========================================================
    "temple": {
        "name": "Sri Ramalingeshwara Swamy Temple",
        "location": "Unspecified location in India",
        "deity": "Lord Shiva",
        "estimated_age": "Medieval (e.g., 12th Century)",
        "architecture_style": "Dravidian",
        "shape": "Rectangular with multiple shrines",
        "overview": "The Sri Ramalingeshwara Swamy Temple is an ancient temple dedicated to Lord Shiva, known for its intricate carvings and historical significance. It represents a significant example of Dravidian architecture."
    },

    # ========================================================
    # HISTORY
    # ========================================================
    "history": {
        "foundation": "Believed to be founded during the Chola dynasty.",
        "invasions": "Survived multiple historical invasions, though some parts were damaged.",
        "restoration": "Underwent various restoration efforts over centuries.",
        "current_status": "Active place of worship and a heritage site."
    },

    # ========================================================
    # ARCHITECTURE
    # ========================================================
    "architecture": {
        "style": "Dravidian architecture, characterized by pyramidal towers (vimanas) and mandapams (halls).",
        "materials": "Primarily constructed from granite and sandstone.",
        "unique_features": "Includes a distinctive 'Padma and Nakshatra' layout, ornamental tiers, and miniature shrines."
    },

    # ========================================================
    # PILLAR
    # ========================================================
    "pillar": {
        "title": "Historic Temple Pillar",
        "importance": "Crucial to the temple's structural integrity and aesthetic design.",
        "description": "An elaborately carved stone pillar, featuring various deities, mythical creatures, and geometric patterns.",
        "historical_significance": "Each carving tells a story from Hindu mythology or depicts daily life from the period of its creation.",
        "engineering": "Showcases advanced ancient stone masonry techniques, including interlocking systems without mortar.",
        "research_value": "Provides valuable insights into medieval craftsmanship, religious practices, and architectural engineering."
    },

    # ========================================================
    # ANNOTATIONS
    # ========================================================

    "annotations": {

        "temple_blueprint": {

            "title":
                "Temple Blueprint Sculpture",

            "description":
                "Ancient Temple Blueprint",

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


    # ========================================================
    # SCULPTURES
    # ========================================================

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


    # ========================================================
    # VISITOR INFORMATION
    # ========================================================

    "visitor_information": {

        "main_attraction":
            "The sculptured pillar is one of the primary attractions inside the temple because of its artistic, historical and engineering significance.",

        "photography":
            "Visitors often study and photograph the pillar because every side contains different carvings.",

        "recommendation":
            "Walk around all four sides of the pillar to observe different sculptures and architectural details."
    },


    # ========================================================
    # AI CONTEXT
    # ========================================================

    "ai_context": {

        "role":
            "You are HeritageLens AI.",

        "behavior": [
            "Answer only using this temple information.",
            "Explain in simple English and if particularly asked in hindi.",
            "If asked about carvings, describe the sculptures visible on the pillar.",
            "If the user asks historical questions, answer using the history section.",
            "If the answer is unavailable, politely state that the available temple knowledge does not contain that information."
        ]
    }
}


# ============================================================
# ELEMENT ID → KNOWLEDGE MAPPING
# ============================================================
#
# Unreal sends IDs such as:
#
# pillar_02
# pillar_03
# pillar_04
#
# These IDs identify the actual 3D element.
#
# The mapping tells the AI which knowledge section belongs
# to that element.
#
# Add more Unreal element IDs here as your project grows.
# ============================================================

ELEMENT_TO_KNOWLEDGE = {

    "pillar_02": "pillar",
    "pillar_03": "pillar",
    "pillar_04": "pillar",

    "temple_blueprint": "temple_blueprint",

    "temple": "temple"
}


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    hindi_chars = set(
        "अआइईउऊएऐओऔकखगघचछजझटठडढण"
        "तथदधनपफबभमयरलवशषसह"
    )

    for char in text:
        if char in hindi_chars:
            return "Hindi"

    return "English"


# ============================================================
# GET ELEMENT CONTEXT
# ============================================================

def get_element_context(element_id):

    # --------------------------------------------------------
    # First check whether the Unreal ID has a mapping.
    # --------------------------------------------------------

    knowledge_key = ELEMENT_TO_KNOWLEDGE.get(element_id)

    if knowledge_key == "pillar":

        pillar = heritage_knowledge["pillar"]

        return f"""
CURRENT HERITAGE ELEMENT

Element ID:
{element_id}

Element Type:
Historic Temple Pillar

Title:
{pillar['title']}

Importance:
{pillar['importance']}

Description:
{pillar['description']}

Historical Significance:
{pillar['historical_significance']}

Engineering:
{pillar['engineering']}

Research Value:
{pillar['research_value']}

SPATIAL GROUNDING:

The user is currently viewing and interacting with the specific
3D heritage element identified as {element_id}.

This element is a historic temple pillar.

When the user says:
"this"
"it"
"this pillar"
"this feature"
"here"

interpret those references as referring to the currently selected
3D element unless the user explicitly asks about the entire temple.
"""


    # --------------------------------------------------------
    # Temple blueprint annotation
    # --------------------------------------------------------

    if knowledge_key == "temple_blueprint":

        annotation = heritage_knowledge["annotations"]["temple_blueprint"]

        return f"""
CURRENT HERITAGE ELEMENT

Element ID:
{element_id}

Title:
{annotation['title']}

Description:
{annotation['description']}

Overview:
{annotation['knowledge']['overview']}

Architecture:
{annotation['knowledge']['architecture']}

Importance:
{annotation['knowledge']['importance']}

Engineering:
{annotation['knowledge']['engineering']}

History:
{annotation['knowledge']['history']}

Visitor Note:
{annotation['knowledge']['visitor_note']}

SPATIAL GROUNDING:

The user is currently viewing and interacting with this specific
3D heritage element.

When the user says:
"this"
"it"
"this feature"
"here"

interpret those references as referring to this selected
3D element unless the user explicitly asks about the entire temple.
"""


    # --------------------------------------------------------
    # Entire temple
    # --------------------------------------------------------

    if knowledge_key == "temple":

        temple = heritage_knowledge["temple"]

        return f"""
CURRENT HERITAGE ELEMENT

Element ID:
{element_id}

This selection refers to the overall temple structure.

Temple:
{temple['name']}

Location:
{temple['location']}

Deity:
{temple['deity']}

Age:
{temple['estimated_age']}

Architecture:
{temple['architecture_style']}

Shape:
{temple['shape']}

Overview:
{temple['overview']}
"""


    # --------------------------------------------------------
    # Unknown element
    # --------------------------------------------------------

    return ""


# ============================================================
# GEMINI HERITAGE AI
# ============================================================

def ask_gemini(element_id, question, history=None):

    if history is None:
        history = []

    annotation_context = get_element_context(element_id)

    lang = detect_language(question)

    lang_rule = (
        "Reply in Hindi ONLY."
        if lang == "Hindi"
        else "Reply in English ONLY. No Hindi words at all."
    )


    # --------------------------------------------------------
    # Conversation history
    # --------------------------------------------------------

    history_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in history
    ])


    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are HeritageLens AI, an intelligent virtual guide for
Sri Ramalingeshwara Swamy Temple.

You help visitors understand:

- temple architecture
- historical significance
- stone carvings
- sculptures
- pillars
- Hindu iconography


INSTRUCTIONS

• You are HeritageLens AI, an intelligent museum and heritage guide.

• Use the provided HeritageLens knowledge as the primary source
  when answering questions about this temple.

• If the visitor asks broader questions about Indian history,
  temple architecture, archaeology, sculpture, conservation,
  structural engineering, or Hindu culture, you may answer
  using your general knowledge.

• Clearly distinguish between information from the HeritageLens
  knowledge base and general historical knowledge whenever necessary.

• Never invent facts specifically about Sri Ramalingeshwara Swamy Temple.

• If you are genuinely uncertain about a temple-specific fact,
  say that the information is not currently available.


LANGUAGE INSTRUCTIONS

• By default, reply in the same language used by the visitor.

• If the visitor explicitly asks:

  - "Explain in Hindi"
  - "Answer in Hindi"
  - "Explain in Telugu"
  - "தமிழில் விளக்கவும்"
  - "Explain in English"

  then respond completely in that requested language,
  regardless of the language of the question.

• Continue using that language until the visitor requests another language.

• Explain naturally like an experienced museum guide.

• Keep answers concise unless the visitor asks for more detail.


============================================================
TEMPLE KNOWLEDGE
============================================================

Temple:
{heritage_knowledge["temple"]}

History:
{heritage_knowledge["history"]}

Architecture:
{heritage_knowledge["architecture"]}

Pillar:
{heritage_knowledge["pillar"]}

Sculptures:
{heritage_knowledge["sculptures"]}

Visitor Information:
{heritage_knowledge["visitor_information"]}


============================================================
CURRENT SPATIAL CONTEXT
============================================================

{annotation_context}


============================================================
CONVERSATION
============================================================

{history_text}


LANGUAGE RULE:

{lang_rule}


RULES

• Maximum 4 sentences.

• You are HeritageLens AI.

• You are the virtual guide of Sri Ramalingeshwara Swamy Temple.

• If the visitor asks about the current selected element,
  focus on that element.

• Never invent facts.

QUESTION:

{question}

ANSWER:
"""


    # ========================================================
    # GEMINI RESPONSE GENERATION
    # ========================================================
    # google-genai 2.x uses client.models.generate_content().
    # ========================================================

    response = client.models.generate_content(
        model=MODELS[0],
        contents=prompt
    )

    answer = (response.text or "").strip()

    if not answer:
        answer = "I could not generate an answer for that question."

    # Update history for the next turn
    updated_history = history + [
        {"role": "USER", "content": question},
        {"role": "MODEL", "content": answer}
    ]

    return answer, updated_history


# ============================================================
# MAKE AUDIO
# ============================================================

def make_audio(text: str, lang: str = "en") -> str:
    """Converts text to speech using gTTS and returns base64 encoded audio."""
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as fp:
            tts.save(fp.name)
            fp.seek(0) # Go to the beginning of the file
            encoded_audio = base64.b64encode(fp.read()).decode("utf-8")
        return encoded_audio
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""


# ============================================================
# JSON QUESTION MODEL
# ============================================================

class Question(BaseModel):

    element_id: str = "temple"

    question: str

    history: list = []


# ============================================================
# ROOT
# ============================================================

@app.head("/")
def root_head():
    return None


@app.get("/")
def root():

    return {
        "status": "HeritageLens API Running",
        "model": "Gemini 2.5 Flash",
        "temple": "Sri Ramalingeshwara Swamy Temple"
    }


# ============================================================
# TEMPLE INFO
# ============================================================

@app.get("/temple")
def get_temple():

    return {

        "name":
            heritage_knowledge["temple"]["name"],

        "location":
            heritage_knowledge["temple"]["location"],

        "deity":
            heritage_knowledge["temple"]["deity"],

        "age":
            heritage_knowledge["temple"]["estimated_age"],

        "style":
            heritage_knowledge["temple"]["architecture_style"]
    }


# ============================================================
# EXISTING JSON /ask ENDPOINT
#
# Unreal sends:
#
# POST /voice-query
#
# Content-Type: audio/wav
#
# X-Heritage-Element-ID: pillar_02
#
# [RAW WAV DATA]
#
# ============================================================

@app.post("/ask")
async def ask_endpoint(payload: Question):
    try:
        print("🧠 JSON question received")
        print(f"   Element: {payload.element_id}")
        print(f"   Question: {payload.question}")

        answer, updated_history = await asyncio.to_thread(
            ask_gemini,
            payload.element_id,
            payload.question,
            payload.history
        )

        lang = detect_language(payload.question)

        audio = await asyncio.to_thread(
            make_audio,
            answer,
            "hi" if lang == "Hindi" else "en"
        )

        return {
            "question": payload.question,
            "answer": answer,
            "audio_base64": audio,
            "element_id": payload.element_id,
            "history": updated_history,
            "language": lang
        }

    except Exception as e:
        print(f"❌ JSON /ask error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/voice-query")
async def voice_query(request: Request):

    try:

        # ====================================================
        # 1. GET ELEMENT ID FROM HEADER
        # ====================================================

        element_id = request.headers.get(
            "X-Heritage-Element-ID",
            "temple"
        ).strip()


        print(
            f"🎯 Voice query element ID: {element_id}"
        )


        # ====================================================
        # 2. READ RAW WAV DATA
        # ====================================================

        audio_bytes = await request.body()


        print(
            f"🎤 Received audio bytes: "
            f"{len(audio_bytes)}"
        )


        # ====================================================
        # 3. VALIDATE AUDIO
        # ====================================================

        if not audio_bytes:

            return JSONResponse(
                {
                    "error":
                        "No audio data received."
                },
                status_code=400
            )


        # Basic WAV validation

        if not audio_bytes.startswith(b"RIFF"):

            return JSONResponse(
                {
                    "error":
                        "Invalid WAV audio. "
                        "Expected RIFF WAV data."
                },
                status_code=400
            )


        # ====================================================
        # 4. SEND AUDIO TO GEMINI FOR TRANSCRIPTION
        # ====================================================

        print(
            "🎧 Sending WAV audio to Gemini..."
        )


        transcription_prompt = """
Listen carefully to this audio recording.

Transcribe exactly what the visitor said.

Return ONLY the spoken question.

Do not explain the question.
Do not answer the question.
Do not add quotation marks.
Do not add commentary.

If the visitor speaks in Hindi, return the Hindi transcription.
If the visitor speaks in English, return the English transcription.
"""


        transcription_response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODELS[0],
            contents=[
                transcription_prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav"
                )
            ]
        )


        question = transcription_response.text.strip()


        print(
            f"📝 Transcribed question: {question}"
        )


        # ====================================================
        # 5. VALIDATE TRANSCRIPTION
        # ====================================================

        if not question:

            return JSONResponse(
                {
                    "error":
                        "Could not understand the audio."
                },
                status_code=400
            )


        # ====================================================
        # 6. SEND QUESTION + ELEMENT ID TO HERITAGE AI
        # ====================================================

        print(
            f"🧠 Asking HeritageLens AI..."
        )

        print(
            f"   Element: {element_id}"
        )

        print(
            f"   Question: {question}"
        )


        answer, updated_history = await asyncio.to_thread(
            ask_gemini,
            element_id,
            question,
            []
        )


        # ====================================================
        # 7. DETECT LANGUAGE
        # ====================================================

        lang = detect_language(question)


        # ====================================================
        # 8. GENERATE AI VOICE
        # ====================================================

        audio = await asyncio.to_thread(
            make_audio,
            answer,
            "hi" if lang == "Hindi" else "en"
        )


        # ====================================================
        # 9. RETURN RESPONSE TO UNREAL
        # ====================================================

        return {

            "question":
                question,

            "answer":
                answer,

            "audio_base64":
                audio,

            "element_id":
                element_id,

            "history":
                updated_history,

            "language":
                lang
        }


    except Exception as e:

        print(
            f"❌ Voice query error: {str(e)}"
        )


        return JSONResponse(

            {
                "error":
                    str(e)
            },

            status_code=500
        )


# ============================================================
# EXISTING UNREAL GET ENDPOINT

# ============================================================

@app.get("/ask_unreal")
async def ask_unreal(
    element_id: str = "temple",
    question: str = "Tell me about this structure"
):

    try:

        answer, _ = ask_gemini(
            element_id,
            question,
            []
        )


        lang = detect_language(question)


        audio = await asyncio.to_thread(
            make_audio,
            answer,
            "hi" if lang == "Hindi" else "en"
        )


        return {

            "answer":
                answer,

            "audio_base64":
                audio,

            "element_id":
                element_id,

            "language":
                lang
        }


    except Exception as e:

        return JSONResponse(
            {
                "error": str(e)
            },
            status_code=500
        )


# ============================================================
# HEALTH CHECK

# ============================================================

@app.get("/health")
def health():

    return {

        "status": "ok",

        "api":
            "vastumind-api.onrender.com",

        "models":
            MODELS
    }


#================================================================================
@app.get("/routes")
def routes():
    return [
        {
            "path": route.path,
            "methods": list(route.methods or [])
        }
        for route in app.routes
    ]
