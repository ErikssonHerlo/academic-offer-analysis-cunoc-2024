# Descripcion de datasets

Este proyecto organiza diez datasets para analizar la oferta academica, asignaciones, resultados registrados en actas, prerrequisitos y configuracion academica de Ingenieria en Ciencias y Sistemas durante 2024.

## 01_catalogo_cursos_2024.csv

Catalogo oficial de cursos de la carrera de Ingenieria en Ciencias y Sistemas para el pensum `2016-58`.

- Registros: 90 cursos.
- Llave principal: `codigo_curso`.
- Uso principal: unificar nombres, creditos, semestre del pensum, tipo de curso y estado del curso.
- Fuente: estructura y datos de cursos disponibles en `sources/database/seeds` y `sources/database/migrations`.
- Campos: `codigo_curso`, `nombre_curso`, `semestre_pensum`, `pensum`, `tipo_curso`, `creditos`, `estado_curso`.

## 02_actas_notas_2024_detalle.csv

Dataset academico principal con resultados registrados en actas durante 2024.

- Registros: 3,468.
- Llaves de analisis: `estudiante_id_ofuscado`, `codigo_curso`, `periodo_academico`, `seccion`, `oportunidad_evaluacion`.
- Uso principal: analizar aprobacion, reprobacion, NSP, recuperaciones y equivalencias por curso y periodo.
- Fuente: Departamento de Computo.
- Campos: `estudiante_id_ofuscado`, `codigo_curso`, `periodo_academico`, `fecha_acta`, `oportunidad_evaluacion`, `seccion`, `zona`, `nota_examen`, `nota_total`, `resultado`, `numero_acta`, `estado_acta`.

## 03_asignaciones_2024.csv

Dataset de asignaciones estudiantiles por curso, periodo y seccion durante 2024.

- Registros: 2,879.
- Llaves de analisis: `estudiante_id_ofuscado`, `codigo_curso`, `periodo_academico`, `seccion`.
- Uso principal: comparar estudiantes asignados contra estudiantes con nota en acta, identificar desasignaciones y estimar demanda atendida por curso.
- Fuente: Departamento de Computo.
- Campos: `estudiante_id_ofuscado`, `codigo_curso`, `periodo_academico`, `seccion`, `fecha_asignacion`, `estado_asignacion`, `fecha_desasignacion`.

## 04_oferta_academica_2024.csv

Oferta academica aperturada en 2024, integrada con horarios, secciones, docentes, cupos, asignaciones y estudiantes con nota.

- Registros: 205.
- Llaves de analisis: `periodo_academico`, `codigo_curso`, `seccion`.
- Uso principal: medir continuidad de oferta, apertura por periodo, demanda atendida, estudiantes con nota y posibles interrupciones de continuidad academica.
- Fuentes: horarios en `sources/schedules`, catalogo de cursos, `02_actas_notas_2024_detalle.csv` y `03_asignaciones_2024.csv`.
- Campos: `periodo_academico`, `codigo_curso`, `nombre_curso`, `seccion`, `curso_aperturado`, `curso_cancelado`, `cupo_ofertado`, `estudiantes_asignados`, `estudiantes_con_nota`, `jornada`, `horario`, `salon`, `docente`, `modalidad`, `fecha_inicio`, `fecha_fin`, `fuente_archivo`, `metodo_match`, `observaciones`.

## 05_malla_prerrequisitos.csv

Malla de prerrequisitos, correquisitos y requisitos por creditos del pensum `2016-58`.

- Registros: 136.
- Llaves de analisis: `codigo_curso`, `codigo_prerrequisito`, `tipo_requisito`.
- Uso principal: identificar cursos bloqueantes y medir impacto curricular potencial cuando un estudiante reprueba un curso.
- Fuentes: pensum oficial en `sources/academic/pensum` y matriz de cursos en `sources/academic/prerrequisitos`.
- Campos: `codigo_curso`, `nombre_curso`, `codigo_prerrequisito`, `nombre_prerrequisito`, `tipo_requisito`, `es_obligatorio`, `semestre_curso`, `semestre_prerrequisito`.

## 06_calendario_academico_2024.csv

Calendario academico de los periodos utilizados en el analisis.

- Registros: 4 periodos.
- Llave principal: `periodo_academico`.
- Uso principal: ordenar periodos, ubicar fechas de clases, finales, primera recuperacion y segunda recuperacion.
- Fuentes: documentos de calendario en `sources/academic/calendario`.
- Campos: `periodo_academico`, `descripcion_periodo`, `orden_periodo`, `fecha_inicio_clases`, `fecha_fin_clases`, `fecha_examen_final`, `fecha_primera_recuperacion`, `fecha_segunda_recuperacion`.

## 07_parametros_academicos.csv

Parametros institucionales de evaluacion utilizados para interpretar resultados academicos.

- Registros: 6.
- Llave principal: `parametro`.
- Uso principal: normalizar criterios de aprobacion, nota maxima, zona, examen y tratamiento de estados como desasignado o NSP.
- Campos: `parametro`, `valor`, `descripcion`, `aplica_a`, `observaciones`.

## 08_configuracion_academica_cursos.csv

Configuracion academica consolidada por curso.

- Registros: 90.
- Llave principal: `codigo_curso`.
- Uso principal: clasificar area academica, componente practico, laboratorio, obligatoriedad, curso base y nivel de bloqueo curricular.
- Fuentes: catalogo de cursos, malla de prerrequisitos y configuracion de carrera.
- Campos: `codigo_curso`, `nombre_curso`, `area_academica`, `tipo_curso_configurado`, `requiere_laboratorio`, `componente_practico`, `curso_obligatorio`, `curso_base`, `curso_bloqueante`, `cantidad_cursos_dependientes`, `nivel_bloqueo_curricular`, `observaciones`.

## 09_estudiantes_inscritos_2024.csv

Padron de estudiantes inscritos en Ingenieria en Ciencias y Sistemas durante 2024.

- Registros: 650.
- Llave principal: `estudiante_id_ofuscado`.
- Uso principal: definir el universo de estudiantes para cruzar asignaciones y actas sin utilizar datos personales directos.
- Fuente: Departamento de Computo.
- Campos: `estudiante_id_ofuscado`, `anio_academico`, `periodo_inscripcion`, `codigo_carrera`, `nombre_carrera`, `pensum`, `cohorte_ingreso`.

## 10_inscritos_sistemas_anual.csv

Serie anual de estudiantes inscritos en Ingenieria en Ciencias y Sistemas.

- Registros: 3 anios.
- Llaves de analisis: `anio`, `codigo_carrera`.
- Uso principal: contextualizar el volumen de estudiantes de la carrera en 2022, 2023 y 2024.
- Fuentes: datos RYCA-CUNOC y registro 2024.
- Campos: `anio`, `codigo_carrera`, `nombre_carrera`, `pensum`, `estudiantes_inscritos`, `fecha_corte`, `fuente`.
