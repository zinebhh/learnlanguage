import pandas as pd
import re
from pathlib import Path

RAW = Path("ml/data/raw")
OUT = Path("ml/data/processed")
OUT.mkdir(parents=True, exist_ok=True)

LEVELS = {"A1","A2","B1","B2","C1","C2"}

def clean_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t

def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[["text", "cefr_level"]].copy()
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() > 0]
    df = df[df["cefr_level"].isin(LEVELS)]
    # limiter longueur extrême (optionnel)
    df = df[df["text"].str.len() <= 400]
    return df

if __name__ == "__main__":
    sp = load_and_clean(RAW / "cefr_sp_en_raw.csv")
    asag = load_and_clean(RAW / "cefr_asag_en_raw.csv")

    df = pd.concat([sp, asag], ignore_index=True).drop_duplicates()
    df.to_csv(OUT / "cefr_en_processed.csv", index=False, encoding="utf-8")

    print("Saved:", OUT / "cefr_en_processed.csv", "rows=", len(df))
    print(df["cefr_level"].value_counts())
