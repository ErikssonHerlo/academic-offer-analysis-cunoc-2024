# Datasets derivados

## Objetivo

Construir las unidades analiticas principales para indicadores, continuidad,
modelos, clustering y reglas de asociacion.

## Archivos generados

| dataset | archivo | filas | columnas | conclusion |
| --- | --- | --- | --- | --- |
| ds_estudiante_curso_resultado_2024 | data/processed/ds_estudiante_curso_resultado_2024.csv | 2879 | 58 | Unidad estudiante-curso-periodo construida desde asignaciones y actas. |
| ds_resumen_curso_periodo_2024 | data/processed/ds_resumen_curso_periodo_2024.csv | 132 | 42 | Unidad curso-periodo lista para indicadores y regresion agregada. |
| ds_continuidad_oferta_2024 | data/processed/ds_continuidad_oferta_2024.csv | 90 | 24 | Unidad curso anual lista para analizar continuidad de oferta. |
| ds_cursos_criticos_clustering | data/processed/ds_cursos_criticos_clustering.csv | 90 | 15 | Dataset numerico y contextual preparado para clustering. |
| ds_modelo_clasificacion | data/processed/ds_modelo_clasificacion.csv | 2726 | 21 | Dataset de modelado sin desasignados ni variables prohibidas por fuga. |
| ds_reglas_asociacion | data/processed/ds_reglas_asociacion.csv | 2726 | 44 | Matriz transaccional codificada para reglas de asociacion. |

## Distribucion de targets de modelado

| target | valor | conteo | porcentaje |
| --- | --- | --- | --- |
| necesito_recuperacion | False | 2147 | 78.76 |
| necesito_recuperacion | True | 579 | 21.24 |
| perdida_definitiva | False | 1899 | 69.66 |
| perdida_definitiva | True | 827 | 30.34 |
| riesgo_retraso_potencial | False | 2315 | 84.92 |
| riesgo_retraso_potencial | True | 411 | 15.08 |
| riesgo_retraso_potencial_amplio | False | 2207 | 80.96 |
| riesgo_retraso_potencial_amplio | True | 519 | 19.04 |

## Definicion e interpretacion de targets

Los targets se derivan de registros academicos observados en actas y de la
continuidad de oferta disponible para 2024. No deben interpretarse como causas,
sino como etiquetas operativas para describir resultados y riesgos potenciales
bajo los datos registrados.

| target | valor verdadero cuando | interpretacion | advertencia metodologica |
| --- | --- | --- | --- |
| `necesito_recuperacion` | El estudiante tiene registro de primera o segunda recuperacion para el curso. | El curso no fue aprobado directamente en ordinario y requirio una oportunidad posterior registrada. | No mide por si solo si la recuperacion fue aprobada o perdida; para eso se usa `aprobo_por_recuperacion` o `perdida_definitiva`. |
| `perdida_definitiva` | El ultimo resultado observable del curso no fue aprobado. La ultima oportunidad se toma en este orden de prioridad: equivalencia, segunda recuperacion, primera recuperacion u ordinario. | Representa que, con las oportunidades registradas en acta, el estudiante no cerro el curso como aprobado. Puede incluir perdida en ordinario sin recuperacion registrada, perdida despues de recuperacion o un ultimo resultado especial no aprobado como `NSP`. | No significa necesariamente que el estudiante no tuvo acceso a recuperacion. Indica el resultado final observado en los datos disponibles. Para separar sensibilidad por inasistencia existe `perdida_definitiva_sin_nsp` en el dataset maestro. |
| `riesgo_retraso_potencial` | Existe `perdida_definitiva`, el curso no se oferta en el periodo inmediato posterior y el curso cumple condicion bloqueante curricular. | Identifica casos donde la perdida de un curso bloqueante coincide con ausencia de oferta inmediata posterior, lo que puede generar retraso academico potencial. | Es un indicador potencial, no una prueba causal ni una medicion individual definitiva de retraso. |
| `riesgo_retraso_potencial_amplio` | Existe `perdida_definitiva` y el curso no se oferta en el periodo inmediato posterior, sin exigir condicion bloqueante. | Version mas amplia del riesgo, util para sensibilidad y comparacion con el target curricular estricto. | Puede incluir cursos con menor impacto curricular directo; por eso se reporta separado del target principal. |

## Tratamiento de desasignados

Los registros con `estado_asignacion=desasignado` se conservan en
`ds_estudiante_curso_resultado_2024.csv` porque forman parte de la trazabilidad
de asignaciones y permiten comparar asignacion inicial contra participacion
evaluada. Sin embargo, se excluyen de `ds_modelo_clasificacion.csv` porque no
representan un resultado academico evaluado comparable en acta.

Incluir desasignados en modelos de perdida, recuperacion o riesgo potencial
mezclaria procesos administrativos previos al cierre del curso con resultados
academicos observados. Tambien obligaria a asignar etiquetas no observadas a
casos que no completaron la trayectoria evaluable del curso.

## Decisiones metodologicas

- `ds_estudiante_curso_resultado_2024.csv` parte de asignaciones para conservar desasignados y cruza resultados de actas cuando existen.
- Los registros desasignados se conservan en el dataset maestro, pero se excluyen de `ds_modelo_clasificacion.csv`.
- `resultado_final` se toma de la ultima oportunidad registrada bajo prioridad academica: equivalencia, segunda recuperacion, primera recuperacion u ordinario.
- `perdida_definitiva` indica que el ultimo resultado observable no fue aprobado; no distingue por si sola entre ausencia de recuperacion registrada y perdida posterior a recuperacion.
- `riesgo_retraso_potencial` requiere perdida definitiva, ausencia de oferta inmediata posterior y condicion bloqueante del curso.
- `riesgo_retraso_potencial_amplio` requiere perdida definitiva y ausencia de oferta inmediata posterior.
- Los datasets de modelado no incluyen `docente`, `nota_examen_ordinario`, `nota_total_ordinario`, `nota_total_final` ni `resultado_final` como predictores.

## Conclusion

La Fase 4 deja construidos los datasets derivados necesarios para iniciar EDA,
indicadores, inferencia y modelos. Los targets presentan distribuciones
verificables y se separa el dataset maestro del dataset de modelado para evitar
mezclar desasignados o variables con fuga de informacion.
