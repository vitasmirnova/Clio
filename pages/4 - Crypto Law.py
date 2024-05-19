from st_files_connection import FilesConnection
# import pandas as pd
import streamlit as st
# import plotly.express as px
# import plotly.graph_objs as go
from custom_functions import *

#######################################
# PAGE SETUP
#######################################

st.set_page_config(
    page_title='BK reporting',
    layout='wide'
)

# Setting a title
st.title('Clio Reports Analyzer')
st.subheader('Crypto Law report')

# Create connection object and retrieve file contents.
conn = st.connection('gcs', type=FilesConnection)

#######################################
# PERIOD SPECIFICATION
#######################################


folder_path = "clio-reports"

# Access the FileSystem object API
fs = conn.fs

# List all files within the folder
period_folders_list = fs.ls(folder_path)

# st.write(period_folders_list)

# Get rid of the bucket path
periods_list = []
for folder in period_folders_list:
    periods_list.append(folder.split('/')[1])
# st.write(periods_list)

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
    st.write(RR)

    st.subheader('Data Viewer (Matter Productivity by User)')
    st.write(MP)
