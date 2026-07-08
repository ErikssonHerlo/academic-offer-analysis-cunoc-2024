# Reglas de asociacion academicas

## Objetivo

Identificar coocurrencias frecuentes entre caracteristicas academicas
agregadas, resultados observados, recuperacion, continuidad y riesgo de retraso
academico potencial.

Las reglas de asociacion no demuestran causalidad. Una regla indica que un
conjunto de items aparece junto con otro con cierta frecuencia dentro de las
transacciones observadas.

## Parametros

- Transacciones analizadas: 2726
- Soporte minimo: 0.050
- Confianza minima: 0.600
- Lift minimo: 1.050
- Tamano maximo de itemset: 3

## Tablas generadas

| tabla | ruta |
| --- | --- |
| 08_itemsets_frecuentes | outputs/tables/association_rules/08_itemsets_frecuentes.csv |
| 08_reglas_asociacion | outputs/tables/association_rules/08_reglas_asociacion.csv |

## Itemsets frecuentes principales

| itemset | tamano_itemset | soporte | conteo |
| --- | --- | --- | --- |
| curso_obligatorio | 1 | 0.883 | 2408 |
| sin_riesgo_retraso | 1 | 0.849 | 2315 |
| sin_recuperacion | 1 | 0.788 | 2147 |
| no_requiere_laboratorio | 1 | 0.745 | 2032 |
| aprobo | 1 | 0.697 | 1899 |
| ocupacion_media | 1 | 0.663 | 1806 |
| area_ciencias_basicas_y_complementarias | 1 | 0.625 | 1703 |
| curso_base | 1 | 0.620 | 1690 |
| no_abierto_siguiente | 1 | 0.608 | 1657 |
| bloqueo_medio | 1 | 0.599 | 1633 |
| zona_media | 1 | 0.541 | 1474 |
| periodo_s1 | 1 | 0.456 | 1244 |
| abierto_siguiente | 1 | 0.392 | 1069 |
| periodo_s2 | 1 | 0.384 | 1047 |
| curso_no_base | 1 | 0.380 | 1036 |

## Reglas principales

| antecedente | consecuente | soporte | confianza | lift | leverage |
| --- | --- | --- | --- | --- | --- |
| area_ciencias_de_la_computacion | no_abierto_siguiente | 0.120 | 1.000 | 1.645 | 0.047 |
| area_ciencias_de_la_computacion + curso_obligatorio | no_abierto_siguiente | 0.120 | 1.000 | 1.645 | 0.047 |
| area_ciencias_de_la_computacion + ocupacion_media | no_abierto_siguiente | 0.100 | 1.000 | 1.645 | 0.039 |
| area_ciencias_de_la_computacion + sin_riesgo_retraso | no_abierto_siguiente | 0.089 | 1.000 | 1.645 | 0.035 |
| area_ciencias_de_la_computacion + sin_recuperacion | no_abierto_siguiente | 0.087 | 1.000 | 1.645 | 0.034 |
| aprobo + area_ciencias_de_la_computacion | no_abierto_siguiente | 0.083 | 1.000 | 1.645 | 0.033 |
| bloqueo_medio + semestre_2 | no_abierto_siguiente | 0.081 | 1.000 | 1.645 | 0.032 |
| area_ciencias_de_la_computacion + bloqueo_medio | no_abierto_siguiente | 0.081 | 1.000 | 1.645 | 0.032 |
| bloqueo_alto + requiere_laboratorio | no_abierto_siguiente | 0.077 | 1.000 | 1.645 | 0.030 |
| curso_no_base + semestre_2 | no_abierto_siguiente | 0.073 | 1.000 | 1.645 | 0.029 |
| area_ciencias_de_la_computacion + no_requiere_laboratorio | no_abierto_siguiente | 0.072 | 1.000 | 1.645 | 0.028 |
| area_desarrollo_de_software + requiere_laboratorio | no_abierto_siguiente | 0.072 | 1.000 | 1.645 | 0.028 |
| area_ciencias_de_la_computacion + curso_base | no_abierto_siguiente | 0.070 | 1.000 | 1.645 | 0.028 |
| bloqueo_bajo + ocupacion_media | no_abierto_siguiente | 0.069 | 1.000 | 1.645 | 0.027 |
| periodo_v2 | no_abierto_siguiente | 0.068 | 1.000 | 1.645 | 0.027 |

La regla con mayor prioridad segun lift, confianza y soporte es `area_ciencias_de_la_computacion` -> `no_abierto_siguiente` con lift 1.645.
Esta lectura debe usarse como patron de coocurrencia, no como explicacion causal.

## Limitaciones

- Las reglas dependen de la codificacion booleana del dataset derivado.
- Los items frecuentes pueden reflejar volumen de area, periodo o semestre, por
  lo que deben leerse junto con los indicadores de Fase 5.
- Un lift alto en una regla poco frecuente requiere cautela aunque cumpla el
  soporte minimo.
- No se exponen identificadores individuales ni se utiliza informacion docente.

## Conclusion

Las reglas de asociacion complementan el analisis al mostrar combinaciones de
condiciones que aparecen juntas en los registros modelables de 2024. Su valor
principal es exploratorio: orientar preguntas sobre perdida, recuperacion,
oferta posterior y riesgo potencial sin afirmar causalidad.
