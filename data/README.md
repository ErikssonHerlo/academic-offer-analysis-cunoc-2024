# Notas de datasets

- Fuente local para catalogo/configuracion: `sources/database/seeds/03-course.seeder.ts`, `sources/database/seeds/04-career-course.seeder.ts`, `sources/database/seeds/05-career-field.seeder.ts`.
- Fuente principal para prerrequisitos: `sources/academic/pensum/Pensum - Ciencias y Sistemas _ CICS App.pdf`.
- Fuente secundaria revisada: `sources/academic/prerrequisitos/Matriz de Cursos Con Estadistica.docx`.
- Carrera filtrada: codigo 58, Ciencias y Sistemas.
- Pensum: `2016-58`.
- Los requisitos expresados como creditos se registran como filas con `tipo_requisito=creditos` y sin `codigo_prerrequisito`.
- La diferencia detectada en la matriz para IPC2 fue corregida: `2800` usa `290` como prerrequisito, no `209`.
- En `08_configuracion_academica_cursos.csv`, area, obligatoriedad, semestre y creditos salen de seeders; las variables de bloqueo se recalcularon con `05_malla_prerrequisitos.csv`.

## Datasets 06 y 07

- `06_calendario_academico_2024.csv` usa como fuentes `sources/academic/calendario/Calendario Académico 1-2024 - Google Drive.html` y `sources/academic/calendario/5fa3f6a8c993b54978a4a14bc79cda23bb1d2a64 (1).pdf`.
- Fechas en rangos ISO usan el formato `YYYY-MM-DD/YYYY-MM-DD`.
- Para S2, la segunda recuperacion corresponde al rango registrado en enero de 2025.
- `07_parametros_academicos.csv` usa los parametros indicados por el usuario: nota minima 61, zona maxima 70, examen maximo 30 y nota total maxima 100.
- Los registros desasignados se conservan con valor `desasignado`; NSP se conserva como atributo/resultado cuando aplica al examen final.

## Dataset 04

- `04_oferta_academica_2024.csv` cruza horarios 2024 contra `01_catalogo_cursos_2024.csv`.
- Fuentes: `sources/schedules/S1/Horario de Clases 01-2024-L-M-V - SD.pdf`, `sources/schedules/V1/Horario de Clases Escuela de Vacaciones Junio 2024 - Google Drive.html`, `sources/schedules/S2/Dias Cursos Segundo Semestre 2024.pdf`, `sources/schedules/V2/HORARIO EDV-Dic-2024 - Google Drive.html`.
- Los semestres S1/S2 se extrajeron por codigo desde PDFs; las escuelas de vacaciones V1/V2 se cruzaron por nombre porque los horarios no siempre traen codigo.
- Correccion aplicada: IPC1 (`2796`) en S1 conserva solo seccion A; la seccion B del archivo fuente se excluyo.
- Cupo, estudiantes asignados y estudiantes con nota se completan desde `03_asignaciones_2024.csv` y `02_actas_notas_2024_detalle.csv`.
- Se incorporan secciones identificadas en `sources/assignments/2024/Asignaciones Sistemas 2024.xlsx` cuando no estaban en la extraccion inicial de horarios.

## Datasets 02 y 03

- `02_actas_notas_2024_detalle.csv` fue provisto por el Departamento de Computo.
- `03_asignaciones_2024.csv` fue provisto por el Departamento de Computo.
- `03_asignaciones_2024.csv` contiene asignaciones por estudiante, periodo, curso y seccion.
- `02_actas_notas_2024_detalle.csv` contiene resultados por estudiante, curso, periodo, oportunidad de evaluacion y acta.
- Las actas se registran entre 1 y 5 dias despues de la evaluacion correspondiente en `06_calendario_academico_2024.csv`.
- Los desasignados se conservan en asignaciones con `estado_asignacion=desasignado`.
- Los casos NSP se registran en actas con `resultado=NSP`.
- Las equivalencias se registran como `oportunidad_evaluacion=Equivalencia`, `nota_total=EQ` y `resultado=Aprobado`.

## Dataset 09

- `09_estudiantes_inscritos_2024.csv` fue provisto por el Departamento de Computo.
- `09_estudiantes_inscritos_2024.csv` define el universo de estudiantes inscritos para validar y cruzar asignaciones y actas 2024.
- Cantidad: 650 estudiantes inscritos en Ciencias y Sistemas durante 2024.
- Todos los registros tienen `periodo_inscripcion=S1`, porque la inscripcion anual se registra en el primer semestre.
- El archivo no guarda carne ni datos personales directos; solo conserva `estudiante_id_ofuscado`.
- Distribucion por cohorte de ingreso: 2016=12, 2017=18, 2018=28, 2019=42, 2020=60, 2021=76, 2022=94, 2023=140, 2024=180.

## Dataset 10

- `10_inscritos_sistemas_anual.csv` contiene la cantidad anual de estudiantes inscritos en Ingenieria en Ciencias y Sistemas.
- Datos registrados: 2022=634, 2023=535, 2024=650.
