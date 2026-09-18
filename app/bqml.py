from app.bq import query


def predict_song_score(model: str, feature_sql: str):
    return query("SELECT * FROM ML.PREDICT(MODEL `" + model + "`, (" + feature_sql + "))")
