"""Constantes y rutas centralizadas del proyecto.

El objetivo de este modulo es evitar valores literales dispersos en el codigo.
Las fases posteriores deben importar estas constantes en lugar de repetir
nombres de archivos, periodos, estados academicos o columnas esperadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"

DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

PERIOD_ORDER: tuple[str, ...] = ("S1", "V1", "S2", "V2")
PERIOD_LABELS: dict[str, str] = {
    "S1": "Primer semestre 2024",
    "V1": "Escuela de vacaciones junio 2024",
    "S2": "Segundo semestre 2024",
    "V2": "Escuela de vacaciones diciembre 2024",
}

RESULT_APPROVED = "Aprobado"
RESULT_FAILED = "Reprobado"
RESULT_NSP = "NSP"

EVALUATION_ORDINARY = "Ordinario"
EVALUATION_FIRST_RECOVERY = "Primera recuperacion"
EVALUATION_SECOND_RECOVERY = "Segunda recuperacion"
EVALUATION_EQUIVALENCE = "Equivalencia"

ASSIGNMENT_WITH_GRADE = "con nota"
ASSIGNMENT_DROPPED = "desasignado"

YES_VALUE = "Si"
NO_VALUE = "No"
SPECIAL_EQ_VALUE = "EQ"

PASSING_GRADE_PARAMETER = "nota_minima_aprobacion"


@dataclass(frozen=True)
class DatasetSpec:
    """Contrato minimo esperado para cada dataset raw."""

    filename: str
    required_columns: tuple[str, ...]
    key_columns: tuple[str, ...] = ()

    @property
    def path(self) -> Path:
        return RAW_DATA_DIR / self.filename


DATASET_SPECS: dict[str, DatasetSpec] = {
    "catalogo_cursos": DatasetSpec(
        filename="01_catalogo_cursos_2024.csv",
        required_columns=(
            "codigo_curso",
            "nombre_curso",
            "semestre_pensum",
            "pensum",
            "tipo_curso",
            "creditos",
            "estado_curso",
        ),
        key_columns=("codigo_curso",),
    ),
    "actas_notas": DatasetSpec(
        filename="02_actas_notas_2024_detalle.csv",
        required_columns=(
            "estudiante_id_ofuscado",
            "codigo_curso",
            "periodo_academico",
            "fecha_acta",
            "oportunidad_evaluacion",
            "seccion",
            "zona",
            "nota_examen",
            "nota_total",
            "resultado",
            "numero_acta",
            "estado_acta",
        ),
    ),
    "asignaciones": DatasetSpec(
        filename="03_asignaciones_2024.csv",
        required_columns=(
            "estudiante_id_ofuscado",
            "codigo_curso",
            "periodo_academico",
            "seccion",
            "fecha_asignacion",
            "estado_asignacion",
            "fecha_desasignacion",
        ),
    ),
    "oferta_academica": DatasetSpec(
        filename="04_oferta_academica_2024.csv",
        required_columns=(
            "periodo_academico",
            "codigo_curso",
            "nombre_curso",
            "seccion",
            "curso_aperturado",
            "curso_cancelado",
            "cupo_ofertado",
            "estudiantes_asignados",
            "estudiantes_con_nota",
            "jornada",
            "horario",
            "salon",
            "docente",
            "modalidad",
            "fecha_inicio",
            "fecha_fin",
            "fuente_archivo",
            "metodo_match",
            "observaciones",
        ),
        key_columns=("periodo_academico", "codigo_curso", "seccion"),
    ),
    "malla_prerrequisitos": DatasetSpec(
        filename="05_malla_prerrequisitos.csv",
        required_columns=(
            "codigo_curso",
            "nombre_curso",
            "codigo_prerrequisito",
            "nombre_prerrequisito",
            "tipo_requisito",
            "es_obligatorio",
            "semestre_curso",
            "semestre_prerrequisito",
        ),
    ),
    "calendario_academico": DatasetSpec(
        filename="06_calendario_academico_2024.csv",
        required_columns=(
            "periodo_academico",
            "descripcion_periodo",
            "orden_periodo",
            "fecha_inicio_clases",
            "fecha_fin_clases",
            "fecha_examen_final",
            "fecha_primera_recuperacion",
            "fecha_segunda_recuperacion",
        ),
        key_columns=("periodo_academico",),
    ),
    "parametros_academicos": DatasetSpec(
        filename="07_parametros_academicos.csv",
        required_columns=(
            "parametro",
            "valor",
            "descripcion",
            "aplica_a",
            "observaciones",
        ),
        key_columns=("parametro",),
    ),
    "configuracion_cursos": DatasetSpec(
        filename="08_configuracion_academica_cursos.csv",
        required_columns=(
            "codigo_curso",
            "nombre_curso",
            "area_academica",
            "tipo_curso_configurado",
            "requiere_laboratorio",
            "componente_practico",
            "curso_obligatorio",
            "curso_base",
            "curso_bloqueante",
            "cantidad_cursos_dependientes",
            "nivel_bloqueo_curricular",
            "observaciones",
        ),
        key_columns=("codigo_curso",),
    ),
    "estudiantes_inscritos": DatasetSpec(
        filename="09_estudiantes_inscritos_2024.csv",
        required_columns=(
            "estudiante_id_ofuscado",
            "anio_academico",
            "periodo_inscripcion",
            "codigo_carrera",
            "nombre_carrera",
            "pensum",
            "cohorte_ingreso",
        ),
        key_columns=("estudiante_id_ofuscado",),
    ),
    "inscritos_sistemas_anual": DatasetSpec(
        filename="10_inscritos_sistemas_anual.csv",
        required_columns=(
            "anio",
            "codigo_carrera",
            "nombre_carrera",
            "pensum",
            "estudiantes_inscritos",
            "fecha_corte",
            "fuente",
        ),
        key_columns=("anio", "codigo_carrera"),
    ),
}

REQUIRED_DIRECTORIES: tuple[Path, ...] = (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    FIGURES_DIR / "eda",
    FIGURES_DIR / "models",
    FIGURES_DIR / "clusters",
    TABLES_DIR / "indicators",
    TABLES_DIR / "statistical_tests",
    TABLES_DIR / "models",
    REPORTS_DIR,
    DOCS_DIR,
    NOTEBOOKS_DIR,
)
