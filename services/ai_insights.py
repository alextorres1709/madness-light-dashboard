import json
import os
import time
from openai import OpenAI
from sqlalchemy import or_
from models import db, Conversation

# In-memory caches
_cache = {"data": None, "expires": 0}
_rrpp_cache = {"data": None, "expires": 0}
_topics_cache = {"data": None, "expires": 0}

CACHE_TTL = 3600       # 1 hour
RRPP_CACHE_TTL = 7200  # 2 hours

RRPP_KEYWORDS = [
    'rrpp', 'promotor', 'promotora', 'comision', 'comisiones',
    'ganar dinero', 'equipo', 'reclutar', 'relaciones publicas',
    'codigo', 'enlace', 'rangos', 'puntos', 'ser rrpp',
    'quiero ser', 'trabajar', 'sueldo', 'beneficios'
]


def _parse_json_response(raw):
    """Parse JSON from GPT response, handling markdown code blocks."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        return None


def _get_client():
    """Return OpenAI client if API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


# ──────────────────────────────────────
# General Insights (existing)
# ──────────────────────────────────────

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
    client = _get_client()
    no_key = "Configura OPENAI_API_KEY para activar el análisis IA."
    if not client:
        return {k: no_key for k in ["preguntas_frecuentes", "salas_populares", "sentimiento", "sugerencias"]}

    messages = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .limit(100)
        .all()
    )

    if len(messages) < 3:
        no_data = "Aún no hay suficientes datos."
        return {
            "preguntas_frecuentes": "Aún no hay suficientes conversaciones para analizar.",
            "salas_populares": no_data, "sentimiento": no_data, "sugerencias": no_data,
        }

    msgs_text = "\n".join([f"- {m.content}" for m in messages if m.content])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de datos para Madness Light, empresa de fiestas light para jóvenes en Madrid. "
                    "Analiza los mensajes de usuarios del bot de Telegram y genera un informe conciso.\n\n"
                    "Responde SOLO con JSON válido (sin markdown, sin ```), con estas 4 claves:\n"
                    '- "preguntas_frecuentes": resumen de 2-4 líneas sobre qué preguntan más los usuarios\n'
                    '- "salas_populares": qué salas o locales generan más interés\n'
                    '- "sentimiento": análisis breve del tono general de los usuarios\n'
                    '- "sugerencias": 2-3 sugerencias concretas para mejorar la comunicación del bot\n\n'
                    "Sé directo y conciso, máximo 3-4 líneas por sección. Escribe en español."
                ),
            },
            {"role": "user", "content": f"Últimos {len(messages)} mensajes:\n\n{msgs_text}"},
        ],
        max_tokens=600,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    parsed = _parse_json_response(raw)
    if parsed:
        return parsed
    return {
        "preguntas_frecuentes": raw[:200],
        "salas_populares": "Error al parsear respuesta de IA.",
        "sentimiento": "Error al parsear respuesta de IA.",
        "sugerencias": "Error al parsear respuesta de IA.",
    }


# ──────────────────────────────────────
# RRPP Analysis
# ──────────────────────────────────────

def get_rrpp_insights():
    """Return RRPP-focused AI insights, cached for 2 hours."""
    now = time.time()
    if _rrpp_cache["data"] and now < _rrpp_cache["expires"]:
        return _rrpp_cache["data"]

    data = _generate_rrpp_insights()
    _rrpp_cache["data"] = data
    _rrpp_cache["expires"] = now + RRPP_CACHE_TTL
    return data


