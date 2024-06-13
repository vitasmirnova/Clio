"""
When a new practice report is being coded, it is neccessary to modify the first three sections in this file
"""

import logging
from st_files_connection import FilesConnection
import streamlit as st
from custom_functions import *

#######################################
# PAGE SETUP
#######################################

# !! This section is modified for every practice

st.set_page_config(
    page_title='BK reporting',
    layout='wide'
)

# Setting a title
st.title('Clio Reports Analyzer')
st.subheader('Management report')

#######################################
# AUTHENTIFICATION
#######################################

# !! This section is modified for every practice

page_allowed_emails = st.secrets["management_emails"]

# Debugging lines
# st.write(st.experimental_user.email)
# st.write(page_allowed_emails)

# Stops the app if the email is not in the allowed list
authenticate(st.experimental_user.email, page_allowed_emails)

# Create connection object and retrieve file contents.
conn = st.connection('gcs', type=FilesConnection)

#######################################
# PRACTICE FOLDER PATH, CURRENCY
#######################################

# !! This section is modified for every practice

folder_path = "clio-reports/management"

revenue_column = 'USD Collected Time'
salary_column = 'Matter Cost in Salary'
currency_label = ' USD'

#######################################
# PERIOD AND DATA LOADING FROM CLOUD
#######################################

# Get all the periods
periods_list = create_periods_list(conn, folder_path)


# как сделать динамику? надо по каждому периоду взять марджин тейбл. как ее хранить / генерить заранее может? и добавлять файл в облако? использовать кэш?
# попробую сейчас просто для двух периодов получить только таблички

# калькулируем таблички проходясь по каждому периоду. Оформляем общий динамичный фрейм (как?). Это все делается по нажатию кнопки рефреш. Если кнопку не жали, файл просто грузтся. 
# Если ошибка, рефреш идет автоматом.


# Configure logging
logging.basicConfig(level=logging.INFO)

# retrieved_data = {}

# for period in periods_list:
#     try:
#         MP = conn.read(
#             f"{folder_path}/{period}/MP_{period}.csv", input_format="csv", ttl=600)
#         RR = conn.read(
#             f"{folder_path}/{period}/RR_{period}.csv", input_format="csv", ttl=600)
#     except Exception as e:
#         st.info(
#             f'Something went wrong while reading data for period {period}: {e}', icon='ℹ️')
#         logging.error(f"Error reading data for period {period}: {e}")
#         continue  # Skip this period and continue with the next one

#     try:
#         mt = create_margin_table(RR, MP, revenue_column, salary_column)
#     except Exception as e:
#         st.info(
#             f'Something went wrong (MT) for period {period}: {e}', icon='ℹ️')
#         logging.error(f"Error creating margin table for period {period}: {e}")
#         continue  # Skip this period and continue with the next one

#     total_collected_time = mt[revenue_column].sum()
#     total_salaries = mt[salary_column].sum()

#     # plot_chart_salary_and_collected_time(
#     #     mt, salary_column, revenue_column, currency_label)

#     # Ensure the dictionary for this period is initialized
#     retrieved_data[period] = {}
#     retrieved_data[period]['margin_table'] = mt
#     retrieved_data[period]['total_salaries'] = total_salaries
#     retrieved_data[period]['total_collected_time'] = total_collected_time

# retrieved_data


def retrieve_data(periods_list, folder_path, conn, revenue_column, salary_column):
    retrieved_data = {}

    for period in periods_list:
        try:
            MP = conn.read(
                f"{folder_path}/{period}/MP_{period}.csv", input_format="csv", ttl=600)
            RR = conn.read(
                f"{folder_path}/{period}/RR_{period}.csv", input_format="csv", ttl=600)
        except Exception as e:
            st.info(
                f'Something went wrong while reading data for period {period}: {e}', icon='ℹ️')
            logging.error(f"Error reading data for period {period}: {e}")
            continue  # Skip this period and continue with the next one

        try:
            mt = create_margin_table(RR, MP, revenue_column, salary_column)
        except Exception as e:
            st.info(
                f'Something went wrong (MT) for period {period}: {e}', icon='ℹ️')
            logging.error(
                f"Error creating margin table for period {period}: {e}")
            continue  # Skip this period and continue with the next one

        total_collected_time = mt[revenue_column].sum()
        total_salaries = mt[salary_column].sum()

        # Ensure the dictionary for this period is initialized
        retrieved_data[period] = {}
        retrieved_data[period]['margin_table'] = mt
        retrieved_data[period]['total_salaries'] = total_salaries
        retrieved_data[period]['total_collected_time'] = total_collected_time

    return retrieved_data

if st.button('Refresh Data'):
    retrieved_data = retrieve_data(
        periods_list, folder_path, conn, revenue_column, salary_column)
    st.success("Data refreshed successfully!")

retrieved_data
