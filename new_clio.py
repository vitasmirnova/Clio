# Importing necessary libraries
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Setting a title
st.title('Clio Reports Analyzer')

# Function to convert DataFrame to CSV bytes


def convert_df_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')


# Uploading Revenue Report
RR_csv = st.file_uploader("Upload a CSV 'Revenue report'", type=["csv"])
if RR_csv is not None:
    st.success("File uploaded successfully!")

    # Read the uploaded CSV file into a DataFrame
    RR = pd.read_csv(RR_csv)

# Uploading Matter Productivity By User
MP_csv = st.file_uploader(
    "Upload a CSV 'Matter Productivity By User'", type=["csv"])
if MP_csv is not None:
    st.success("File uploaded successfully!")

    # Read the uploaded CSV file into a DataFrame
    MP = pd.read_csv(MP_csv)

# Creating Data Editor for Revenue Report
st.subheader('Data Editor (Revenue Report)')
new_RR = st.data_editor(RR, num_rows='dynamic', hide_index=False)

# Creating a button to save the edited DataFrame to a new CSV file
csv = convert_df_to_csv_bytes(new_RR)
st.download_button("Press to download the edited CSV", csv,
                   "RR_edited.csv", "text/csv", key='download-csv')

# Add separate Data Viewer to view data without editing it
st.subheader('Data Viewer (Revenue Report)')
st.write(new_RR)

# Charting data
st.header('Charts')

# Chart 1: Revenue by Practice Area
st.subheader("Revenue by Practice Area")
fig = px.bar(new_RR, x='Practice Area', y='USD_collected_time',
             title='Revenue Analysis by Practice Area',
             labels={'USD_collected_time': 'Total Revenue',
                     'Practice Area': 'Practice Area'},
             color="Practice Area", color_discrete_sequence=px.colors.qualitative.G10)
st.plotly_chart(fig, use_container_width=True)

# Chart 2: Currency Distribution
st.subheader("Currency Distribution")
currency_distribution = new_RR.groupby(
    'Currency')['USD_collected_time'].sum().reset_index()
fig = px.pie(currency_distribution, names='Currency', values='USD_collected_time',
             title='Currency Distribution of Collected Revenue', hole=0.3)
st.plotly_chart(fig, use_container_width=True)

# Chart 3: Client's contribution to collected time
st.subheader("Client's contribution to collected time")
n = st.slider("Pick a %", 0, 100, value=20, step=5)/100
client_contribution = new_RR.groupby(
    'Client')['USD_collected_time'].sum().reset_index()
total_revenue = client_contribution['USD_collected_time'].sum()
top_clients = client_contribution.sort_values(
    'USD_collected_time', ascending=False).head(int(len(client_contribution) * n))
other_clients = client_contribution[~client_contribution['Client'].isin(
    top_clients['Client'])]
other_clients = pd.DataFrame({'Client': ['Other'], 'USD_collected_time': [
                             other_clients['USD_collected_time'].sum()]})
grouped_data = pd.concat([top_clients, other_clients])
fig = px.pie(grouped_data, names='Client', values='USD_collected_time',
             title=f'Top {round(n*100)}% Clients Contribution to Revenue', hole=0.3)
st.plotly_chart(fig, use_container_width=True)

# Working with MP
# Remove unnecessary columns
MP = MP.drop(columns=['Activity Type', 'Description', 'Rate', 'Total',
             'Invoice Number', 'Invoice Status', 'Invoice Last Payment Date'])
MP['user_total_hours'] = MP['User'].map(MP.groupby('User')['Quantity'].sum())
MP['matter_prct_of_total_time'] = MP['Quantity'] / MP['user_total_hours']
MP['matter_cost_in_salary'] = MP['user_salary'] * \
    MP['matter_prct_of_total_time']

# Creating Data Editor for Matter Productivity by User
st.subheader('Data Editor (Matter Productivity by User)')
MP = st.data_editor(MP, num_rows='dynamic', hide_index=False)

