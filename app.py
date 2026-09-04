"""Interfaz de chat (Streamlit) del asistente de soporte con RAG."""

import streamlit as st

from rag import construir_indice, responder

st.set_page_config(page_title="Soporte TechShop", page_icon="🛒", layout="centered")


@st.cache_resource(show_spinner="Preparando la base de conocimiento...")
def get_indice():
    # Se construye una sola vez por sesión (embeddings + índice vectorial).
    return construir_indice()


st.title("🛒 Asistente de soporte · TechShop")
st.caption(
    "Pregúntame sobre productos, envíos, devoluciones o pagos. "
    "Solo respondo con la información de la tienda, y te cito la fuente."
)

try:
    col = get_indice()
except Exception as e:
    st.error(f"No se pudo iniciar la aplicación: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Historial
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada del usuario
if pregunta := st.chat_input("¿En qué puedo ayudarte?"):
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en la tienda..."):
            try:
                respuesta, fuentes = responder(col, pregunta)
            except Exception as e:
                respuesta, fuentes = f"Ha ocurrido un error: {e}", []
        st.markdown(respuesta)
        if fuentes:
            st.caption("📎 Fuentes: " + ", ".join(fuentes))

    st.session_state.messages.append({"role": "assistant", "content": respuesta})
