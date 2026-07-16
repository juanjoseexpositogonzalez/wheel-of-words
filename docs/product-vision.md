# Visión de producto

## 1. Nombre provisional

**Wheel Vocabulary**

El nombre es provisional y no implica afiliación con el autor, editor o titulares de derechos de *The Wheel of Time*.

## 2. Problema

Las novelas extensas contienen vocabulario útil, pero convertirlo en material de estudio exige trabajo manual: extraer palabras, eliminar duplicados, agrupar formas flexionadas, identificar categorías, distinguir nombres propios, detectar phrasal verbs, priorizar vocabulario y crear tarjetas de Anki.

Las herramientas convencionales suelen producir listas superficiales de tokens y pierden el contexto lingüístico.

## 3. Visión

Construir una aplicación web local-first que transforme un libro aportado legalmente por el usuario en un corpus de vocabulario consultable, corregible y exportable a sistemas de repetición espaciada.

## 4. Usuario principal

Persona adulta que lee literatura en inglés, desea ampliar vocabulario, usa o puede usar Anki, valora la precisión lingüística y quiere conservar el control sobre sus archivos.

## 5. Propuesta de valor

Wheel Vocabulary permitirá:

1. Importar una obra.
2. Extraer formas, lemas y frecuencias.
3. Consultar usos gramaticales.
4. Separar vocabulario general de nombres propios.
5. Revisar resultados automáticos.
6. Marcar el estado de aprendizaje.
7. Exportar selecciones a Anki.

## 6. Principios de producto

### Local-first

El texto se procesa localmente por defecto.

### Transparencia lingüística

El usuario puede ver y corregir clasificaciones.

### Datos preservables

Las correcciones y estados de aprendizaje deben poder exportarse y respaldarse.

### Progresión incremental

La aplicación debe ser útil desde versiones tempranas.

### Reutilización

El sistema no se limitará a un libro; el primero será un corpus inicial.

## 7. Objetivos del MVP

- Crear un proyecto local.
- Importar TXT y EPUB.
- Extraer palabras y frecuencias.
- Normalizar formas.
- Agrupar por lema.
- Etiquetar categorías gramaticales.
- Separar nombres propios.
- Buscar y filtrar vocabulario.
- Marcar palabras conocidas, desconocidas o ignoradas.
- Seleccionar vocabulario.
- Exportar CSV/TSV compatible con Anki.
- Exportar `.apkg` en una fase posterior si la estabilidad lo permite.

## 8. Fuera de alcance inicial

- Aplicación móvil nativa.
- Sincronización multiusuario.
- Marketplace de libros.
- Distribución de obras protegidas.
- Traducción automática masiva de pago.
- Entrenamiento de modelos NLP propios.
- Análisis semántico perfecto.
- Colaboración social.
- Gamificación compleja.

## 9. Métricas de éxito

### Producto

- Importar un archivo válido sin editarlo manualmente.
- Encontrar un lema rápidamente.
- Corregir una clasificación sin perderla al reprocesar.
- Exportar una selección utilizable en Anki.

### Calidad

- Operaciones críticas cubiertas por pruebas.
- Análisis reproducible.
- Errores sin corrupción de datos.
- Correcciones manuales preservadas.

### Usabilidad

- Flujo básico sin documentación externa.
- Interfaz utilizable con teclado.
- Estados de procesamiento visibles.

## 10. Escenario principal

1. El usuario importa un EPUB.
2. La aplicación procesa capítulos.
3. El usuario filtra palabras de frecuencia media.
4. Excluye nombres propios.
5. Marca las conocidas.
6. Revisa phrasal verbs.
7. Exporta las desconocidas a Anki.

## 11. Riesgos y mitigaciones

### Riesgo lingüístico

Los modelos pueden equivocarse con prosa literaria.

**Mitigación:** confianza, revisión manual y fixtures de regresión.

### Riesgo legal

El producto podría confundirse con una fuente de distribución.

**Mitigación:** no incorporar libros, procesamiento local y textos sintéticos en pruebas.

### Riesgo de rendimiento

Un libro completo puede requerir procesamiento prolongado.

**Mitigación:** estados de trabajo, progreso, lotes e idempotencia.

### Riesgo de alcance

Añadir demasiadas funciones pronto puede retrasar el núcleo.

**Mitigación:** cortes verticales y roadmap explícito.

## 12. Roadmap

1. Fundación técnica.
2. Importación TXT.
3. Tokenización y normalización.
4. Lematización y POS.
5. Navegador de vocabulario.
6. Nombres propios y términos ficticios.
7. Phrasal verbs.
8. Estado de aprendizaje.
9. Exportación Anki.
10. EPUB y rendimiento.
