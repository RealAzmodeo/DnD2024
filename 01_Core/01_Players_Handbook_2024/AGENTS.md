# Directrices para Agentes: Edición de Archivos XML de Hechizos (PHB 2024)

Este documento proporciona directrices para trabajar con los archivos XML de hechizos ubicados en esta carpeta, generados a partir de `spells-phb24.xml` y parseados por `parse_spells.py`. El objetivo es mantener la consistencia y asegurar que los datos sean utilizables.

## Principios Generales

1.  **Consultar `glossary_xml_tags_v1.txt`**: Este es el documento maestro para la estructura XML. Cualquier nueva etiqueta o cambio estructural mayor debe reflejarse allí.
2.  **Consistencia**: Aplicar las etiquetas de manera uniforme en todos los hechizos.
3.  **Script `parse_spells.py`**: Este script maneja la división inicial y el parseo. Si se realizan cambios manuales significativos que el script no puede replicar, considerar actualizar el script o documentar claramente la desviación.

## Estructura XML Clave para Hechizos (`<spell>`)

Recordar la estructura definida en el paso de diseño del plan y detallada en `glossary_xml_tags_v1.txt`. A continuación, algunos puntos clave a observar:

*   **`<school code="[ABREVIATURA]">[Nombre Completo]</school>`**: Usar las abreviaturas estándar (A, C, D, EN, EV, I, N, T) y el nombre completo correspondiente.
*   **`<ritual available="[true|false]"/>`**
*   **`<casting_time description="[Original]">`**:
    *   `<value>`, `<unit>`, `<condition text="..."/>` (para reacciones/bonus actions con triggers).
*   **`<range description="[Original]">`**:
    *   `<value>`, `<unit>`, `<shape>`, `<shape_value>`.
*   **`<components>`**:
    *   `<verbal/>`, `<somatic/>` (etiquetas vacías si están presentes).
    *   `<material consumed="[true|false]" cost_gp="[numero]" cost_text="[texto_costo_descriptivo]">[descripción_limpia_material]</material>`
        *   `cost_gp`: Solo el número (ej., "1500" para "1,500 GP").
        *   `cost_text`: Para frases como "worth X GP" o "X+ GP".
        *   Texto del tag: Descripción del material idealmente sin la información de costo ya capturada.
*   **`<duration description="[Original]">`**:
    *   `<value>`, `<unit>`.
    *   `<concentration available="[true|false]" up_to="[true|false]"/>`.
*   **`<description>`**:
    *   Usar `<p>` para párrafos.
    *   Usar `<list><item>...</item></list>` para listas con viñetas o numeradas.
    *   Usar `<table>` para tablas estructuradas.
*   **`<classes text_original="[Original]">`**:
    *   `<class_name>...</class_name>`
    *   `<subclass_restriction for_class="..." name="..."/>`
*   **`<source name="..." page="..."/>`**
*   **`<roll description="..." type="...">`**:
    *   `<dice>...</dice>`, `<damage_type>...</damage_type>`, `<bonus_from_ability>...</bonus_from_ability>`.
*   **`<at_higher_levels>`**:
    *   Para **Cantrips**: Usar múltiples `<scaling level="X"><effect description="YdZ"/></scaling>`. Evitar el `text_block` si todos los niveles están parseados.
    *   Para **Hechizos con Nivel**:
        *   `<per_slot_above base_level="L"><effect description="Texto completo del efecto de escalado"><roll_increase increase_dice="XdY"/> o <additional_targets count="N"/> etc.</effect></per_slot_above>`
        *   `<specific_slot level="L"><effect description="Texto completo del efecto a este nivel específico."/></specific_slot>`
        *   Usar `text_block title="General Higher Level Effects"` como último recurso si la estructura no encaja en los anteriores.

## Notas sobre el Parseo (Script `parse_spells.py`)

*   **Componentes Materiales**: El script intenta extraer `cost_gp` y `cost_text` y limpiar la descripción. Revisar que la descripción resultante sea natural. Casos como "a X worth Y GP item" donde Y es el costo, la descripción debería ser "a X item".
*   **"A Niveles Superiores"**: El script intenta parsear los patrones comunes.
    *   La descripción en `<effect>` dentro de `<per_slot_above>` debe ser lo más completa posible.
    *   Verificar que no queden `text_block` incorrectos o redundantes si la información ya está estructurada.
*   **Múltiples `<roll>`**: El script actualmente mantiene todos los `<roll>` del archivo XML original. Esto es para preservar la información, ya que el original no siempre distingue claramente el "roll base" de los rolls de niveles superiores. La sección `<at_higher_levels>` es la que debe usarse para interpretar el escalado.

## Futuras Modificaciones

*   Si se añaden nuevos hechizos manualmente o se editan existentes, seguir esta estructura.
*   Si se encuentran patrones de texto recurrentes no manejados adecuadamente por el script, considerar actualizar `parse_spells.py` para mejorar la automatización y consistencia.

Al seguir estas directrices, se facilitará el mantenimiento y la utilidad de los datos de hechizos.
