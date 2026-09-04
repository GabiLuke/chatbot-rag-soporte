"""
Núcleo RAG del asistente de soporte.

Flujo:
  docs/ -> trocear (chunking) -> embeddings -> índice vectorial (Chroma)
  pregunta -> embedding -> búsqueda por similitud -> fragmentos -> LLM -> respuesta + citas

Los modelos de Gemini se eligen de forma dinámica (consultando los disponibles
en tu cuenta), para que el proyecto no se rompa si cambia el catálogo.
"""

import glob
import os
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai

load_dotenv()

DOCS_DIR = Path(__file__).parent / "docs"

SYSTEM = """Eres el asistente de soporte de la tienda online TechShop.
Responde ÚNICAMENTE con la información del CONTEXTO que se te proporciona más abajo.

Reglas:
- Si la respuesta NO está en el contexto, responde exactamente:
  "No tengo esa información. Puedes escribir a soporte@techshop.com y te ayudarán."
  No te inventes datos ni uses conocimiento externo.
- Al final de tu respuesta, cita la fuente o fuentes entre corchetes (p. ej.: [faq], [productos]).
- Sé claro, breve y amable, y responde en el mismo idioma en que te escriba el cliente."""


# --------------------------------------------------------------------------
# Cliente de Gemini (lee la clave de Streamlit secrets o del archivo .env)
# --------------------------------------------------------------------------
def _clave_api():
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


_cliente = None


def cliente():
    global _cliente
    if _cliente is None:
        clave = _clave_api()
        if not clave:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Ponla en el archivo .env "
                "(o en los Secrets de Streamlit Cloud)."
            )
        _cliente = genai.Client(api_key=clave)
    return _cliente


# --------------------------------------------------------------------------
# Reintentos ante errores transitorios de la API (503 saturación, 429 cuota…)
# --------------------------------------------------------------------------
_TRANSITORIOS = ("503", "unavailable", "429", "resource_exhausted", "overloaded",
                 "deadline", "timeout", "internal")


def es_error_transitorio(e):
    return any(t in str(e).lower() for t in _TRANSITORIOS)


def _con_reintentos(fn, intentos=4, espera_base=1.0):
    ultimo = None
    for intento in range(intentos):
        try:
            return fn()
        except Exception as e:
            ultimo = e
            if intento < intentos - 1 and es_error_transitorio(e):
                time.sleep(espera_base * (2 ** intento))  # 1s, 2s, 4s…
                continue
            raise
    raise ultimo


# --------------------------------------------------------------------------
# Selección dinámica de modelos válidos para la cuenta
# --------------------------------------------------------------------------
_cache_modelos = {}


def _elegir_modelo(accion, preferencias):
    if accion in _cache_modelos:
        return _cache_modelos[accion]
    disponibles = []
    try:
        for m in cliente().models.list():
            if m.supported_actions and accion in m.supported_actions:
                disponibles.append(m.name.replace("models/", ""))
    except Exception:
        disponibles = []
    elegido = None
    for pref in preferencias:
        candidatos = sorted((n for n in disponibles if pref in n), reverse=True)
        if candidatos:
            elegido = candidatos[0]
            break
    if not elegido and disponibles:
        elegido = disponibles[0]
    _cache_modelos[accion] = elegido
    return elegido


def modelo_generacion():
    return _elegir_modelo(
        "generateContent",
        ["gemini-flash-lite-latest", "gemini-flash-latest", "flash-lite", "flash"],
    )


def modelo_embeddings():
    return _elegir_modelo(
        "embedContent",
        ["gemini-embedding", "text-embedding", "embedding"],
    )


# --------------------------------------------------------------------------
# 1) Ingesta y troceado (chunking)
# --------------------------------------------------------------------------
def cargar_y_trocear(carpeta=DOCS_DIR, tam=600, solape=100):
    """Lee los .md de la carpeta y los parte en fragmentos con solapamiento."""
    trozos = []
    for ruta in sorted(glob.glob(str(Path(carpeta) / "*.md"))):
        fuente = Path(ruta).stem  # nombre del archivo sin extensión
        texto = Path(ruta).read_text(encoding="utf-8")
        i = 0
        while i < len(texto):
            fragmento = texto[i:i + tam].strip()
            if fragmento:
                trozos.append({"texto": fragmento, "fuente": fuente})
            i += tam - solape
    return trozos


# --------------------------------------------------------------------------
# 2) Embeddings + índice vectorial (Chroma)
# --------------------------------------------------------------------------
def _embed(texto):
    r = _con_reintentos(
        lambda: cliente().models.embed_content(model=modelo_embeddings(), contents=texto)
    )
    return r.embeddings[0].values


def construir_indice(trozos=None):
    """Crea el índice vectorial en memoria a partir de los fragmentos."""
    if trozos is None:
        trozos = cargar_y_trocear()
    chroma = chromadb.Client()
    try:
        chroma.delete_collection("soporte")  # empezar limpio si ya existía
    except Exception:
        pass
    col = chroma.create_collection("soporte")
    col.add(
        ids=[str(i) for i in range(len(trozos))],
        embeddings=[_embed(t["texto"]) for t in trozos],
        documents=[t["texto"] for t in trozos],
        metadatas=[{"fuente": t["fuente"]} for t in trozos],
    )
    return col


# --------------------------------------------------------------------------
# 3) Recuperación
# --------------------------------------------------------------------------
def recuperar(col, pregunta, k=4):
    """Devuelve los k fragmentos más parecidos a la pregunta y sus fuentes."""
    res = col.query(query_embeddings=[_embed(pregunta)], n_results=k)
    docs = res["documents"][0]
    fuentes = [m["fuente"] for m in res["metadatas"][0]]
    return docs, fuentes


# --------------------------------------------------------------------------
# 4) Generación con contexto (fundamentada)
# --------------------------------------------------------------------------
def responder(col, pregunta, k=4):
    docs, fuentes = recuperar(col, pregunta, k)
    contexto = "\n\n".join(f"[{f}] {d}" for d, f in zip(docs, fuentes))
    prompt = f"{SYSTEM}\n\nCONTEXTO:\n{contexto}\n\nPREGUNTA DEL CLIENTE: {pregunta}"
    r = _con_reintentos(
        lambda: cliente().models.generate_content(model=modelo_generacion(), contents=prompt)
    )
    return r.text, sorted(set(fuentes))
