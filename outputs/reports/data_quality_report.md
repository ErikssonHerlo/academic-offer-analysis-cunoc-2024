# Reporte de calidad de datos

## Objetivo

Validar la existencia, estructura y consistencia inicial de los diez datasets raw antes del ETL.

## Resumen de carga

| dataset | archivo | filas | columnas |
| --- | --- | --- | --- |
| catalogo_cursos | 01_catalogo_cursos_2024.csv | 90 | 7 |
| actas_notas | 02_actas_notas_2024_detalle.csv | 3468 | 12 |
| asignaciones | 03_asignaciones_2024.csv | 2879 | 7 |
| oferta_academica | 04_oferta_academica_2024.csv | 205 | 19 |
| malla_prerrequisitos | 05_malla_prerrequisitos.csv | 136 | 8 |
| calendario_academico | 06_calendario_academico_2024.csv | 4 | 8 |
| parametros_academicos | 07_parametros_academicos.csv | 6 | 5 |
| configuracion_cursos | 08_configuracion_academica_cursos.csv | 90 | 12 |
| estudiantes_inscritos | 09_estudiantes_inscritos_2024.csv | 650 | 7 |
| inscritos_sistemas_anual | 10_inscritos_sistemas_anual.csv | 3 | 7 |

## Validacion de esquema

| dataset | existe_archivo | columnas_esperadas | columnas_encontradas | estado |
| --- | --- | --- | --- | --- |
| catalogo_cursos | True | 7 | 7 | ok |
| actas_notas | True | 12 | 12 | ok |
| asignaciones | True | 7 | 7 | ok |
| oferta_academica | True | 19 | 19 | ok |
| malla_prerrequisitos | True | 8 | 8 | ok |
| calendario_academico | True | 8 | 8 | ok |
| parametros_academicos | True | 5 | 5 | ok |
| configuracion_cursos | True | 12 | 12 | ok |
| estudiantes_inscritos | True | 7 | 7 | ok |
| inscritos_sistemas_anual | True | 7 | 7 | ok |

## Resumen de hallazgos

- Criticos: 0
- Altos: 1
- Medios: 2
- Informativos: 3

## Hallazgos de calidad de datos

| severidad | dataset | regla | columna | hallazgo | cantidad | detalle |
| --- | --- | --- | --- | --- | --- | --- |
| alto | oferta_academica | duplicados_llave | periodo_academico + codigo_curso + seccion | Existen registros con llave principal duplicada. | 10 |  |

## Decisiones de limpieza aplicadas

No se aplicaron transformaciones ni eliminaciones de registros en esta fase.
Los archivos raw se leyeron en modo texto para preservar codigos con ceros a la izquierda.
Los valores especiales `EQ`, `NSP` y `desasignado` se reportan y se conservaran para el ETL.

## Conclusion

Los datasets cargan correctamente, pero existen hallazgos altos que deben revisarse antes de construir datasets derivados.
