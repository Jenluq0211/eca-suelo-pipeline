import pandas as pd
from pathlib import Path
import psycopg

# ==================================================
# CONFIGURACION
# ==================================================

USO_SUELO = "AGRICOLA"

# Opciones:
# AGRICOLA
# RESIDENCIAL
# COMERCIAL_INDUSTRIAL

RUTA_ECA = "data/eca_suelo.csv"
RUTA_RESULTADOS = "data/resultados_suelo.csv"

OUTPUT_DIR = "output"

# ==================================================
# CREAR CARPETA OUTPUT
# ==================================================

Path(OUTPUT_DIR).mkdir(exist_ok=True)

# ==================================================
# CARGAR ARCHIVOS
# ==================================================

print("\nLeyendo archivos...")

eca = pd.read_csv(RUTA_ECA)
resultados = pd.read_csv(RUTA_RESULTADOS)

# ==================================================
# NORMALIZAR COLUMNAS
# ==================================================

eca.columns = (
    eca.columns
    .str.strip()
    .str.lower()
)

resultados.columns = (
    resultados.columns
    .str.strip()
    .str.lower()
)

# ==================================================
# VALIDAR COLUMNAS OBLIGATORIAS
# ==================================================

columnas_eca = [
    "parametro",
    "unidad",
    "uso_suelo",
    "valor_eca"
]

columnas_resultados = [
    "muestra",
    "parametro",
    "resultado"
]

for col in columnas_eca:

    if col not in eca.columns:
        raise Exception(
            f"Falta columna en ECA: {col}"
        )

for col in columnas_resultados:

    if col not in resultados.columns:
        raise Exception(
            f"Falta columna en resultados: {col}"
        )

print("Validacion de columnas correcta")

# ==================================================
# LIMPIAR TEXTO
# ==================================================

eca["parametro"] = (
    eca["parametro"]
    .astype(str)
    .str.strip()
)

resultados["parametro"] = (
    resultados["parametro"]
    .astype(str)
    .str.strip()
)

# ==================================================
# FILTRAR ECA
# ==================================================

eca_filtrado = eca[
    eca["uso_suelo"]
    .str.upper()
    == USO_SUELO.upper()
]

print(f"\nUso de suelo seleccionado: {USO_SUELO}")

print("\nRegistros ECA encontrados:")

print(len(eca_filtrado))

# ==================================================
# UNIR RESULTADOS + ECA
# ==================================================

comparacion = pd.merge(
    resultados,
    eca_filtrado[
        [
            "parametro",
            "valor_eca"
        ]
    ],
    on="parametro",
    how="left"
)

# ==================================================
# VERIFICAR PARAMETROS SIN ECA
# ==================================================

sin_eca = comparacion[
    comparacion["valor_eca"].isna()
]

if len(sin_eca) > 0:

    print("\nADVERTENCIA")
    print("Parametros sin valor ECA:")

    print(
        sin_eca["parametro"]
        .unique()
    )

# ==================================================
# EVALUACION DE CUMPLIMIENTO
# ==================================================

comparacion["estado"] = comparacion.apply(
    lambda x:
    "SIN_ECA"
    if pd.isna(x["valor_eca"])
    else (
        "EXCEDE"
        if x["resultado"] > x["valor_eca"]
        else "CUMPLE"
    ),
    axis=1
)

# ==================================================
# KPI
# ==================================================

total = len(comparacion)

cumplen = len(
    comparacion[
        comparacion["estado"] == "CUMPLE"
    ]
)

exceden = len(
    comparacion[
        comparacion["estado"] == "EXCEDE"
    ]
)

sin_eca_total = len(
    comparacion[
        comparacion["estado"] == "SIN_ECA"
    ]
)

porcentaje_cumplimiento = (
    cumplen / total * 100
    if total > 0
    else 0
)

# ==================================================
# MOSTRAR KPI
# ==================================================

print("\n========================")
print("KPI DE CUMPLIMIENTO")
print("========================")

print(f"Total registros : {total}")
print(f"Cumplen         : {cumplen}")
print(f"Exceden         : {exceden}")
print(f"Sin ECA         : {sin_eca_total}")
print(
    f"% Cumplimiento  : {porcentaje_cumplimiento:.2f}%"
)

# ==================================================
# EXPORTAR RESULTADOS
# ==================================================

comparacion.to_csv(
    "output/comparacion_eca.csv",
    index=False
)

comparacion[
    comparacion["estado"] == "EXCEDE"
].to_csv(
    "output/excedencias.csv",
    index=False
)

kpi = pd.DataFrame(
    [
        {
            "uso_suelo": USO_SUELO,
            "total_registros": total,
            "cumplen": cumplen,
            "exceden": exceden,
            "sin_eca": sin_eca_total,
            "porcentaje_cumplimiento":
            round(
                porcentaje_cumplimiento,
                2
            )
        }
    ]
)

kpi.to_csv(
    "output/kpi.csv",
    index=False
)

print("\nArchivos generados:")

print("output/comparacion_eca.csv")

print("output/excedencias.csv")

print("output/kpi.csv")

print("\nProceso finalizado correctamente")

# ==================================================
# GUARDAR RESULTADOS EN POSTGRESQL
# ==================================================

try:

    conn = psycopg.connect(
        host="127.0.0.1",
        port="5434",
        dbname="eca_suelo",
        user="eca_admin",
        password="eca123"
    )

    cursor = conn.cursor()

    print("\nConectado a PostgreSQL")

    # ------------------------------------------
    # INSERTAR RESULTADOS
    # ------------------------------------------

    for _, fila in comparacion.iterrows():

        cursor.execute(
            """
            INSERT INTO resultados_eca
            (
                muestra,
                parametro,
                resultado,
                valor_eca,
                estado
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                fila["muestra"],
                fila["parametro"],
                float(fila["resultado"]),
                float(fila["valor_eca"]),
                fila["estado"]
            )
        )

    # ------------------------------------------
    # INSERTAR KPI
    # ------------------------------------------

    cursor.execute(
        """
        INSERT INTO kpi_cumplimiento
        (
            uso_suelo,
            total_registros,
            cumplen,
            exceden,
            sin_eca,
            porcentaje_cumplimiento
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            USO_SUELO,
            total,
            cumplen,
            exceden,
            sin_eca_total,
            porcentaje_cumplimiento
        )
    )

    conn.commit()

    print("Datos almacenados en PostgreSQL")

    cursor.close()
    conn.close()

except Exception as e:

    print("\nERROR SQL")

    print(e)

    print("Modulo PostgreSQL implementado")