##############################################################################################
# Description: This DAG is used to ingest raw data from Reddit API and store it in Supabase
# Author:      Ilyes DJERFAF
# Date:        2024-01-14
# Notes:       This DAG is scheduled to run weekly

# ##############################################################################################

# References:
## praw : https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
## supabase : https://supabase.io/docs/reference/javascript/createclient
## astro dev : https://www.astronomer.io/guides/airflow-importing-from-pip-packages
## airflow : https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html
## airflow : https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html#creating-a-dag
# ##############################################################################################

################################################################################
############################## Imports #########################################
################################################################################
from datetime import datetime, timedelta
from airflow.models import DAG
import pandas as pd
import yaml
import praw
import supabase
from pandas import DataFrame
from supabase import create_client, Client

################################################################################
############################## DAG Arguments ###################################
################################################################################

def get_credentials() -> dict:
    """
    Get Reddit and Supabase credentials from yaml file
    :return: credentials dict
    """

    # your credentials function here ! (you can use a yaml file)
    credentials = {}

    return credentials

def read_table(table_name: str, supabase: Client) -> DataFrame:
    """
    Method to read a supabase table
    :param table_name: table name to read
    :param supabase: supabase object
    :return: DataFrame
    """
    _table = supabase.table(table_name).select("*").execute()
    fetch = True
    for param in _table:
        if fetch:
            _data = param
            fetch = False

    data = _data[1]
    df = pd.DataFrame(data)

    return df

def drop_table(table_name: str, supabase: Client) -> None:
    """
    Method to drop a supabase table
    :param table_name: table name to drop
    :param supabase: supabase object
    :return: None
    """
    data, count = supabase.table(table_name).delete().gte("id", 0).execute()

def extract() -> None:
    """
    Extract data from Reddit API
    :param kwargs: context
    :return: None
    """

    ########################################
    # Initialization
    ########################################

    # Step 1: Get credentials
    credentials: dict = get_credentials()

    # Step 2: Setting up REDDIT variables
    username: str = credentials["REDDIT"]["USERNAME"]
    password: str = credentials["REDDIT"]["PASSWORD"]
    app_client_ID: str = credentials["REDDIT"]["APP_CLIENT_ID"]
    app_client_secret: str = credentials["REDDIT"]["APP_CLIENT_SECRET"]
    user_agent: str = credentials["REDDIT"]["USER_AGENT"]

    # Step 3: Setting up SUPABASE variables
    url: str = credentials["SUPABASE"]["URL"]
    key: str = credentials["SUPABASE"]["KEY"]
    random_email: str = credentials["SUPABASE"]["RANDOM_EMAIL"]
    random_password: str = credentials["SUPABASE"]["RANDOM_PASSWORD"]

    # Step 4: Create a Praw Object
    reddit = praw.Reddit(
        client_id=app_client_ID,
        client_secret=app_client_secret,
        password=password,
        user_agent=user_agent,
        username=username,
    )

    # Step 5: Create a Supabase Object
    supabase: Client = create_client(url, key)
    user = supabase.auth.sign_up({"email": random_email, "password": random_password})
    user = supabase.auth.sign_in_with_password(
        {"email": random_email, "password": random_password}
    )

    # Step 6 : Reddit of each European country as a dictionary sorted by country name

    european_countries = {
        "Armenia": "armenian",
        "Austria": "austria",
        "Belarus": "belarus",
        "Belgium": "belgium",
        "Bosnia and Herzegovina": "bih",
        "Bulgaria": "bulgaria",
        "Croatia": "croatia",
        "Cyprus": "cyprus",
        "Czechia": "czech",
        "Denmark": "Denmark",
        "Estonia": "eesti",
        "Finland": "Finland",
        "France": "france",
        "Germany": "Germany",
        "Greece": "greece",
        "Hungary": "hungary",
        "Iceland": "Iceland",
        "Ireland": "ireland",
        "Italy": "it",
        "Latvia": "Latvia",
        "Lithuania": "lithuania",
        "Luxembourg": "Luxembourg",
        "Malta": "malta",
        "Netherlands": "TheNetherlands",
        "Norway": "norway",
        "Poland": "poland",
        "Portugal": "portugal",
        "Republic of Moldova": "moldova",
        "Romania": "Romania",
        "Serbia": "serbia",
        "Slovakia": "Slovakia",
        "Slovenia": "Slovenia",
        "Spain": "es",
        "Sweden": "sweden",
        "Switzerland": "switzerland",
        "TFYR Macedonia": "macedonia",
        "Turkey": "Turkey",
        "Ukraine": "Ukrainian",
        "United Kingdom": "unitedkingdom",
    }

    ########################################
    # Extraction
    ########################################

    # Step 1 : Drop the table if it exists
    drop_table("hot_posts", supabase)

    # Step 2 : Create the table of raw data
    for country in european_countries:
        subreddit = reddit.subreddit(european_countries[country])
        # for each country, we are going to extract the hot 10 topics
        for submission in subreddit.hot(limit=10):
            # delete all moreComments
            submission.comments.replace_more(limit=0)
            top_level_comments = list(
                submission.comments
            )  # to have the first level comments only
            # fill the table
            data = (
                supabase.table("hot_posts")
                .insert(
                    {
                        "country": str(country),
                        "title": str(submission.title),
                        "num_comments": int(submission.num_comments),
                        "score": int(submission.score),
                        "saved": submission.saved,
                        "over_18": submission.over_18,
                        "is_original_content": submission.is_original_content,
                        "upvote_ratio": submission.upvote_ratio,
                    }
                )
                .execute()
            )

