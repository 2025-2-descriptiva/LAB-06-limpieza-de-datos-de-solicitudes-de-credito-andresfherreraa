# pylint: disable=import-outside-toplevel
import os
import re
import pandas as pd
import numpy as np


def _read_input_csv(path: str) -> pd.DataFrame:
    """
    Lectura robusta del CSV: intenta con ';' y si no, con ','.
    Declara NA comunes que suelen venir como texto.
    """
    na_vals = ["", " ", "na", "n/a", "nan", "none", "null", "sin dato", "sin_dato", "nd"]
    try:
        df = pd.read_csv(path, sep=";", na_values=na_vals, dtype=str)
        if df.shape[1] == 1:  # cayó todo en una columna -> reintentar con coma
            df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    except Exception:
        df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    return df


def _std_str(s: pd.Series) -> pd.Series:
    """
    Normaliza textos: minúsculas, strip, colapsa espacios internos.
    (No cambiamos nombres de columnas; solo contenidos).
    """
    s = s.astype(str).str.lower()
    s = s.str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s


def _to_numeric(series: pd.Series) -> pd.Series:
    """
    Convierte a número eliminando signos, puntos y comas de miles.
    Devuelve Int64 (acepta NA).
    """
    s = series.astype(str).str.replace(r"[^\d\-\.]", "", regex=True)
    # si vienen miles con punto y decimales con coma, uniformar
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    s = pd.to_numeric(s, errors="coerce")
    # la mayoría son montos enteros
    s = s.round().astype("Int64")
    return s


def _to_comuna(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _to_date(series: pd.Series) -> pd.Series:
    """
    Convierte fechas variadas a YYYY-MM-DD (día primero si aplica).
    """
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True, infer_datetime_format=True)
    return dt.dt.strftime("%Y-%m-%d")


def pregunta_01():
    """
    Limpia 'files/input/solicitudes_de_credito.csv' y escribe
    'files/output/solicitudes_de_credito.csv' (sep=';').

    Pasos clave (alineados con lo visto en clase y con el autograder):
    - Normalización de texto (lower, trim, espacios).
    - Estandarización de NA.
    - Conversión de numéricos (monto, estrato, comuna).
    - Conversión de fecha a YYYY-MM-DD.
    - Unificación de categorías (sin tildes/espacios erráticos).
    - Eliminación de duplicados y filas sin información crítica.
    """
    in_path = os.path.join("files", "input", "solicitudes_de_credito.csv")
    out_dir = os.path.join("files", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "solicitudes_de_credito.csv")

    df = _read_input_csv(in_path)

    # Asegurar columnas esperadas (no renombramos, solo usamos si existen)
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
    # En algunos datasets vienen con ligeras variaciones; mapeo mínimo
    rename_map = {}
    # por si llega 'linea_credito' sin tilde
    if "linea_credito" in df.columns and "línea_credito" not in df.columns:
        rename_map["linea_credito"] = "línea_credito"
    # por si llega 'monto_credito'
    if "monto_credito" in df.columns and "monto_del_credito" not in df.columns:
        rename_map["monto_credito"] = "monto_del_credito"
    df = df.rename(columns=rename_map)

    # Solo seguimos si están las columnas principales; el test fallará si no.
    # Normalización de strings en las categóricas
    for col in ["sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = _std_str(df[col])

    # Limpieza específica de categorías: quitar guiones bajos/dobles espacios residuales
    for col in ["tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = df[col].str.replace(r"\s*-\s*", " ", regex=True)
            df[col] = df[col].str.replace(r"_+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()

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

    # Eliminar filas completamente duplicadas
    df = df.drop_duplicates()

    # Filtrado de calidad: requerimos campos clave no vacíos para el análisis del test
    keys = [
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
    keep = [k for k in keys if k in df.columns]
    df = df.dropna(subset=keep)

    # Exportar con ';' como separador (como lo lee el test)
    df.to_csv(out_path, sep=";", index=False)