"""
Evaluación del RAG. Mide dos cosas:
  1. Recuperación: ¿trae la fuente correcta para cada pregunta?
  2. Anti-alucinación: ante preguntas fuera de tema, ¿dice "no tengo esa información"?

Ejecuta:  python evaluacion.py
"""

from rag import construir_indice, recuperar, responder

# Preguntas que SÍ están en los documentos (con la fuente que se espera)
PRUEBAS = [
    {"pregunta": "¿Cuánto tarda el envío?", "fuente": "envios_devoluciones"},
    {"pregunta": "¿Tenéis SSD de 1 TB y a qué precio?", "fuente": "productos"},
    {"pregunta": "¿Puedo pagar contra reembolso?", "fuente": "faq"},
    {"pregunta": "¿Cuál es el plazo de devolución?", "fuente": "envios_devoluciones"},
    {"pregunta": "¿Qué métodos de pago aceptáis?", "fuente": "faq"},
]

# Preguntas que NO están: el bot debe negarse a responder
FUERA_DE_TEMA = [
    "¿Cuál es la capital de Francia?",
    "Recomiéndame una receta de tortilla de patatas.",
]


def main():
    col = construir_indice()

    print("\n== Recuperación ==")
    aciertos = 0
    for p in PRUEBAS:
        _, fuentes = recuperar(col, p["pregunta"])
        ok = p["fuente"] in fuentes
        aciertos += ok
        print(f"[{'OK ' if ok else ' X '}] {p['pregunta']}  ->  {fuentes}")

    print("\n== Anti-alucinación (preguntas fuera de tema) ==")
    evitadas = 0
    for q in FUERA_DE_TEMA:
        respuesta, _ = responder(col, q)
        evitada = "no tengo esa información" in respuesta.lower()
        evitadas += evitada
        print(f"[{'OK ' if evitada else ' X '}] {q}  ->  {respuesta[:60]}...")

    print("\n" + "=" * 55)
    print(f"Recuperación correcta:   {aciertos}/{len(PRUEBAS)} "
          f"({aciertos / len(PRUEBAS) * 100:.0f}%)")
    print(f"Alucinaciones evitadas:  {evitadas}/{len(FUERA_DE_TEMA)} "
          f"({evitadas / len(FUERA_DE_TEMA) * 100:.0f}%)")


if __name__ == "__main__":
    main()
