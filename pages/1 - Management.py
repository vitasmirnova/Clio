"""
When a new practice report is being coded, it is neccessary to modify the first three sections in this file
"""

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

# if st.experimental_user.is_logged_in:
#     st.write(st.experimental_user)

page_allowed_emails = st.secrets["management_emails"]

# Debugging lines
# st.write(st.experimental_user.email)
# st.write(page_allowed_emails)

authenticate(st.experimental_user.email, page_allowed_emails) # Stops the app if the email is not in the allowed list

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

# Get available periods
periods_list = create_periods_list(conn, folder_path)

# Independent dropdowns
years = [2024, 2025, 2026]
quarters = ["Q1", "Q2", "Q3", "Q4"]

selected_year = st.selectbox(
    "Select year:", years, index=years.index(2025))   # preselect 2025
selected_quarter = st.selectbox(
    "Select quarter:", quarters, index=quarters.index("Q4"))  # preselect Q4

chosen_period = f"{selected_quarter}_{selected_year}"

# Check if this period actually exists in cloud data
if chosen_period not in periods_list:
    st.warning("No data available for this period")
    st.stop()
else:
    # Load from cloud
    MP = conn.read(
        f"{folder_path}/{chosen_period}/MP_{chosen_period}.csv",
        input_format="csv",
        ttl=600
    )
    RR = conn.read(
        f"{folder_path}/{chosen_period}/RR_{selected_quarter}_{selected_year}.csv",
        input_format="csv",
        ttl=600
    )

# # Get the desired period
# periods_list = create_periods_list(conn, folder_path)
# chosen_period = st.selectbox("Select period:", periods_list)

# # Load data from the cloud


# MP = conn.read(
#     f"{folder_path}/{chosen_period}/MP_{chosen_period}.csv", input_format="csv", ttl=600)
# RR = conn.read(
#     f"{folder_path}/{chosen_period}/RR_{chosen_period}.csv", input_format="csv", ttl=600)

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
# GETTING DATA THAT IS USED LATER
#######################################

try:
    mt = create_margin_table(RR, MP, revenue_column, salary_column)
except:
    st.info('Something went wrong (MT)', icon='ℹ️')
    st.stop()
total_collected_time = mt[revenue_column].sum()
total_salaries = mt[salary_column].sum()

#######################################
# STREAMLIT LAYOUT AND PLOTTING
#######################################

top_left_line, top_right_line = st.columns((2, 2))
middle_left_line, middle_right_line = st.columns((1.8, 1.5), gap="medium")
# lower_left_line, lower_right_line = st.columns(2, gap="medium")

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


client_contribution(RR, revenue_column)


hours_by_practice(MP)


try:
    display_user_hours_table(MP)
except:
    st.info('No hours table avaliable', icon='ℹ️')