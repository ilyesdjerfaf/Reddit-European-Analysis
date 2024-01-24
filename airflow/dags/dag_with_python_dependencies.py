from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'ilyes_djerfaf',
    'retry':  5,
    'retry_delay': timedelta(minutes=5)
}

def get_dependencies():
    import praw
    print(praw.__version__)

    import pandas as pd
    print(pd.__version__)

    import supabase
    print(supabase.__version__)



with DAG(
    default_args=default_args,
    dag_id='dag_with_python_dependencies_v01',
    start_date=datetime(2021, 1, 1),
    schedule_interval='@daily'
) as dag:
    
    get_dependencies = PythonOperator(
        task_id='get_dependencies',
        python_callable=get_dependencies
    )

    get_dependencies