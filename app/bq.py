from google.cloud import bigquery

from app.settings import BIGQUERY_DATASET, BIGQUERY_PROJECT


def client():
    kwargs = {}
    if BIGQUERY_PROJECT:
        kwargs["project"] = BIGQUERY_PROJECT
    return bigquery.Client(**kwargs)


def query(sql: str, parameters=None):
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    return list(client().query(sql, job_config=job_config).result())
