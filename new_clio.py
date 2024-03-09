"""
Run with `streamlit run new_clio.py`
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go

#######################################
# PAGE SETUP
#######################################

st.set_page_config(
    page_title='BK reporting',
    layout='wide'
)

# Setting a title
st.title('Clio Reports Analyzer')

# Function to convert DataFrame to CSV bytes
def convert_df_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

#######################################
# DATA LOADING
#######################################

with st.expander('Data Upload'):
    RR_csv = st.file_uploader("Upload a CSV 'Revenue report'", type=["csv"])
    if RR_csv is not None:
        st.success("File uploaded successfully!")
        # Read the uploaded CSV file into a DataFrame
        RR = pd.read_csv(RR_csv)
    else:
        st.info('Upload a file', icon='ℹ️')
        st.stop()

    # Uploading Matter Productivity By User
    MP_csv = st.file_uploader(
        "Upload a CSV 'Matter Productivity By User'", type=["csv"])
    if MP_csv is not None:
        st.success("File uploaded successfully!")

        # Read the uploaded CSV file into a DataFrame
        MP = pd.read_csv(MP_csv)
    else:
        st.info('Upload a file', icon='ℹ️')
        st.stop()

with st.expander("Data Editor"):
# Creating Data Editor for Revenue Report
    st.subheader('Data Editor (Revenue Report)')
    new_RR = st.data_editor(RR, num_rows='dynamic', hide_index=False)

    # Creating a button to save the edited DataFrame to a new CSV file
    csv = convert_df_to_csv_bytes(new_RR)
    st.download_button("Press to download the edited CSV", csv,
                    "RR_edited.csv", "text/csv", key='download-csv')

    #ТУТ НУЖНА ПЕРЕЗАПИСЬ MP Creating Data Editor for Matter Productivity by User
    st.subheader('Data Editor (Matter Productivity by User)')
    MP = st.data_editor(MP, num_rows='dynamic', hide_index=False)
    csv2 = convert_df_to_csv_bytes(MP)
    st.download_button("Press to download the edited CSV", csv2,
                    "MP_edited.csv", "text/csv", key='download-csv2')

with st.expander("Data Viewer"):
    # Add separate Data Viewer to view data without editing it
    st.subheader('Data Viewer (Revenue Report)')
    st.write(new_RR)

    st.subheader('Data Viewer (Matter Productivity by User)')
    st.write(MP)


st.title('Dashboard')

#######################################
# VIZUALIZATION METHODS AND FUNCTIONS
#######################################

def plot_metric(label, value, prefix="", suffix=""):
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            value=value,
            gauge={"axis": {"visible": False}},
            number={
                "prefix": prefix,
                "suffix": suffix,
                "font.size": 28,
            },
            title={
                "text": label,
                "font": {"size": 24},
            },
        )
    )

    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)
    fig.update_layout(
        # paper_bgcolor="lightgrey",
        margin=dict(t=30, b=0),
        showlegend=False,
        plot_bgcolor="white",
        height=100,
    )

    st.plotly_chart(fig, use_container_width=True)

def create_margin_table(RR=RR, MP=MP):
    temp = RR.groupby(['Practice Area'], dropna=False)['USD Collected Time'].sum()
    temp = temp.to_frame()
    temp_dict = temp.to_dict()['USD Collected Time']

    margin_table = MP.groupby(['Practice Area'], dropna=False)[
        'Matter Cost in Salary'].sum().reset_index()

    margin_table['USD Collected Time'] = margin_table['Practice Area'].map(temp_dict)
    margin_table['Margin, %'] = (margin_table['USD Collected Time'] -
                    margin_table['Matter Cost in Salary']) / margin_table['USD Collected Time'] * 100
    return margin_table

def plot_chart_salary_and_collected_time(margin_table):
    # st.write('Cost in Salary and Collected Time by Practice')
    # Create a bar chart from margin table
    fig = go.Figure()
    fig.add_trace(go.Bar(x=margin_table['Practice Area'], 
                         y=margin_table['Matter Cost in Salary'], 
                         name='Cost in Salary', 
                         marker_color='red'))
    fig.add_trace(go.Bar(x=margin_table['Practice Area'], 
                         y=margin_table['USD Collected Time'],
                         name='Collected Time', 
                         marker_color='rgb(26, 100, 255)'))
    fig.update_layout(barmode='group', title='Cost in Salary and Collected Time by Practice',
                      legend=dict(y=1.1, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)

def show_margin_table(margin_table):
    st.write(' ')
    st.write(' ')
    st.write('' )

    margin_table['Margin, %'] = margin_table['Margin, %'].map('{:.2f}%'.format)
    margin_table['Matter Cost in Salary'] = margin_table['Matter Cost in Salary'].map(
        '{:,.0f}'.format).astype('str').str.replace(',', ' ')
    margin_table['USD Collected Time'] = margin_table['USD Collected Time'].map(
        '{:,.0f}'.format).astype('str').str.replace(',', ' ')
    margin_table.rename(
        columns={'Matter Cost in Salary': 'Practice Cost in Salary'}, inplace = True)
    
    st.dataframe(margin_table, hide_index=True, use_container_width=True)

def client_contribution(RR):
    st.write('')
    st.write('')
    st.markdown("**Client's contribution to collected time**")
    n = st.slider("Pick a %", 0, 100, value=20, step=5)/100
    client_contribution = RR.groupby(
        'Client')['USD Collected Time'].sum().reset_index()
    top_clients = client_contribution.sort_values(
        'USD Collected Time', ascending=False).head(int(len(client_contribution) * n))
    other_clients = client_contribution[~client_contribution['Client'].isin(
        top_clients['Client'])]
    other_clients = pd.DataFrame({'Client': ['Other'], 'USD Collected Time': [
        other_clients['USD Collected Time'].sum()]},)
    grouped_data = pd.concat([top_clients, other_clients])
    fig = px.pie(grouped_data, names='Client', values='USD Collected Time',
                title=f'Top {round(n*100)}% Clients Contribution to Revenue', hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

def hours_by_practice(MP):
    grouped_data = MP.groupby(['User', 'Practice Area'])[
        'Quantity'].sum().reset_index()
    fig = px.bar(grouped_data, x='Quantity', y='User', color='Practice Area', barmode='stack',
                title="Users' Hours Allocation", labels={'Quantity': 'Hours', 'User' : ''}, height = 622)
    st.plotly_chart(fig, use_container_width=True)

#######################################
# GETTING DATA THAT IS USED LATER
#######################################
    
mt = create_margin_table(RR=RR, MP=MP)
total_collected_time = mt['USD Collected Time'].sum()
total_salaries = mt['Matter Cost in Salary'].sum()

#######################################
# STREAMLIT LAYOUT AND PLOTTING
#######################################
top_left_line, top_right_line = st.columns((2, 2))
middle_left_line, middle_right_line = st.columns((2, 1.5), gap="medium")
lower_left_line, lower_right_line = st.columns(2, gap = "medium")

with top_left_line:
    with st.container(border=True):
        plot_metric("Total Collected Time", total_collected_time,
                    prefix="", suffix=" USD")
with top_right_line:
    with st.container(border=True):
        plot_metric("Total Salaries", total_salaries, prefix="", suffix=" USD")

with middle_left_line:
    with st.container(border=True):
        plot_chart_salary_and_collected_time(mt)

with middle_right_line:
     with st.container(border=True):
        show_margin_table(mt)

with lower_left_line:
    with st.container(border=True):
        client_contribution(RR)

with lower_right_line:
    with st.container(border=True):
        hours_by_practice(MP)
