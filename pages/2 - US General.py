from st_files_connection import FilesConnection
import streamlit as st
from custom_functions import *

#######################################
# PAGE SETUP
#######################################

# !! This section is modified for every practice

st.set_page_config(
    page_title='BK reporting – US General',
    layout='wide'
)

# Setting a title
st.title('Clio Reports Analyzer')
st.subheader('US General practice report')

#######################################
# AUTHENTIFICATION
#######################################

# !! This section is modified for every practice

page_allowed_emails = st.secrets["us_general_emails"] + \
    st.secrets["management_emails"]

# Debugging lines
# st.write(st.experimental_user.email)
# st.write(page_allowed_emails)

# Stops the app if the email is not in the allowed list
authenticate(st.experimental_user.email, page_allowed_emails)

# Create connection object and retrieve file contents.
conn = st.connection('gcs', type=FilesConnection)

# st.info('TBA')
# st.stop()

#######################################
# PRACTICE FOLDER PATH, CURRENCY
#######################################

# !! This section is modified for every practice

folder_path = "clio-reports/us_general"

revenue_column = 'USD Collected Time'
salary_column = 'Matter Cost in Salary'
currency_label = ' USD'

#######################################
# PERIOD AND DATA LOADING FROM CLOUD
#######################################

# Get available periods
periods_list = create_periods_list(conn, folder_path)

# Independent dropdowns
years = [2025, 2026]
quarters = ["Q1", "Q2", "Q3", "Q4"]

selected_year = st.selectbox(
    "Select year:", years, index=years.index(2025))   # preselect 2025
selected_quarter = st.selectbox(
    "Select quarter:", quarters, index=quarters.index("Q3"))  # preselect Q3

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

#######################################
# DATA VIEWING
#######################################

with st.expander("Data Viewer"):
    # Add separate Data Viewer to view data without editing it
    st.subheader('Data Viewer (Revenue Report)')
    st.write(RR)  # было new_RR когда было с Editor

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
        plot_chart_salary_and_collected_time(
            mt, salary_column, revenue_column, currency_label)

with middle_right_line:
    with st.container(border=True):
        show_margin_table(mt, salary_column,
                          revenue_column, currency_label)

client_contribution(RR, revenue_column)

hours_by_practice(MP)