st.subheader('Data Viewer (Matter Productivity by User)')
st.write(MP)

# Chart 0: Users Salary Allocations by Practice Area
b = MP.groupby(['Practice Area', 'User'])[
    'matter_cost_in_salary'].sum().reset_index()
fig = px.bar(b, x='Practice Area', y='matter_cost_in_salary', title='Users Salary Allocations by Practice Area',
             hover_data=['User'], labels={'matter_cost_in_salary': 'Cost in Salary', 'Practice Area': 'Practice Area'})
st.plotly_chart(fig, use_container_width=True)

# Chart 0: Users Salary Allocations by Practice Area vs Collected Time
st.header('Margin Analysis')
no_partners = st.checkbox("Don't consider RB and EK salaries")

if no_partners:
    b = MP.copy()
    b.loc[(b['User'] == 'Roman Buzko') | (b['User'] ==
                                          'Evgeny Krasnov'), 'matter_cost_in_salary'] = 0
    b = b.groupby('Practice Area')['matter_cost_in_salary'].sum().reset_index()
else:
    b = MP.groupby('Practice Area')[
        'matter_cost_in_salary'].sum().reset_index()

a = new_RR.groupby(['Practice Area'])['USD_collected_time'].sum()
a = a.to_frame()
a_dict = a.to_dict()['USD_collected_time']
b['USD_collected_time'] = b['Practice Area'].map(a_dict)
b['Margin, %'] = (b['USD_collected_time'] -
                  b['matter_cost_in_salary']) / b['USD_collected_time'] * 100

# Create a grouped bar chart
fig = go.Figure()
fig.add_trace(go.Bar(x=b['Practice Area'], y=b['matter_cost_in_salary'],
              name='Cost in Salary', marker_color='red'))
fig.add_trace(go.Bar(x=b['Practice Area'], y=b['USD_collected_time'],
              name='Collected Time', marker_color='rgb(26, 100, 255)'))
fig.update_layout(barmode='group', title='Cost in Salary and Collected Time')
st.plotly_chart(fig, use_container_width=True)

# Display the DataFrame
st.write(b)

# Hours Analysis
st.subheader("Hours Analysis")

# Chart 1: Users' Hours by Practice Area
grouped_data = MP.groupby(['Practice Area', 'User'])[
    'Quantity'].sum().reset_index()
fig = px.bar(grouped_data, x='Practice Area', y='Quantity', color='User', barmode='stack',
             title="Users' Hours by Practice Area", labels={'Quantity': 'Hours'})
st.plotly_chart(fig, use_container_width=True)

# Chart 2: Hours Per Month
a = MP.copy()
a['Date'] = pd.to_datetime(a['Date'], format='%d/%m/%Y')
a['Month'] = a['Date'].dt.to_period('M')
a['Month'] = a['Month'].astype(str)
cumulative_data = a.groupby('Month')['Quantity'].sum().reset_index()
fig = px.bar(cumulative_data, x='Month', y='Quantity',
             labels={'Quantity': 'Cumulative Hours'})
fig.update_layout(title='Hours Per Month')
st.plotly_chart(fig, use_container_width=True)


# # import matplotlib.pyplot as plt
# # from wordcloud import WordCloud
# # from openai import OpenAI
# import plotly.graph_objs as go
# from plotly.subplots import make_subplots
# import pandas as pd
# import streamlit as st
# import plotly.express as px
# # import streamlit_pandas as sp

# # Setting a title
# st.title('Clio reports analyser')

# # Uploading Revenue Report
# RR_csv = st.file_uploader(
#     "Upload a a CSV 'Revenue report'", type=["csv"])
# if RR_csv is not None:
#     st.success("File uploaded successfully!")

#     # Read the uploaded CSV file into a DataFrame
#     RR = pd.read_csv(RR_csv)

