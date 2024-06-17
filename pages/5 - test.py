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
st.title('Clio Reports')
st.subheader('Management report (Dynamic data)')

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



try:
    # Attempt to read Pickle data from GCS
    with conn.fs.open(f"{dynamic_folder_path}/{dynamic_file_name}", 'rb') as f:
        pkl_data = pickle.load(f)
    # If successful, display success message
    # st.success('Data retrieved from dynamic cloud')

except Exception as e:
    # If there's an exception (e.g., file not found, connection issue), handle it
    st.error(f'Error retrieving data: {e}')
    # Optionally, log the error for further investigation
    logging.error(f"Error retrieving data from GCS: {e}")

    # If not found, then the data is retrieved and written to the cloud
    logging.error(
        f"File with dynamic data is not found. Initiating data retrieval")
    plk_data = refresh_and_upload_data(periods_list, folder_path, revenue_column,
             salary_column, dynamic_folder_path, dynamic_file_name, conn)

if st.button('Refresh Data'):
    plk_data = refresh_and_upload_data(periods_list, folder_path, revenue_column,
                 salary_column, dynamic_folder_path, dynamic_file_name, conn)

a, b = pkl_to_two_dfs(pkl_data)
st.write(a, b)




