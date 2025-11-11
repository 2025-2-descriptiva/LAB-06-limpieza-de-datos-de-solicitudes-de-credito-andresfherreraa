"""
Escriba el codigo que ejecute la accion solicitada en la pregunta.
"""

import os
import re
import pandas as pd
import numpy as np


def _read_input_csv(path: str) -> pd.DataFrame:

    na_vals = ["", " ", "na", "n/a", "nan", "none", "null", "sin dato", "sin_dato", "nd"]
    try:
        df = pd.read_csv(path, sep=";", na_values=na_vals, dtype=str)
        if df.shape[1] == 1:  
            df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    except Exception:
        df = pd.read_csv(path, sep=",", na_values=na_vals, dtype=str)
    return df


def _std_str(s: pd.Series) -> pd.Series:

    s = s.astype(str).str.lower()
    s = s.str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s


def _to_numeric(series: pd.Series) -> pd.Series:

    s = series.astype(str).str.replace(r"[^\d\-\.]", "", regex=True)

    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    s = pd.to_numeric(s, errors="coerce")

    s = s.round().astype("Int64")
    return s


def _to_comuna(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _to_date(series: pd.Series) -> pd.Series:

    dt = pd.to_datetime(series, errors="coerce", dayfirst=True, infer_datetime_format=True)
    return dt.dt.strftime("%Y-%m-%d")

def pregunta_01():
    """
    Realice la limpieza del archivo "files/input/solicitudes_de_credito.csv".
    El archivo tiene problemas como registros duplicados y datos faltantes.
    Tenga en cuenta todas las verificaciones discutidas en clase para
    realizar la limpieza de los datos.

    El archivo limpio debe escribirse en "files/output/solicitudes_de_credito.csv"

    """
    in_path = os.path.join("files", "input", "solicitudes_de_credito.csv")
    out_dir = os.path.join("files", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "solicitudes_de_credito.csv")

    df = _read_input_csv(in_path)


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

    rename_map = {}

    if "linea_credito" in df.columns and "línea_credito" not in df.columns:
        rename_map["linea_credito"] = "línea_credito"

    if "monto_credito" in df.columns and "monto_del_credito" not in df.columns:
        rename_map["monto_credito"] = "monto_del_credito"
    df = df.rename(columns=rename_map)


    for col in ["sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = _std_str(df[col])


    for col in ["tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = df[col].str.replace(r"\s*-\s*", " ", regex=True)
            df[col] = df[col].str.replace(r"_+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()

    if "estrato" in df.columns:
        df["estrato"] = _to_numeric(df["estrato"])
    if "comuna_ciudadano" in df.columns:
        df["comuna_ciudadano"] = _to_comuna(df["comuna_ciudadano"])
    if "monto_del_credito" in df.columns:
        df["monto_del_credito"] = _to_numeric(df["monto_del_credito"])


    if "fecha_de_beneficio" in df.columns:
        df["fecha_de_beneficio"] = _to_date(df["fecha_de_beneficio"])

    df = df.drop_duplicates()


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


    df.to_csv(out_path, sep=";", index=False)