# Por qué usamos Mistral OCR

| Aspecto                               | Mistral OCR                                                                                                                                                           | Métodos Tradicionales de OCR                                                                                                                                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Enfoque y Tecnología**              | Utiliza modelos de IA avanzados que no solo extraen el texto, sino que entienden la estructura completa del documento (imágenes, tablas, ecuaciones, etc.).           | Basados en técnicas clásicas de procesamiento de imágenes, se centran principalmente en extraer texto plano sin comprender la estructura.                                                                                  |
| **Precisión y Rendimiento**           | Precisión global de 94.89% (superior a Google Document AI y Azure OCR) y procesamiento de hasta 2,000 páginas por minuto.                                             | Precisión inferior en documentos con formatos complejos y velocidades menores, con necesidad de pasos adicionales de post-procesamiento.                                                                                   |
| **Soporte Multilingüe y Multimodal**  | Nativamente multilingüe y multimodal; puede procesar miles de idiomas y manejar imágenes integradas en los documentos.                                                | Soporte para varios idiomas, pero con limitaciones en la calidad del reconocimiento en alfabetos o scripts menos comunes; usualmente solo texto.                                                                           |
| **Integración, Flexibilidad y Costo** | Ofrece una API moderna, escalable e integrable en flujos de trabajo de IA (con opciones on-premise para datos sensibles) a un costo competitivo (1 USD/1000 páginas). | Suelen integrarse como bibliotecas (por ejemplo, Tesseract o ABBYY) que requieren adaptaciones adicionales para integrarse en aplicaciones modernas; algunas son gratuitas, pero con limitaciones en escenarios complejos. |
| **Casos de Uso**                      | Ideal para investigación, análisis de documentos complejos (científicos, legales, financieros) y digitalización de información en múltiples idiomas.                  | Adecuado para tareas simples de extracción de texto en documentos sin formato o estructura compleja.                                                                                                                       |

# Nuevo modelo de embedding

Ahora utilizamos el modelo **"gemini-embedding-exp-03-07"** debido a sus ventajas clave:

- **Mayor capacidad de contexto:** Soporta hasta **8K tokens**, permitiendo el procesamiento de grandes fragmentos de texto, código u otros datos.
- **Embeddings de alta dimensionalidad:** Ofrece **3K dimensiones**, casi 4 veces más que modelos anteriores.
- **Flexibilidad con MRL:** Permite truncar las dimensiones originales para ajustarse a los costos de almacenamiento deseados.
- **Soporte ampliado de idiomas:** Compatible con más de **100 idiomas**, duplicando la cobertura de modelos previos.
- **Modelo unificado:** Supera la calidad de modelos anteriores específicos para tareas multilingües, en inglés o código.
- **Rendimiento excepcional:** Funciona de manera generalizada en dominios como finanzas, ciencia, derecho y búsqueda, sin necesidad de ajustes extensos.

-- Insertar tabla comparativa
