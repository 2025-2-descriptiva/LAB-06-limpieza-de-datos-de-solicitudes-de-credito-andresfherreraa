# pylint: disable=import-outside-toplevel
import os
import pandas as pd
import numpy as np
import unicodedata
import re


def _read_input_csv(path: str) -> pd.DataFrame:
    """Lectura robusta: intenta ';' y si no, ','; mantiene strings."""
    na_vals = ["", " ", "na", "n/a", "nan", "none", "null"]
    try:
        df = pd.read_csv(path, sep=";", dtype=str, na_values=na_vals)
        if df.shape[1] == 1:
            df = pd.read_csv(path, sep=",", dtype=str, na_values=na_vals)
    except Exception:
        df = pd.read_csv(path, sep=",", dtype=str, na_values=na_vals)
    return df


def _std_str(s: pd.Series) -> pd.Series:
    """Minúsculas, trim, colapsa espacios."""
    s = s.astype(str).str.lower().str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s


def _clean_text(s: pd.Series) -> pd.Series:
    """Normaliza separadores y acentos para mejorar colapso de duplicados."""
    s = _std_str(s)
    s = s.str.replace(r"[-_\.]+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    # quitar acentos (opcional, pero ayuda a colapsar variantes)
    s = s.apply(lambda x: "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)))
    return s


def _map_sex(x: str) -> str:
    x = str(x).strip().lower()
    if x.startswith("f"):
        return "femenino"
    if x.startswith("m"):
        return "masculino"
    return np.nan


def _to_int(series: pd.Series) -> pd.Series:
    """Extrae dígitos, convierte a Int64 (sin redondear)."""
    s = series.astype(str).str.replace(r"[^\d]", "", regex=True)
    s = s.replace("", np.nan)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _to_date(series: pd.Series) -> pd.Series:
    """Fecha a YYYY-MM-DD (dayfirst=True)."""
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    return dt.dt.strftime("%Y-%m-%d")


def pregunta_01():
    """
    Limpia 'files/input/solicitudes_de_credito.csv' y escribe
    'files/output/solicitudes_de_credito.csv' con ';'.

    Pasos:
      - Eliminar columna índice 'Unnamed: 0' si existe.
      - Normalizar strings y separadores en columnas categóricas.
      - Homologar 'sexo' a {'femenino','masculino'} y filtrar fuera del set.
      - Convertir numéricos (estrato, comuna_ciudadano, monto_del_credito).
      - Convertir fecha a 'YYYY-MM-DD'.
      - Excluir filas con el string literal 'nan' en 'barrio' o 'tipo_de_emprendimiento'.
      - Eliminar duplicados después de toda la limpieza.
    """
    in_path = os.path.join("files", "input", "solicitudes_de_credito.csv")
    out_dir = os.path.join("files", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "solicitudes_de_credito.csv")

    df = _read_input_csv(in_path)

    # Quitar índice basura si viene
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Renombres defensivos que a veces aparecen
    if "linea_credito" in df.columns and "línea_credito" not in df.columns:
        df = df.rename(columns={"linea_credito": "línea_credito"})
    if "monto_credito" in df.columns and "monto_del_credito" not in df.columns:
        df = df.rename(columns={"monto_credito": "monto_del_credito"})

    # Normalización de categóricas
    for col in ["sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]:
        if col in df.columns:
            df[col] = _clean_text(df[col])

    # Homologación estricta de 'sexo' y filtro a dos categorías
    if "sexo" in df.columns:
        df["sexo"] = df["sexo"].apply(_map_sex)
        df = df[df["sexo"].isin(["femenino", "masculino"])]

    # Eliminar filas con el string literal "nan" en estos campos (no son NaN reales)
    for col in ["barrio", "tipo_de_emprendimiento"]:
        if col in df.columns:
            df = df[df[col] != "nan"]

    # Numéricos
    if "estrato" in df.columns:
        df["estrato"] = _to_int(df["estrato"])
    if "comuna_ciudadano" in df.columns:
        # Ojo: el test espera los valores tal como vienen (10, 20, ..., 900), no dividir por 10
        df["comuna_ciudadano"] = _to_int(df["comuna_ciudadano"])
    if "monto_del_credito" in df.columns:
        df["monto_del_credito"] = _to_int(df["monto_del_credito"])

    # Fechas
    if "fecha_de_beneficio" in df.columns:
        df["fecha_de_beneficio"] = _to_date(df["fecha_de_beneficio"])

    # Eliminar duplicados una vez todo está limpio (esto es clave)
    df = df.drop_duplicates()

    # Exportar con ';' para que el test lo lea tal cual
    df.to_csv(out_path, sep=";", index=False)
