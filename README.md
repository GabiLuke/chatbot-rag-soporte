# 🛒 Asistente de Soporte con RAG

Chatbot de soporte para una tienda online que responde **únicamente con la información de la tienda** (catálogo, FAQ y política de envíos/devoluciones), **cita la fuente** de cada respuesta y **no se inventa nada**: si la respuesta no está en los documentos, lo dice.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=flat&logo=googlegemini&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FCA121?style=flat)

> 🔗 **Demo en vivo:** **[chatbot-rag-soporte-gabiluke.streamlit.app](https://chatbot-rag-soporte-gabiluke.streamlit.app)**

---

## ✨ Qué hace

- Responde preguntas de clientes (productos, precios, envíos, devoluciones, pagos) **fundamentándose solo en los documentos de la tienda**.
- **Cita la fuente** de cada respuesta (`[faq]`, `[productos]`…).
- **Controla las alucinaciones**: ante preguntas fuera de tema, se niega a responder en vez de inventar.

## 🧠 Qué es RAG (y por qué importa)

RAG = *Retrieval-Augmented Generation*. En lugar de dejar que el modelo de lenguaje responda de memoria (y alucine), primero **recupera** los fragmentos relevantes de una base de conocimiento propia (mediante *embeddings* y una base de datos vectorial) y se los pasa como **contexto** al modelo. Así las respuestas son concretas, actualizables y trazables.

```
INGESTA (una vez):
  docs/ → trocear (chunking) → embeddings → índice vectorial (Chroma)

CONSULTA (cada pregunta):
  pregunta → embedding → búsqueda por similitud → fragmentos
          → prompt con contexto → LLM → respuesta + citas
```

## 🛠️ Stack

| Tema | Detalle |
|------|---------|
| Lenguaje | Python 3.10+ |
| Interfaz | Streamlit |
| Embeddings + generación | API de Google Gemini (`google-genai`) |
| Base vectorial | ChromaDB |

> El proyecto **selecciona el modelo de Gemini de forma dinámica** (consulta los disponibles en la cuenta), de modo que no se rompe si cambia el catálogo de modelos.

## 🗂️ Estructura

```
chatbot-rag-soporte/
├── app.py            # Interfaz de chat (Streamlit)
├── rag.py            # Ingesta, embeddings, recuperación y generación
├── evaluacion.py     # Métricas de recuperación y anti-alucinación
├── docs/             # Base de conocimiento de la tienda
│   ├── productos.md
│   ├── faq.md
│   └── envios_devoluciones.md
├── requirements.txt
└── .env.example
```

## 🚀 Puesta en marcha

```bash
git clone https://github.com/GabiLuke/chatbot-rag-soporte.git
cd chatbot-rag-soporte

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Copia `.env.example` como `.env` y añade tu clave de Gemini (gratis en
[aistudio.google.com/apikey](https://aistudio.google.com/apikey)):

```env
GEMINI_API_KEY=tu_clave
```

Ejecuta la app:
```bash
streamlit run app.py     # http://localhost:8501
```

## 📊 Evaluación

```bash
python evaluacion.py
```
Comprueba, sobre un conjunto de preguntas de prueba, el **% de recuperación correcta** (¿trae la fuente adecuada?) y el **% de alucinaciones evitadas** (¿se niega a responder lo que no sabe?).

**Resultados actuales:**

| Métrica | Resultado |
|---------|-----------|
| Recuperación correcta | **100%** (5/5) |
| Alucinaciones evitadas | **100%** (2/2) |

## 🎯 Qué demuestra este proyecto

- Implementación de **RAG de principio a fin**: chunking, embeddings, base vectorial, recuperación por similitud y generación fundamentada.
- **Control de alucinaciones** mediante un *system prompt* restrictivo y citación de fuentes.
- Buenas prácticas: gestión segura de la clave (variables de entorno), código organizado y **evaluación** del sistema.

---

## 👤 Autor

**Gabriel Luque Velasco** — Desarrollador Full-Stack Junior · Python & IA
[GitHub](https://github.com/GabiLuke) · gabiluke99@gmail.com
