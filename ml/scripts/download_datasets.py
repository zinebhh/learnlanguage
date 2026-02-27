from datasets import load_dataset
import pandas as pd
from pathlib import Path

OUT = Path("ml/data/raw")
OUT.mkdir(parents=True, exist_ok=True)

def save_dataset(hf_name: str, filename: str):
    ds = load_dataset(hf_name)
    df = pd.DataFrame(ds["train"])
    df.to_csv(OUT / filename, index=False, encoding="utf-8")
    print(f"Saved: {OUT/filename} rows={len(df)}")

if __name__ == "__main__":
    save_dataset("UniversalCEFR/cefr_sp_en", "cefr_sp_en_raw.csv")
    save_dataset("UniversalCEFR/cefr_asag_en", "cefr_asag_en_raw.csv")