# # Uploading Matter Productivity By User
# MP_csv = st.file_uploader(
#     "Upload a a CSV 'Matter Productivity By User'", type=["csv"])
# if MP_csv is not None:
#     st.success("File uploaded successfully!")

#     # Read the uploaded CSV file into a DataFrame
#     MP = pd.read_csv(MP_csv)


# # Creating Data Editor
# st.subheader('Data Editor (Revenue Report)')
# new_RR = st.data_editor(RR, num_rows='dynamic', hide_index=False)

# # Creating a button to save the edited DataFrame to a new CSV file


# def convert_df(df):
#     return df.to_csv(index=False).encode('utf-8')


# csv = convert_df(new_RR)

# st.download_button(
#     "Press to download the edited CSV",
#     csv,
#     "RR_edited.csv",
#     "text/csv",
#     key='download-csv'
# )


# # Add separate Data Viewer to view data without editing it
# st.subheader('Data Viewer (Revenue Report)')
# st.write(new_RR)

# # Charting data
# st.header('Charts')

# # Chart 1: Revenue by Practice Area, MAIN

# st.subheader("Revenue by Practice Area")
# fig = px.bar(new_RR, x='Practice Area', y='USD_collected_time',
#              title='Revenue Analysis by Practice Area',
#              labels={'USD_collected_time': 'Total Revenue',
#                      'Practice Area': 'Practice Area'},
#              color="Practice Area",
#              color_discrete_sequence=px.colors.qualitative.G10)

# st.plotly_chart(fig, use_container_width=True)

# # Chart 2: Currency Distribution
# st.subheader("Currency Distribution")

# currency_distribution = new_RR.groupby(
#     'Currency')['USD_collected_time'].sum().reset_index()
# fig = px.pie(
#     currency_distribution,
#     names='Currency',
#     values='USD_collected_time',
#     title='Currency Distribution of Collected Revenue',
#     hole=0.3,  # Set to 0 for a pie chart or adjust for a donut chart
# )
# st.plotly_chart(fig, use_container_width=True)


# # Chart 3: Client's contribution to collected time

# st.subheader("Client's contribution to collected time")

# #  title='Top 20% Clients Contribution to Revenue
# n = st.slider("Pick a %", 0, 100, value=20, step=5)/100

# # Group by client and sum the collected time
# client_contribution = new_RR.groupby(
#     'Client')['USD_collected_time'].sum().reset_index()

# # Calculate the total revenue
# total_revenue = client_contribution['USD_collected_time'].sum()

# # Sort clients by contribution and select the top 10%
# top_clients = client_contribution.sort_values(
#     'USD_collected_time', ascending=False).head(int(len(client_contribution) * n))

# # Group the remaining clients as 'Other'
# other_clients = client_contribution[~client_contribution['Client'].isin(
#     top_clients['Client'])]
# other_clients = pd.DataFrame({'Client': ['Other'], 'USD_collected_time': [
#                              other_clients['USD_collected_time'].sum()]})

# # Concatenate top clients and 'Other'
# grouped_data = pd.concat([top_clients, other_clients])

# # Create a pie chart using Plotly Express
# fig = px.pie(
#     grouped_data,
#     names='Client',
#     values='USD_collected_time',
#     title=f'Top {round(n*100)}% Clients Contribution to Revenue',
#     hole=0.3,  # Set to 0 for a pie chart or adjust for a donut chart
# )

# st.plotly_chart(fig, use_container_width=True)

# # Working with MP


# # Users' Hours by Practice Area

# MP = MP.drop(columns=['Activity Type', 'Description', 'Rate',
#                       'Total', 'Invoice Number', 'Invoice Status', 'Invoice Last Payment Date'])

# MP['user_total_hours'] = MP['User'].map(
#     MP.groupby('User')['Quantity'].sum())

# MP['matter_prct_of_total_time'] = MP['Quantity'] / MP['user_total_hours']

