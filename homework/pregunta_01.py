# pylint: disable=import-outside-toplevel
import os
import re
import pandas as pd
import numpy as np


# ---------- utilidades ----------

def _read_input_csv(path: str) -> pd.DataFrame:
    """
    Lee el CSV de entrada de forma robusta: intenta con ';' y si no, con ','.
    Declara NA comunes que suelen venir como texto.
    """
    na_vals = ["", " ", "na", "n/a", "nan", "none", "null", "sin dato", "sin_dato", "nd"]
    try:
        df = pd.read_csv(path, sep=";", na_values=na_vals, dtype=str)
        if df.shape[1] == 1:  # todo en una sola columna -> probar con coma
            df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    except Exception:
        df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    return df


def _std_str(s: pd.Series) -> pd.Series:
    """
    Normaliza textos: minúsculas, strip y colapsa espacios internos.
    """
    s = s.astype(str).str.lower()
    s = s.str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s


def _to_numeric(series: pd.Series) -> pd.Series:
    """
    Convierte a número eliminando signos, separadores de miles y símbolos.
    Devuelve Int64 (acepta NA).
    """
    s = series.astype(str)
    s = s.str.replace(r"[^\d,\.\-]", "", regex=True)
    # si hay punto de miles y coma decimal -> uniformar a punto decimal
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    s = pd.to_numeric(s, errors="coerce")
    s = s.round().astype("Int64")
    return s


def _to_comuna(series: pd.Series) -> pd.Series:
    """
    Extrae dígitos de la comuna y los convierte a Int64.
    """
    s = series.astype(str).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _to_date(series: pd.Series) -> pd.Series:
    """
    Convierte fechas variadas a YYYY-MM-DD (dayfirst=True para formateos latinos).
    """
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    return dt.dt.strftime("%Y-%m-%d")


# ---------- función pedida por el profe ----------

def pregunta_01():
    """
    Limpia 'files/input/solicitudes_de_credito.csv' y escribe
    'files/output/solicitudes_de_credito.csv' (sep=';').

    Incluye:
    - Normalización de texto (lower/strip/espacios).
    - Conversión de numéricos (estrato, comuna_ciudadano, monto_del_credito).
    - Estandarización de fecha (YYYY-MM-DD).
    - Homologación estricta de categorías en 'sexo' para cumplir el test.
    - Eliminación de duplicados y filas con NA en campos clave.
    """
    in_path = os.path.join("files", "input", "solicitudes_de_credito.csv")
    out_dir = os.path.join("files", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "solicitudes_de_credito.csv")

    df = _read_input_csv(in_path)

    # Renombres mínimos por si el dataset trae pequeñas variaciones
    rename_map = {}
    if "linea_credito" in df.columns and "línea_credito" not in df.columns:
        rename_map["linea_credito"] = "línea_credito"
    if "monto_credito" in df.columns and "monto_del_credito" not in df.columns:
        rename_map["monto_credito"] = "monto_del_credito"
    df = df.rename(columns=rename_map)

    # Columnas que el test usa explícitamente
    needed = [
        "sexo",
        "tipo_de_emprendimiento",
        "idea_negocio",
        "barrio",
        "estrato",
        "comuna_ciudadano",
        "fecha_de_beneficio",
        "monto_del_credito",
        "línea_credito",
    ]

    # Normalización general de textos en categóricas
    for col in ["sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = _std_str(df[col])

    # --------- Homologación FINITA de 'sexo' (clave para pasar el test) ----------
    if "sexo" in df.columns:
        # reemplazos directos comunes
        df["sexo"] = df["sexo"].replace({
            "f": "femenino",
            "m": "masculino",
            "femenino.": "femenino",
            "masculino.": "masculino",
            "femenino ": "femenino",
            "masculino ": "masculino",
        })
        # si quedan siglas/variantes, mapear por inicial
        df["sexo"] = df["sexo"].apply(
            lambda x: "femenino" if str(x).strip().lower().startswith("f")
            else ("masculino" if str(x).strip().lower().startswith("m") else np.nan)
        )

    # Limpieza de textos extra en otras categóricas (guiones/underscores dobles)
    for col in ["tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .str.replace(r"\s*-\s*", " ", regex=True)
                .str.replace(r"_+", " ", regex=True)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

    # Sustituir strings de NA residuales por verdaderos NA
    df = df.replace({"nan": np.nan, "na": np.nan})

    # Numéricos
    if "estrato" in df.columns:
        df["estrato"] = _to_numeric(df["estrato"])
    if "comuna_ciudadano" in df.columns:
        df["comuna_ciudadano"] = _to_comuna(df["comuna_ciudadano"])
    if "monto_del_credito" in df.columns:
        df["monto_del_credito"] = _to_numeric(df["monto_del_credito"])

    # Fechas
    if "fecha_de_beneficio" in df.columns:
        df["fecha_de_beneficio"] = _to_date(df["fecha_de_beneficio"])

    # Eliminar duplicados exactos
    df = df.drop_duplicates()

    # Mantener solo filas con info crítica (las que el test usa)
    keep = [k for k in needed if k in df.columns]
    if keep:
        df = df.dropna(subset=keep)

    # Exportar con ';' (el test lee con sep=';')
    df.to_csv(out_path, sep=";", index=False)