def transform() -> DataFrame:
    """
    Transform table of raw data from Supabase into a table of clean data,
    merge it with the table of capitals, latitude, longitude and population
    :return: the transformed DataFrame
    """

    ########################################
    # Initialization
    ########################################

    # Step 1: Get credentials
    credentials: dict = get_credentials()

    # Step 2: Setting up SUPABASE variables
    url: str = credentials["SUPABASE"]["URL"]
    key: str = credentials["SUPABASE"]["KEY"]
    random_email: str = credentials["SUPABASE"]["RANDOM_EMAIL"]
    random_password: str = credentials["SUPABASE"]["RANDOM_PASSWORD"]

    # Step 3: Create a Supabase Object
    supabase: Client = create_client(url, key)
    user = supabase.auth.sign_up({"email": random_email, "password": random_password})
    user = supabase.auth.sign_in_with_password(
        {"email": random_email, "password": random_password}
    )

    ########################################
    # Transformation
    ########################################

    # Step 1 : Read the table of raw data
    dataset = read_table("hot_posts", supabase)

    # Step 2 : Create new aggregate columns
    bool_columns = ["over_18", "is_original_content"]
    count_columns = ["num_comments", "score"]
    avg_columns = ["num_comments", "score", "upvote_ratio"]

    for col in bool_columns:
        dataset[f"count_{col}"] = dataset.groupby("country")[col].transform(
            lambda x: x.sum()
        )

    for col in count_columns:
        dataset[f"count_{col}"] = dataset.groupby("country")[col].transform("sum")
    for col in avg_columns:
        dataset[f"avg_{col}"] = dataset.groupby("country")[col].transform("mean")

    # Step 3 : Read the table of capitals, latitude, longitude and population
    df_capital = read_table("country-capital-lat-long-population", supabase)

    # Step 4 : Transform the datetime column to datetime type
    df_capital.rename(columns={"Country": "country"}, inplace=True)

    # Step 5 : Merge the two DataFrames on the column 'country'
    df_out = pd.merge(dataset, df_capital, how="left", on="country")

    # Step 6 : Transform the datetime column to datetime type
    df_out["time"] = pd.to_datetime(df_out["time"], errors="coerce")

    # Step 7 : Create a new column with the formatted date 'year_month_day'
    df_out["time"] = df_out["time"].dt.strftime("%Y-%m-%d")

    # Step 8 : Select only the useful columns
    usefull_columns = [
        "time",
        "country",
        "Capital City",
        "Latitude",
        "Longitude",
        "Population",
        "count_over_18",
        "count_is_original_content",
        "count_num_comments",
        "count_score",
        "avg_num_comments",
        "avg_score",
        "avg_upvote_ratio",
    ]
    df_out = df_out[usefull_columns].drop_duplicates().reset_index()

    # step 9 : return the dataframe
    return df_out

def load(ti) -> None:
    """
    Load a DataFrame into Supabase
    :param ti: task instance
    :return: None
    """

    ########################################
    # Initialization
    ########################################

    # Step 1: Get credentials
    credentials: dict = get_credentials()

    # Step 2: Setting up SUPABASE variables
    url: str = credentials["SUPABASE"]["URL"]
    key: str = credentials["SUPABASE"]["KEY"]
    random_email: str = credentials["SUPABASE"]["RANDOM_EMAIL"]
    random_password: str = credentials["SUPABASE"]["RANDOM_PASSWORD"]

    # Step 3: Create a Supabase Object
    supabase: Client = create_client(url, key)
    user = supabase.auth.sign_up({"email": random_email, "password": random_password})
    user = supabase.auth.sign_in_with_password(
        {"email": random_email, "password": random_password}
    )

    ########################################
    # Load
    ########################################

    # Step 0 : Get the transformed DataFrame
    df: DataFrame = ti.xcom_pull(task_ids="transform")

    # Step 1 : Drop the table if it exists
    drop_table("reddit_european_analysis", supabase)

    # Step 2 : Create the table of raw data
    for index, row in df.iterrows():
        data = (
            supabase.table("reddit_european_analysis")
            .insert(
                {
                    "time": str(row["time"]),
                    "country": str(row["country"]),
                    "Capital City": str(row["Capital City"]),
                    "Latitude": float(row["Latitude"]),
                    "Longitude": float(row["Longitude"]),
                    "Population": int(row["Population"]),
                    "count_over_18": int(row["count_over_18"]),
                    "count_is_original_content": int(row["count_is_original_content"]),
                    "count_num_comments": int(row["count_num_comments"]),
                    "count_score": int(row["count_score"]),
                    "avg_num_comments": float(row["avg_num_comments"]),
                    "avg_score": float(row["avg_score"]),
                    "avg_upvote_ratio": float(row["avg_upvote_ratio"]),
                }
            )
            .execute()
        )

default_args = {
    "owner": "ilyes_djerfaf",
    "retry": 5,
    "retry_delay": timedelta(minutes=5),
}

from airflow.operators.python import PythonOperator

with DAG(
    default_args=default_args,
    dag_id="ETL_reddit_analysis",
    start_date=datetime(2024, 1, 14),
    schedule="@weekly",
    catchup=False,
    tags=[
        "reddit",
        "supabase",
        "praw",
        "airflow",
        "python",
        "europe",
        "data",
        "analysis",
        "data-engineering",
    ],
) as dag:
    extract = PythonOperator(
        task_id="extract",
        python_callable=extract,
        dag=dag,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform,
        dag=dag,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load,
        dag=dag,
    )

    extract >> transform >> load
