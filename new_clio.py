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

    # ТУТ НУЖНА ПЕРЕЗАПИСЬ MP Creating Data Editor for Matter Productivity by User
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
# CURRENCY CONTROL
#######################################

ru_law_checkbox = st.checkbox('Russian Law', value=False)

if ru_law_checkbox:
    revenue_column = 'RUB Collected Time'
    salary_column = 'RUB Matter Cost in Salary'
    currency_label = ' RUB'
else:
    revenue_column = 'USD Collected Time'
    salary_column = 'Matter Cost in Salary'
    currency_label = ' USD'

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


def create_margin_table(RR, MP, revenue_column, salary_column):
    temp = RR.groupby(['Practice Area'], dropna=False)[revenue_column].sum()
    temp = temp.to_frame()
    temp_dict = temp.to_dict()[revenue_column]

    margin_table = MP.groupby(['Practice Area'], dropna=False)[
        salary_column].sum().reset_index()

    margin_table[revenue_column] = margin_table['Practice Area'].map(temp_dict)
    margin_table['Margin, %'] = (margin_table[revenue_column] -
                                 margin_table[salary_column]) / margin_table[revenue_column] * 100

    margin_table['x2 Salary'] = 2 * margin_table[salary_column]

    margin_table['Delta of Revenue and x2 Salary'] = margin_table[revenue_column] - \
        margin_table['x2 Salary']

    return margin_table


def plot_chart_salary_and_collected_time(margin_table):
    # Create a bar chart from margin table
    fig = go.Figure()
    fig.add_trace(go.Bar(x=margin_table['Practice Area'],
                         y=margin_table[salary_column] * 2,
                         name=f'2x Cost in Salary,{currency_label}',
                         marker_color='red'))
    fig.add_trace(go.Bar(x=margin_table['Practice Area'],
                         y=margin_table[revenue_column],
                         name=f'Revenue,{currency_label}',
                         marker_color='rgb(26, 100, 255)'))
    fig.update_layout(barmode='group', title='Cost in Salary and Revenue by Practice',
                      legend=dict(y=1.1, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)


def show_margin_table(margin_table):
    st.write(' ')
    st.write(' ')
    st.write('')

    # margin_table['Margin, %'] = margin_table['Margin, %']
    # margin_table[salary_column] = margin_table[salary_column]
    # margin_table[revenue_column] = margin_table[revenue_column]
    # margin_table['x2 Salary'] = margin_table['x2 Salary']
    # margin_table['Delta of Revenue and x2 Salary'] = margin_table['Delta of Revenue and x2 Salary']

# не получается пока формат как я хочу
    format_config = {
        'Margin, %': st.column_config.NumberColumn(format="%.2f"),
        salary_column: st.column_config.NumberColumn(label=f'Practice Cost in Salary,{currency_label}', format="%.0f"),
        revenue_column: st.column_config.NumberColumn(label=f'Revenue,{currency_label}', format="%.0f"),
        'x2 Salary': st.column_config.NumberColumn(format="%.0f"),
        'Delta of Revenue and x2 Salary': st.column_config.NumberColumn(format="%.0f")
    }

    # margin_table.rename(
    #     columns={revenue_column: f'Revenue,{currency_label}'}, inplace=True)

    st.dataframe(margin_table, hide_index=True,
                 use_container_width=True, column_config=format_config)


def client_contribution(RR):
    st.write('')
    st.write('')
    st.markdown("**Client's contribution to collected time**")
    n = st.slider("Pick a %", 0, 100, value=20, step=5)/100
    client_contribution = RR.groupby(
        'Client')[revenue_column].sum().reset_index()
    top_clients = client_contribution.sort_values(
        revenue_column, ascending=False).head(int(len(client_contribution) * n))
    other_clients = client_contribution[~client_contribution['Client'].isin(
        top_clients['Client'])]
    other_clients = pd.DataFrame({'Client': ['Other'], revenue_column: [
        other_clients[revenue_column].sum()]},)
    grouped_data = pd.concat([top_clients, other_clients])
    fig = px.pie(grouped_data, names='Client', values=revenue_column,
                 title=f'Top {round(n*100)}% Clients Contribution to Revenue', hole=0.3)
    st.plotly_chart(fig, use_container_width=True)


def hours_by_practice(MP):
    grouped_data = MP.groupby(['User', 'Practice Area'])[
        'Quantity'].sum().reset_index()
    fig = px.bar(grouped_data, x='Quantity', y='User', color='Practice Area', barmode='stack',
                 title="Users' Hours Allocation", labels={'Quantity': 'Hours', 'User': ''}, height=622)
    st.plotly_chart(fig, use_container_width=True)


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
