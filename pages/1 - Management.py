"""
Run with `streamlit run new_clio.py`
"""

from st_files_connection import FilesConnection
# import pandas as pd
import streamlit as st
# import plotly.express as px
# import plotly.graph_objs as go
from custom_functions import *

#######################################
# PAGE SETUP AND AUTHENTICATION
#######################################

st.set_page_config(
    page_title='BK reporting',
    layout='wide'
)

# Setting a title
st.title('Clio Reports Analyzer')
st.subheader('Management report')

page_allowed_emails = st.secrets["management_emails"]

# Debugging
# st.write(st.experimental_user.email)
# st.write(page_allowed_emails)

authenticate(st.experimental_user.email, page_allowed_emails) # stops the app if the email is not in the allowed list

# Create connection object and retrieve file contents.
conn = st.connection('gcs', type=FilesConnection)

#######################################
# PERIOD SPECIFICATION
#######################################

folder_path = "clio-reports"

periods_list = create_periods_list(conn, folder_path)
chosen_period = st.selectbox("Select period:", periods_list)

#######################################
# DATA LOADING (CLOUD VERSION)
#######################################

# Specify input format is a csv and to cache the result for 600 seconds.

MP = conn.read(
    f"clio-reports/{chosen_period}/MP_{chosen_period}.csv", input_format="csv", ttl=600)
RR = conn.read(
    f"clio-reports/{chosen_period}/RR_{chosen_period}.csv", input_format="csv", ttl=600)

#######################################
# DATA VIEWING
#######################################

with st.expander("Data Viewer"):
    # Add separate Data Viewer to view data without editing it
    st.subheader('Data Viewer (Revenue Report)')
    st.write(RR) #было new_RR когда было с Editor

    st.subheader('Data Viewer (Matter Productivity by User)')
    st.write(MP)


st.title('Dashboard')

#######################################
# CURRENCY CONTROL
#######################################

# ru_law_checkbox = st.checkbox('Russian Law', value=False)

# if ru_law_checkbox:
#     revenue_column = 'RUB Collected Time'
#     salary_column = 'RUB Matter Cost in Salary'
#     currency_label = ' RUB'
# else:
#     revenue_column = 'USD Collected Time'
#     salary_column = 'Matter Cost in Salary'
#     currency_label = ' USD'

revenue_column = 'USD Collected Time'
salary_column = 'Matter Cost in Salary'
currency_label = ' USD'


#######################################
# GETTING DATA THAT IS USED LATER
#######################################
try:
    mt = create_margin_table(RR, MP, revenue_column, salary_column)
except:
    st.info('Unselect the checkbox', icon='ℹ️')
    st.stop()
total_collected_time = mt[revenue_column].sum()
total_salaries = mt[salary_column].sum()

#######################################
# STREAMLIT LAYOUT AND PLOTTING
#######################################
top_left_line, top_right_line = st.columns((2, 2))
middle_left_line, middle_right_line = st.columns((1.8, 1.5), gap="medium")
lower_left_line, lower_right_line = st.columns(2, gap="medium")

with top_left_line:
    with st.container(border=True):
        plot_metric("Revenue", total_collected_time,
                    prefix="", suffix=currency_label)

with top_right_line:
    with st.container(border=True):
        plot_metric("Total Salaries", total_salaries,
                    prefix="", suffix=currency_label)

with middle_left_line:
    with st.container(border=True):
        plot_chart_salary_and_collected_time(mt, salary_column, revenue_column, currency_label)

with middle_right_line:
    with st.container(border=True):
        show_margin_table(mt, salary_column,
                          revenue_column, currency_label)

with lower_left_line:
    with st.container(border=True):
        client_contribution(RR, revenue_column)

with lower_right_line:
    with st.container(border=True):
        hours_by_practice(MP)
