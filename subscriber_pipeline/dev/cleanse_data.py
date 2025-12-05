import sqlite3
import pandas as pd
import ast
import numpy as np
from sqlalchemy import create_engine
import logging

pd.options.mode.chained_assignment = None  # Disable SettingWithCopyWarning

logging.basicConfig(filename="./dev/cleanse_db.log",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filemode='w',
                    level=logging.DEBUG,
                    force=True)
logger = logging.getLogger(__name__)

def cleanse_student_table(df):
    """
    Cleanse the `cademycode_students` table according to the discoveries made in the writeup
    Parameters:
        df (DataFrame): `student` table from `cademycode.db`
    Returns:
        df (DataFrame): Cleansed `student` table
        missing_data (DataFrame): incomplete records removed from `student` table for later inspection
    """
    now = pd.to_datetime("now")
    dob = pd.to_datetime(df['dob'])
    df['age'] = (now.year - dob.dt.year) - (
    (now.month < dob.dt.month) | ((now.month == dob.dt.month) & (now.day < dob.dt.day)))
    df['age_group'] = np.int64((df['age']/10))*10

    df['contact_info'] = df['contact_info'].apply(lambda x: ast.literal_eval(x))
    explode_contact = pd.json_normalize(df['contact_info'])
    df = pd.concat([df.drop('contact_info', axis=1).reset_index(drop=True), explode_contact], axis=1)

    split_address = df.mailing_address.str.split(',', expand=True)
    split_address.columns = ['street', 'city', 'state', 'zip_code']
    df = pd.concat([df.drop('mailing_address', axis=1), split_address], axis=1)

    df['job_id'] = df['job_id'].astype(float)
    df['current_career_path_id'] = df['current_career_path_id'].astype(float)
    df['num_course_taken'] = df['num_course_taken'].astype(float)
    df['time_spent_hrs'] = df['time_spent_hrs'].astype(float)

    missing_data = pd.DataFrame()
    missing_course_taken = df[df[['num_course_taken']].isnull().any(axis=1)]
    missing_data = pd.concat([missing_data, missing_course_taken])
    df = df.dropna(subset=['num_course_taken'])

    missing_job_id = df[df[['job_id']].isnull().any(axis=1)]
    missing_data = pd.concat([missing_data, missing_job_id])
    df = df.dropna(subset=['job_id'])

    df['current_career_path_id'] = np.where(df['current_career_path_id'].isnull(), 0, df['current_career_path_id'])
    df['time_spent_hrs'] = np.where(df['time_spent_hrs'].isnull(), 0, df['time_spent_hrs'])

    return(df, missing_data)
