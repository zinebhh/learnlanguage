import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
import joblib

DATA = Path("ml/data/processed/cefr_en_processed.csv")
OUT = Path("ml/models")
OUT.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    df = pd.read_csv(DATA)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["cefr_level"], test_size=0.2, random_state=42, stratify=df["cefr_level"]
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=12000, ngram_range=(1,2))),
        ("clf", LinearSVC(class_weight="balanced"))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(classification_report(y_test, y_pred))

    joblib.dump(model, OUT / "cefr_model.pkl")
    print("Saved model:", OUT / "cefr_model.pkl")
