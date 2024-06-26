
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import pickle
import logging

#######################################
# PAGE CONFIGURATION FUNCTIONS
#######################################

def convert_df_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')


def authenticate(user_email, allowed_emails):
    if user_email in allowed_emails:
        return True
    else:
        st.warning('You don\'t have access to this content')
        st.stop()

def create_periods_list(conn, path):
    fs = conn.fs
    period_folders_list = fs.ls(path)[1:]
    # st.write(period_folders_list) debug line

    periods_list = []

    for folder in period_folders_list:
        periods_list.append(folder.split('/')[2])

    return periods_list


#######################################
# DYNAMIC REPORT DATA HANDLING
#######################################

# Configure logging
logging.basicConfig(level=logging.INFO)

# This function returns a pkl file, which it forms from the data from the main folder
def retrieve_pkl_data(periods_list, folder_path, conn, revenue_column, salary_column):
    pkl_data = {}

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
        pkl_data[period] = {}
        pkl_data[period]['margin_table'] = mt
        pkl_data[period]['total_salaries'] = total_salaries
        pkl_data[period]['total_collected_time'] = total_collected_time

    # Convert to pkl
    pkl_data = pickle.dumps(pkl_data)
    return pkl_data

# This function writes pkl file to gsm
def write_pkl_to_gcs(pkl_data, folder_path, file_name, conn):
    # Write PKL to GCS using the Streamlit connection
    with conn.fs.open(f"{folder_path}/{file_name}", 'wb') as f:
        f.write(pkl_data)
    # st.success(
    #     f'File successfully written to gs://{folder_path}/{file_name}')

# This function uses previous functions to a) retrieve data from main cloud and b) upload it, replacing the existing file
# Returns pkl file
def refresh_and_upload_data(periods_list, folder_path, revenue_column, salary_column, dynamic_folder_path, dynamic_file_name, conn):
    pkl_data = retrieve_pkl_data(
        periods_list, folder_path, conn, revenue_column, salary_column)
    write_pkl_to_gcs(
        pkl_data, dynamic_folder_path, dynamic_file_name, conn)
    # st.success("Data refreshed and uploaded successfully!")
    return pkl_data

# Forms two dfs from the pkl file


def pkl_to_two_dfs(pkl_file):
    combined_df_list = []
    main_stats_df_list = []

    for key in pkl_file:
        # First df (all the info)
        margin_table = pkl_file[key]['margin_table'].copy()
        margin_table['Quarter'] = key
        combined_df_list.append(margin_table)

        # Second df (main stats)
        main_stats_row = {'quarter': key,
                          'total_salaries': pkl_file[key]['total_salaries'],
                          'total_collected_time': pkl_file[key]['total_collected_time']}
        main_stats_df_list.append(main_stats_row)

    combined_df = pd.concat(combined_df_list, ignore_index=True)
    main_stats_df = pd.DataFrame(main_stats_df_list)

    return combined_df, main_stats_df

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


def plot_chart_salary_and_collected_time(margin_table, salary_column, revenue_column, currency_label):
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


def show_margin_table(margin_table, salary_column, revenue_column, currency_label):
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


# def client_contribution(RR, revenue_column):
#     st.write('')
#     st.write('')
#     st.markdown("**Client's contribution to collected time**")
#     n = st.slider("Pick a %", 0, 100, value=20, step=5)/100
#     client_contribution = RR.groupby(
#         'Client')[revenue_column].sum().reset_index()
#     top_clients = client_contribution.sort_values(
#         revenue_column, ascending=False).head(int(len(client_contribution) * n))
#     other_clients = client_contribution[~client_contribution['Client'].isin(
#         top_clients['Client'])]
#     other_clients = pd.DataFrame({'Client': ['Other'], revenue_column: [
#         other_clients[revenue_column].sum()]},)
#     grouped_data = pd.concat([top_clients, other_clients])
#     fig = px.pie(grouped_data, names='Client', values=revenue_column,
#                  title=f'Top {round(n*100)}% Clients Contribution to Revenue', hole=0.3)
#     st.plotly_chart(fig, use_container_width=True)

def client_contribution(RR, revenue_column):
    st.write('')
    st.write('')
    st.markdown("**Client's contribution to collected time**")

    # Add a dropdown to filter by Practice Area
    practice_areas = RR['Practice Area'].unique().tolist()
    practice_area = st.selectbox("Select Practice Area", [
                                 "All"] + practice_areas)

    # Filter the data based on the selected Practice Area
    if practice_area != "All":
        RR = RR[RR['Practice Area'] == practice_area]

    n = st.slider("Pick a %", 0, 100, value=20, step=5) / 100

    client_contribution = RR.groupby(
        'Client')[revenue_column].sum().reset_index()
    top_clients = client_contribution.sort_values(
        revenue_column, ascending=False).head(int(len(client_contribution) * n))
    other_clients = client_contribution[~client_contribution['Client'].isin(
        top_clients['Client'])]
    other_clients = pd.DataFrame({'Client': ['Other'], revenue_column: [
                                 other_clients[revenue_column].sum()]})
    grouped_data = pd.concat([top_clients, other_clients])

    fig = px.pie(grouped_data, names='Client', values=revenue_column,
                 title=f'Top {round(n*100)}% Clients Contribution to Revenue ({practice_area})', hole=0.3)
    st.plotly_chart(fig, use_container_width=True)


def hours_by_practice(MP):
    grouped_data = MP.groupby(['User', 'Practice Area'])[
        'Quantity'].sum().reset_index()
    fig = px.bar(grouped_data, x='Quantity', y='User', color='Practice Area', barmode='stack',
                 title="Users' Hours Allocation", labels={'Quantity': 'Hours', 'User': ''}, height=622)
    st.plotly_chart(fig, use_container_width=True)

