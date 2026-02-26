import json
import os
import time
from openai import OpenAI
from models import db, Conversation

# In-memory cache
_cache = {"data": None, "expires": 0}
CACHE_TTL = 3600  # 1 hour


def get_insights():
    """Return AI-generated insights, cached for 1 hour."""
    now = time.time()
    if _cache["data"] and now < _cache["expires"]:
        return _cache["data"]

    data = _generate_insights()
    _cache["data"] = data
    _cache["expires"] = now + CACHE_TTL
    return data


def _generate_insights():
    """Fetch recent conversations and analyze with GPT-4o-mini."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return {
            "preguntas_frecuentes": "Configura OPENAI_API_KEY para activar el análisis IA.",
            "salas_populares": "Configura OPENAI_API_KEY para activar el análisis IA.",
            "sentimiento": "Configura OPENAI_API_KEY para activar el análisis IA.",
            "sugerencias": "Configura OPENAI_API_KEY para activar el análisis IA.",
        }

    # Get last 100 user messages
    messages = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .limit(100)
        .all()
    )

    if len(messages) < 3:
        return {
            "preguntas_frecuentes": "Aún no hay suficientes conversaciones para analizar. Se necesitan al menos 3 mensajes.",
            "salas_populares": "Aún no hay suficientes datos.",
            "sentimiento": "Aún no hay suficientes datos.",
            "sugerencias": "Aún no hay suficientes datos.",
        }

    msgs_text = "\n".join(
        [f"- {m.content}" for m in messages if m.content]
    )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de datos para Madness Light, empresa de fiestas light para jóvenes en Madrid. "
                    "Analiza los mensajes de usuarios del bot de Telegram y genera un informe conciso.\n\n"
                    "Responde SOLO con JSON válido (sin markdown, sin ```), con estas 4 claves:\n"
                    '- "preguntas_frecuentes": resumen de 2-4 líneas sobre qué preguntan más los usuarios (temas, dudas recurrentes)\n'
                    '- "salas_populares": qué salas o locales generan más interés según las conversaciones\n'
                    '- "sentimiento": análisis breve del tono general de los usuarios (entusiasmados, confundidos, etc.)\n'
                    '- "sugerencias": 2-3 sugerencias concretas para mejorar la comunicación del bot\n\n'
                    "Sé directo y conciso, máximo 3-4 líneas por sección. Escribe en español."
                ),
            },
            {
                "role": "user",
                "content": f"Estos son los últimos {len(messages)} mensajes de usuarios:\n\n{msgs_text}",
            },
        ],
        max_tokens=600,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON from markdown code blocks
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        return {
            "preguntas_frecuentes": raw[:200],
            "salas_populares": "Error al parsear respuesta de IA.",
            "sentimiento": "Error al parsear respuesta de IA.",
            "sugerencias": "Error al parsear respuesta de IA.",
        }
