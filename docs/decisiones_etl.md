# Decisiones ETL

Este documento registra las decisiones de limpieza, normalizacion e integracion
aplicadas durante el proyecto.

## Fase 3: Limpieza, normalizacion y ETL

### Alcance

- No se modificaron archivos en `data/raw/`.
- Los datasets normalizados se guardaron en `data/interim/`.
- La oferta academica consolidada se guardo en `data/processed/`.
- La columna `docente` se excluyo del archivo consolidado final de oferta.

### Normalizaciones aplicadas

- Se limpiaron espacios al inicio y al final de campos textuales.
- Se redujeron espacios repetidos dentro de texto.
- Se preservaron codigos de curso como texto para no perder ceros a la izquierda.
- Se normalizaron `periodo_academico`, `periodo_inscripcion` y `seccion` en mayusculas.
- Se agregaron columnas numericas auxiliares para notas y conteos cuando aplica.
- Se agregaron columnas auxiliares de fecha parseada cuando aplica.
- Se agregaron banderas `es_equivalencia`, `es_nsp` y `es_desasignado`.

### Consolidacion de oferta academica

- Filas originales de oferta: 205.
- Filas consolidadas de oferta: 200.
- Llaves duplicadas documentadas: 5.
- Llave de consolidacion: `periodo_academico + codigo_curso + seccion`.

Reglas aplicadas:

- `nombre_curso`: primer valor no vacio.
- `curso_aperturado` y `curso_cancelado`: `Si` si al menos un registro del grupo indica `Si`.
- `cupo_ofertado`, `estudiantes_asignados`, `estudiantes_con_nota`: maximo numerico del grupo.
- `jornada`, `horario`, `salon`, `modalidad`, `fuente_archivo`, `metodo_match`, `observaciones`: valores unicos concatenados con `; `.
- `fecha_inicio`: valor unico original si no hay conflicto; si hay multiples valores, fecha minima parseada.
- `fecha_fin`: valor unico original si no hay conflicto; si hay multiples valores, fecha maxima parseada.

### Archivos generados

| dataset | archivo_salida | filas_entrada | filas_salida | columnas_salida | observacion |
| --- | --- | --- | --- | --- | --- |
| catalogo_cursos | data/interim/01_catalogo_cursos_2024_normalizado.csv | 90 | 90 | 7 | Dataset normalizado sin eliminar registros. |
| actas_notas | data/interim/02_actas_notas_2024_detalle_normalizado.csv | 3468 | 3468 | 18 | Dataset normalizado sin eliminar registros. |
| asignaciones | data/interim/03_asignaciones_2024_normalizado.csv | 2879 | 2879 | 10 | Dataset normalizado sin eliminar registros. |
| oferta_academica | data/interim/04_oferta_academica_2024_normalizado.csv | 205 | 205 | 25 | Dataset normalizado sin eliminar registros. |
| malla_prerrequisitos | data/interim/05_malla_prerrequisitos_normalizado.csv | 136 | 136 | 8 | Dataset normalizado sin eliminar registros. |
| calendario_academico | data/interim/06_calendario_academico_2024_normalizado.csv | 4 | 4 | 18 | Dataset normalizado sin eliminar registros. |
| parametros_academicos | data/interim/07_parametros_academicos_normalizado.csv | 6 | 6 | 5 | Dataset normalizado sin eliminar registros. |
| configuracion_cursos | data/interim/08_configuracion_academica_cursos_normalizado.csv | 90 | 90 | 12 | Dataset normalizado sin eliminar registros. |
| estudiantes_inscritos | data/interim/09_estudiantes_inscritos_2024_normalizado.csv | 650 | 650 | 7 | Dataset normalizado sin eliminar registros. |
| inscritos_sistemas_anual | data/interim/10_inscritos_sistemas_anual_normalizado.csv | 3 | 3 | 7 | Dataset normalizado sin eliminar registros. |
| oferta_academica_consolidada | data/processed/04_oferta_academica_2024_consolidada.csv | 205 | 200 | 18 | Oferta consolidada sin columna docente. |

### Conclusion

La Fase 3 deja los datasets raw normalizados en `data/interim/` y una version
consolidada de oferta academica lista para construir datasets derivados. La
consolidacion resuelve duplicados de llave sin eliminar informacion de horarios
o trazabilidad de fuente.