# MP['matter_cost_in_salary'] = MP['user_salary'] * \
#     MP['matter_prct_of_total_time']

# # Creating Data Editor
# st.subheader('Data Editor (Matter Productivity by User)')
# MP = st.data_editor(MP, num_rows='dynamic', hide_index=False)

# st.subheader('Data Viewer (Matter Productivity by User)')
# st.write(MP)


# # Chart 0: Users Salary Allocations by Practice Area, MAIN
# b = MP.groupby(['Practice Area', 'User'])[
#     'matter_cost_in_salary'].sum().reset_index()
# fig = px.bar(b, x='Practice Area', y='matter_cost_in_salary', title='Users Salary Allocations by Practice Area',
#              hover_data=['User'], labels={'matter_cost_in_salary': 'Cost in Salary', 'Practice Area': 'Practice Area'})

# st.plotly_chart(fig, use_container_width=True)


# # Chart 0: Users Salary Allocations by Practice Area vs Collected Time, MAIN 2
# st.header('Margin Analysis')

# no_partners = st.checkbox("Don't consider RB and EK salaries")


# if no_partners:
#     b = MP.copy()
#     b.loc[(b['User'] == 'Roman Buzko') | (b['User'] ==
#                                           'Evgeny Krasnov'), 'matter_cost_in_salary'] = 0
#     b = b.groupby('Practice Area')[
#         'matter_cost_in_salary'].sum().reset_index()

# else:

#     b = MP.groupby('Practice Area')[
#         'matter_cost_in_salary'].sum().reset_index()

# a = new_RR.groupby(['Practice Area'])['USD_collected_time'].sum()
# a = a.to_frame()
# a_dict = a.to_dict()['USD_collected_time']


# b['USD_collected_time'] = b['Practice Area'].map(a_dict)

# b['Margin, %'] = (b['USD_collected_time'] -
#                   b['matter_cost_in_salary'])/b['USD_collected_time'] * 100


# fig = go.Figure()
# fig.add_trace(go.Bar(
#     x=b['Practice Area'],
#     y=b['matter_cost_in_salary'],
#     name='Cost in Salary',
#     marker_color='red'
# ))
# fig.add_trace(go.Bar(
#     x=b['Practice Area'],
#     y=b['USD_collected_time'],
#     name='Collected Time',
#     marker_color='rgb(26, 100, 255)'
# ))


# # Here we modify the tickangle of the xaxis, resulting in rotated labels.
# fig.update_layout(barmode='group', title='Cost in Salary and Collected Time')
# st.plotly_chart(fig, use_container_width=True)

# st.write(b)

# st.subheader("Hours Analysis")

# # Chart 1: Users' Hours by Practice Area
# grouped_data = MP.groupby(['Practice Area', 'User'])[
#     'Quantity'].sum().reset_index()

# fig = px.bar(
#     grouped_data,
#     x='Practice Area',
#     y='Quantity',
#     color='User',
#     barmode='stack',
#     title="Users' Hours by Practice Area",
#     labels={'Quantity': 'Hours'},
# )
# st.plotly_chart(fig, use_container_width=True)


# # Chart 2: Hours Per Month
# a = MP.copy()
# a['Date'] = pd.to_datetime(a['Date'], format='%d/%m/%Y')

# # Extract month and year from 'Date'
# a['Month'] = a['Date'].dt.to_period('M')
# a['Month'] = a['Month'].astype(str)

# # Group by 'Month' and calculate the cumulative sum of 'Quantity'
# cumulative_data = a.groupby('Month')['Quantity'].sum().reset_index()

# # Create a cumulative line graph using Plotly Express
# fig = px.bar(cumulative_data, x='Month', y='Quantity',
#              labels={'Quantity': 'Cumulative Hours'})
# fig.update_layout(title='Hours Per Month')
# st.plotly_chart(fig, use_container_width=True)


# #добавить формат чисел в табличках
