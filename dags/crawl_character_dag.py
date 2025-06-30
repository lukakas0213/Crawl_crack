from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from docker.types import Mount
from datetime import datetime
import os
from dotenv import load_dotenv

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
}

load_dotenv()

CRAWLER_PATH = os.environ.get("CRAWLER_PATH")
DATA_PATH = os.environ.get("DATA_PATH")

if CRAWLER_PATH and DATA_PATH:
    with DAG(
        dag_id='crawl_character_dag',
        default_args=default_args,
        schedule_interval=None,
        catchup=False,
        description='크랙 캐릭터 크롤링 DAG',
    ) as dag:

        crawl = DockerOperator(
            task_id='run_character_crawler',
            image='airflow-crawler:latest',
            command='python /opt/airflow/crawler/crawl_get_info.py',
            docker_url='unix:///var/run/docker.sock',
            network_mode='airflow_net',
            auto_remove=True,
            tty=True,
            mount_tmp_dir=False,
            mounts=[
                Mount(source="/var/run/docker.sock", target="/var/run/docker.sock", type="bind"),
                Mount(source=CRAWLER_PATH, target="/opt/airflow/crawler", type="bind"),
                Mount(source=DATA_PATH, target="/opt/airflow/data", type="bind"),
            ]
        )
else:
    import logging
    logging.warning()
    dag = None
