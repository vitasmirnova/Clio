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

folder_path = "clio-reports/management"
dynamic_folder_path = "clio-reports/dynamic"
dynamic_file_name = 'dynamic_data.pkl'

#######################################
# PERIOD AND DATA LOADING FROM CLOUD
#######################################

# Get all the periods
periods_list = create_periods_list(conn, folder_path)

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

full_table, short_table = pkl_to_two_dfs(pkl_data)

short_table = short_table.sort_values(
    by="quarter",
    key=lambda col: col.map(quarter_sort_key)
)

full_table = full_table.sort_values(
    by="quarter",
    key=lambda col: col.map(quarter_sort_key)
)
st.write(full_table.rename(columns={'Matter Cost in Salary': 'Cost in Salary'}))


#######################################
# VISUALISATION
####################################### 

# version of v3 with right sorting
visualize_cost_vs_collected_time_v5(
    full_table, salary_column='Matter Cost in Salary', collected_time_column='USD Collected Time')


st.write(short_table.rename(
    columns={'quarter': 'Quarter', 'total_collected_time': 'Revenue', 'total_salaries': 'Cost in Salary'}))

visualize_salaries_vs_revenue(
    short_table, revenue_column='total_collected_time', salary_column='total_salaries')

