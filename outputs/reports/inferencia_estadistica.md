# Inferencia estadistica

## Objetivo

Evaluar asociaciones observadas entre area academica, continuidad de oferta,
perdida definitiva, recursamiento observable y riesgo de retraso academico
potencial.

Las pruebas de esta fase no demuestran causalidad. Su funcion es aportar
evidencia estadistica sobre patrones observados en los datasets procesados y
orientar las fases posteriores de modelado y sintesis.

## Tablas generadas

| tabla | ruta |
| --- | --- |
| 06_chi_square_tests | outputs/tables/statistical_tests/06_chi_square_tests.csv |
| 06_confidence_intervals | outputs/tables/statistical_tests/06_confidence_intervals.csv |
| 06_nonparametric_tests | outputs/tables/statistical_tests/06_nonparametric_tests.csv |
| 06_proportion_tests | outputs/tables/statistical_tests/06_proportion_tests.csv |
| 06_resumen_pruebas_estadisticas | outputs/tables/statistical_tests/06_resumen_pruebas_estadisticas.csv |
| 06_spearman_correlations | outputs/tables/statistical_tests/06_spearman_correlations.csv |

## Resumen de pruebas

| prueba | p_value | conclusion |
| --- | --- | --- |
| grupo_area_vs_perdida_definitiva | 0.0994 | No se observa evidencia estadistica suficiente de asociacion entre grupo academico y perdida definitiva. |
| grupo_area_vs_riesgo_retraso_potencial | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico y riesgo de retraso academico potencial. |
| area_academica_vs_perdida_definitiva | 0.0182 | Se observa evidencia estadistica de asociacion entre area academica especifica y perdida definitiva. |
| grupo_area_vs_recursamiento_observable | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico y recursamiento observable posterior. |
| oferta_posterior_vs_recursamiento_observable | < 0.001 | Se observa evidencia estadistica de asociacion entre oferta posterior observable y recursamiento observable. |
| perdida_definitiva_area_comun_vs_profesional | 0.0909 | No se observa evidencia estadistica suficiente de asociacion entre grupo academico y perdida definitiva. |
| riesgo_retraso_area_comun_vs_profesional | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico y riesgo de retraso potencial. |
| recursamiento_area_comun_vs_profesional | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico y recursamiento observable. |
| aprobacion_al_recursar_area_comun_vs_profesional | 0.0120 | Se observa evidencia estadistica de asociacion entre grupo academico y aprobacion posterior al recursar. |
| sin_oferta_posterior_area_comun_vs_profesional | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico y perdida sin oferta posterior observable. |
| continuidad_area_comun_vs_profesional | < 0.001 | Se observa evidencia estadistica de asociacion entre grupo academico e indice de continuidad de oferta. |
| perdida_relativa_area_comun_vs_profesional | 0.4399 | No se observa evidencia estadistica suficiente de asociacion entre grupo academico y tasa de perdida definitiva por curso. |

En total se calcularon 19 pruebas con p-value
interpretable. De ellas, 15 presentan p-value
menor que 5.0%, lo que se reporta como evidencia
estadistica de asociacion observada bajo el alcance del proyecto.

## Intervalos de confianza

| indicador | grupo_area | exitos | n | proporcion | ic_95_inferior | ic_95_superior | denominador |
| --- | --- | --- | --- | --- | --- | --- | --- |
| perdida_definitiva | Area comun | 497 | 1703 | 29.2% | 27.1% | 31.4% | registros modelables con resultado final |
| riesgo_retraso_potencial | Area comun | 150 | 1703 | 8.8% | 7.6% | 10.2% | registros modelables con resultado final |
| recursamiento_observable | Area comun | 333 | 435 | 76.6% | 72.3% | 80.3% | perdidas definitivas con ventana posterior observable en 2024 |
| aprobacion_al_recursar | Area comun | 203 | 333 | 61.0% | 55.6% | 66.0% | recursamientos con resultado posterior observable |
| perdida_definitiva | Area profesional | 330 | 1023 | 32.3% | 29.5% | 35.2% | registros modelables con resultado final |
| riesgo_retraso_potencial | Area profesional | 261 | 1023 | 25.5% | 22.9% | 28.3% | registros modelables con resultado final |
| recursamiento_observable | Area profesional | 85 | 319 | 26.6% | 22.1% | 31.8% | perdidas definitivas con ventana posterior observable en 2024 |
| aprobacion_al_recursar | Area profesional | 39 | 85 | 45.9% | 35.7% | 56.4% | recursamientos con resultado posterior observable |

## Lectura vinculada con Fase 5.1

La comparacion de recursamiento observable entre area comun y area profesional
usa como denominador las perdidas definitivas con ventana posterior observable
en 2024. La proporcion estimada para area comun fue
76.6%; para area profesional
fue 26.6%.

Esta diferencia no debe interpretarse como causalidad. Es evidencia compatible
con la lectura descriptiva de Fase 5.1: la continuidad de oferta puede ampliar
la ventana observable de recursamiento, pero no garantiza aprobacion posterior.

## Limitaciones

- Los p-values se reportan sin correccion por comparaciones multiples; deben
  interpretarse como evidencia exploratoria dentro de esta fase.
- Las pruebas trabajan con registros observados en 2024; no reconstruyen la
  trayectoria academica completa de cada estudiante.
- Los indicadores de recursamiento posterior excluyen perdidas en `V2`, porque
  no existe un periodo posterior dentro de 2024 para observar el flujo.
- La prueba entre oferta posterior observable y recursamiento observable esta
  estructuralmente vinculada con la definicion del indicador; se usa como
  validacion del flujo observado, no como prueba causal independiente.
- Las pruebas por curso usan agregados y pueden verse afectadas por tamanos de
  muestra pequenos.
- No se utiliza `docente`, presupuesto, contratacion, horas docentes ni datos
  personales identificables.
- Los resultados deben leerse como asociaciones observadas, no como mecanismos
  causales demostrados.

## Conclusion

La Fase 6 aporta evidencia estadistica para contrastar los patrones descriptivos
de Fase 5 y Fase 5.1. En particular, permite evaluar si las diferencias entre
area comun y area profesional, continuidad de oferta, perdida definitiva,
recursamiento observable y riesgo potencial son consistentes con asociaciones
observadas en los datos. Estos resultados quedan listos para alimentar modelos
explicativos y analisis de cursos criticos sin afirmar causalidad.
