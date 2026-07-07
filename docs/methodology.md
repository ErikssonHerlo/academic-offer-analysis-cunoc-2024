# Metodologia de organizacion e integracion

## Objetivo del proyecto

El proyecto analiza la relacion entre oferta academica, asignaciones, resultados registrados en actas y estructura curricular de Ingenieria en Ciencias y Sistemas durante 2024.

El alcance se limita a datos academicos y de configuracion curricular. No incorpora presupuesto ejecutado, horas docentes, contratacion docente, encuestas ni datos personales identificables.

## Organizacion de archivos

La carpeta `data/` contiene los datasets finales en formato CSV.

La carpeta `sources/` conserva las fuentes usadas para construir, validar o contextualizar los datasets:

- `sources/academic/pensum`: pensum oficial de Ciencias y Sistemas.
- `sources/academic/prerrequisitos`: matriz y documentos de prerrequisitos.
- `sources/academic/calendario`: calendarios academicos 2024.
- `sources/schedules/S1`: horario del primer semestre 2024.
- `sources/schedules/V1`: horario de escuela de vacaciones de junio 2024.
- `sources/schedules/S2`: horario del segundo semestre 2024.
- `sources/schedules/V2`: horario de escuela de vacaciones de diciembre 2024.
- `sources/assignments/2024`: archivo de asignaciones 2024.
- `sources/assignments/historical`: historico de asignaciones 2011-2023.
- `sources/assignments/supporting`: archivos de apoyo estadistico y docente.
- `sources/institutional/informes`: informes institucionales usados como contexto.
- `sources/institutional/certificaciones`: certificaciones academicas usadas como referencia de formato.
- `sources/database`: migraciones y seeders usados para estructura academica, catalogo y pensum.

La carpeta `docs/` contiene descripcion de datasets y metodologia.

## Criterios de integracion

### Identificadores

La llave academica central de cursos es `codigo_curso`. Se utiliza para cruzar catalogo, oferta, prerrequisitos, asignaciones, actas y configuracion academica.

La llave estudiantil es `estudiante_id_ofuscado`. Esta permite cruzar actas, asignaciones y estudiantes inscritos sin incluir datos personales directos.

### Periodos academicos

Se utilizan cuatro periodos:

- `S1`: primer semestre 2024.
- `V1`: escuela de vacaciones junio 2024.
- `S2`: segundo semestre 2024.
- `V2`: escuela de vacaciones diciembre 2024.

El orden y fechas de evaluacion se toman de `06_calendario_academico_2024.csv`.

### Catalogo y pensum

El catalogo de cursos se obtiene de la estructura academica disponible en `sources/database`. Se filtra la carrera:

- Codigo: `58`.
- Nombre: `Ciencias y Sistemas`.
- Pensum: `2016-58`.

La malla de prerrequisitos se cruza contra el catalogo para asegurar que los cursos origen y destino existan dentro del pensum analizado.

### Oferta academica

La oferta academica se integra desde horarios por periodo y se cruza contra el catalogo oficial.

El cruce se hace por codigo cuando el horario lo incluye. Cuando el archivo fuente no incluye codigo, se cruza por nombre de curso y se conserva el metodo de cruce en `metodo_match`.

El dataset de oferta se complementa con:

- `estudiantes_asignados`: conteo por `periodo_academico`, `codigo_curso` y `seccion` desde `03_asignaciones_2024.csv`.
- `estudiantes_con_nota`: conteo por `periodo_academico`, `codigo_curso` y `seccion` desde `02_actas_notas_2024_detalle.csv`.
- `cupo_ofertado`: capacidad registrada para analizar demanda atendida.

### Asignaciones

`03_asignaciones_2024.csv`, provisto por el Departamento de Computo, se utiliza para identificar estudiantes asignados por curso, periodo y seccion.

Los registros con `estado_asignacion=desasignado` se conservan para medir diferencia entre asignacion y llegada a acta. Los registros desasignados no se esperan como resultados con nota en `02_actas_notas_2024_detalle.csv`.

### Actas y notas

`02_actas_notas_2024_detalle.csv`, provisto por el Departamento de Computo, se usa como fuente academica principal de resultados.

Cada fila representa un resultado registrado para una oportunidad de evaluacion:

- `Ordinario`.
- `Primera recuperacion`.
- `Segunda recuperacion`.
- `Equivalencia`.

Las fechas de acta deben ubicarse despues de la evaluacion correspondiente en el calendario academico. Como criterio operativo, las actas se consideran registradas entre 1 y 5 dias despues de la evaluacion.

Los estados se interpretan asi:

- `Aprobado`: el estudiante aprobo la oportunidad correspondiente.
- `Reprobado`: el estudiante no alcanzo la nota minima.
- `NSP`: el estudiante no se presento.
- `Equivalencia`: curso aprobado por equivalencia registrada.

### Estudiantes inscritos

`09_estudiantes_inscritos_2024.csv`, provisto por el Departamento de Computo, define el universo de estudiantes inscritos en Ciencias y Sistemas durante 2024.

Este padron se usa solo para validacion e integracion analitica, sin exponer datos personales directos ni reportar casos individuales.

### Parametros academicos

Los parametros generales utilizados son:

- Nota minima de aprobacion: 61.
- Zona maxima: 70.
- Examen maximo: 30.
- Nota total maxima: 100.

Estos parametros se conservan en `07_parametros_academicos.csv`.

### Configuracion academica de cursos

`08_configuracion_academica_cursos.csv` integra informacion de:

- catalogo de cursos;
- tipo de curso;
- area academica;
- obligatoriedad;
- componente practico;
- laboratorio;
- prerrequisitos;
- cantidad de cursos dependientes.

Con esta informacion se clasifica el nivel de bloqueo curricular y se identifican cursos base o bloqueantes.

## Validaciones aplicadas

Se validaron las siguientes relaciones:

- Todos los cursos de oferta existen en el catalogo.
- Las actas usan estudiantes presentes en el padron 2024.
- Las asignaciones usan estudiantes presentes en el padron 2024.
- No hay actas sin asignacion activa.
- No hay asignaciones activas sin registro de acta.
- Los conteos de `04_oferta_academica_2024.csv` coinciden con `02` y `03`.
- Las fechas de acta se ubican dentro de la ventana esperada posterior a la evaluacion.

## Uso analitico esperado

Con estos datasets se pueden construir indicadores como:

- tasa de aprobacion por curso y periodo;
- tasa de NSP;
- tasa de recuperacion;
- diferencia entre estudiantes asignados y estudiantes con nota;
- cursos con mayor cantidad de desasignaciones;
- cursos bloqueantes con alta reprobacion;
- continuidad de oferta por periodo;
- cursos que no aparecen en todos los periodos esperados;
- impacto curricular potencial de perder un prerrequisito.