def _generate_rrpp_insights():
    """Analyze RRPP-related conversations for doubts and objections."""
    client = _get_client()
    no_key = "Configura OPENAI_API_KEY para activar el análisis RRPP."
    if not client:
        return {k: no_key for k in [
            "dudas_principales", "objeciones", "preguntas_comisiones",
            "nivel_interes", "sugerencias_conversion"
        ]}

    keyword_filters = [Conversation.content.ilike(f'%{kw}%') for kw in RRPP_KEYWORDS]
    messages = (
        Conversation.query
        .filter_by(role="user")
        .filter(or_(*keyword_filters))
        .order_by(Conversation.created_at.desc())
        .limit(150)
        .all()
    )

    if len(messages) < 3:
        no_data = "No hay suficientes conversaciones sobre RRPP para analizar."
        return {k: no_data for k in [
            "dudas_principales", "objeciones", "preguntas_comisiones",
            "nivel_interes", "sugerencias_conversion"
        ]}

    msgs_text = "\n".join([f"- {m.content}" for m in messages if m.content])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista especializado en programas de RRPP (promotores) para Madness Light, "
                    "empresa de fiestas light para jóvenes en Madrid. Los RRPP venden entradas con un código personal "
                    "y pueden reclutar sub-promotores cuyas ventas también les cuentan.\n\n"
                    "Analiza estos mensajes de usuarios interesados en ser RRPP y responde SOLO con JSON válido "
                    "(sin markdown, sin ```), con estas 5 claves:\n"
                    '- "dudas_principales": las 3-5 dudas o preguntas más frecuentes de potenciales RRPPs\n'
                    '- "objeciones": razones o miedos por los que la gente decide NO hacerse RRPP '
                    '(ej: parece estafa, no tengo tiempo, no quiero vender, etc.)\n'
                    '- "preguntas_comisiones": dudas específicas sobre dinero, comisiones, puntos y ganancias\n'
                    '- "nivel_interes": evaluación general del interés (alto/medio/bajo) con breve explicación\n'
                    '- "sugerencias_conversion": 2-3 acciones concretas para que más gente se anime a ser RRPP\n\n'
                    "Sé directo y específico. Máximo 3-4 líneas por sección. Escribe en español."
                ),
            },
            {"role": "user", "content": f"Mensajes relacionados con RRPP ({len(messages)} mensajes):\n\n{msgs_text}"},
        ],
        max_tokens=800,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    parsed = _parse_json_response(raw)
    if parsed:
        return parsed
    return {
        "dudas_principales": raw[:200],
        "objeciones": "Error al parsear respuesta de IA.",
        "preguntas_comisiones": "Error al parsear respuesta de IA.",
        "nivel_interes": "Error al parsear respuesta de IA.",
        "sugerencias_conversion": "Error al parsear respuesta de IA.",
    }


# ──────────────────────────────────────
# Topic Distribution
# ──────────────────────────────────────

def get_topic_distribution():
    """Return AI-categorized topic breakdown, cached for 1 hour."""
    now = time.time()
    if _topics_cache["data"] and now < _topics_cache["expires"]:
        return _topics_cache["data"]

    data = _generate_topic_distribution()
    _topics_cache["data"] = data
    _topics_cache["expires"] = now + CACHE_TTL
    return data


def _generate_topic_distribution():
    """Classify recent conversations into topic categories."""
    client = _get_client()
    if not client:
        return {"topics": []}

    messages = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .limit(200)
        .all()
    )

    if len(messages) < 5:
        return {"topics": []}

    msgs_text = "\n".join([f"- {m.content}" for m in messages if m.content])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de datos para Madness Light (fiestas light para jóvenes en Madrid). "
                    "Clasifica los mensajes de usuarios del bot por tema y devuelve los porcentajes.\n\n"
                    "Responde SOLO con JSON válido (sin markdown, sin ```), con esta estructura:\n"
                    '{"topics": [\n'
                    '  {"name": "Eventos y Fiestas", "percentage": 45},\n'
                    '  {"name": "RRPP y Promotores", "percentage": 20},\n'
                    '  {"name": "Entradas y Precios", "percentage": 15},\n'
                    '  {"name": "Salas y Ubicacion", "percentage": 10},\n'
                    '  {"name": "Otros", "percentage": 10}\n'
                    ']}\n\n'
                    "Usa exactamente esas 5 categorías. Los porcentajes deben sumar 100. "
                    "Basa los porcentajes en el contenido real de los mensajes."
                ),
            },
            {"role": "user", "content": f"Clasifica estos {len(messages)} mensajes:\n\n{msgs_text}"},
        ],
        max_tokens=300,
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    parsed = _parse_json_response(raw)
    if parsed and "topics" in parsed:
        return parsed
    return {"topics": []}
