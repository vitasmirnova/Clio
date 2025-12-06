
import plotly.graph_objects as go
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
                         name=f'2x Matter Cost in Salary,{currency_label}',
                         marker_color='red'))
    fig.add_trace(go.Bar(x=margin_table['Practice Area'],
                         y=margin_table[revenue_column],
                         name=f'Revenue,{currency_label}',
                         marker_color='rgb(26, 100, 255)'))
    fig.update_layout(barmode='group', title='Matter Cost in Salary and Revenue by Practice',
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
    # Calculate total hours per user and use it to order the User axis
    user_totals = MP.groupby(
        'User')['Quantity'].sum().sort_values(ascending=True)
    user_order = user_totals.index.tolist()  # List of users sorted by total hours

    # Group data by User and Practice Area, then sum the hours (Quantity)
    grouped_data = MP.groupby(['User', 'Practice Area'])[
        'Quantity'].sum().reset_index()

    # Create the stacked bar plot, specifying the user order in `category_orders`
    fig = px.bar(
        grouped_data,
        x='Quantity',
        y='User',
        color='Practice Area',
        barmode='stack',
        title="Users' Hours Allocation by Practice Area",
        labels={'Quantity': 'Hours', 'User': ''},
        height=622,
        category_orders={'User': user_order}  # Sort User axis by total hours
    )

    # Add total hours annotations for each user
    for user, total_hours in user_totals.items():
        fig.add_annotation(
            x=total_hours,
            y=user,
            text=f"{total_hours:.0f}",  # Display total hours (rounded)
            showarrow=False,
            font=dict(size=12, color="black"),
            xshift=10  # Offset text slightly to avoid overlap
        )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def display_user_hours_table(MP):
    # Compute required columns
    user_hours_table = MP.groupby('User').agg(
        User_Primary_Hours=('User Primary Hours', 'first'),
        User_Marketing_Hours=('User Marketing Hours', 'first'),
        User_Total_Hours=('User Total Hours', 'first')
    ).reset_index()

    # Add calculated columns
    user_hours_table['User_Total_Hours_per_360'] = (user_hours_table['User_Total_Hours'] / \
        360).round(2)
    user_hours_table['User_Billable_Hours_In_Total'] = (user_hours_table['User_Primary_Hours'] / \
        user_hours_table['User_Total_Hours']).round(2)
    user_hours_table['User_Marketing_Hours_In_Total'] = (user_hours_table['User_Marketing_Hours'] / \
        user_hours_table['User_Total_Hours']).round(2)

    # Rename columns for readability
    user_hours_table.rename(columns={
        'User_Total_Hours_per_360': 'Share of Total Hours in 360h',
        'User_Billable_Hours_In_Total': 'Share of Client Hours',
        'User_Marketing_Hours_In_Total': 'Share of Marketing Hours',
        'User_Primary_Hours': 'User Client Hours',
        'User_Marketing_Hours': 'User Marketing Hours',
        'User_Total_Hours': 'User Total Hours',
    }, inplace=True)

    # Display the table in Streamlit
    st.write("### User Hours Table")
    st.dataframe(user_hours_table, use_container_width=True)

#######################################
# DYNAMIC REPORT VISUALS
#######################################


def visualize_salaries_vs_revenue(df, revenue_column, salary_column):
    """
    This function visualizes the relationship between total salaries and total revenue across quarters.
    It creates a bar chart using Plotly and displays it using Streamlit.
    It includes percentage change annotations for total revenue and salaries compared to the previous quarter.

    Parameters:
    df (pd.DataFrame): A DataFrame containing the columns: 'quarter', 'total_salaries', and 'total_revenue'.
    """
    # Sort the dataframe by quarter to ensure the percentage change is correct
    df = df.sort_values(by='quarter').reset_index(drop=True)

    # Calculate percentage change in revenue and salaries compared to the previous quarter
    df['revenue_pct_change'] = df[revenue_column].pct_change() * 100
    df['salaries_pct_change'] = df[salary_column].pct_change() * 100

    # Melt the DataFrame for easier plotting (grouped by 'Quarter')
    df_melted = df.melt(id_vars='quarter', value_vars=[salary_column, revenue_column],
                        var_name='Metric', value_name='Amount')

    # Create the Plotly figure with slim bars
    fig = px.bar(df_melted, x='quarter', y='Amount', color='Metric',
                 barmode='group', title='Total Salaries vs Total Revenue by Quarter',
                 labels={'Amount': 'Amount (USD)', 'quarter': 'Quarter'},
                 color_discrete_map={salary_column: 'red'})  # Red for salaries

    # Adjust the bar width for slimmer columns
    fig.update_traces(width=0.3)

    # Add percentage change annotations for both revenue and salaries
    for i, row in df.iterrows():
        # Skip the first row since it doesn't have a previous quarter
        if i == 0 or pd.isna(row['revenue_pct_change']) or pd.isna(row['salaries_pct_change']):
            continue

        # Format the percentage change with '+' or '-' sign
        revenue_pct_change_str = f"{'+' if row['revenue_pct_change'] > 0 else ''}{row['revenue_pct_change']:.2f}%"
        salaries_pct_change_str = f"{'+' if row['salaries_pct_change'] > 0 else ''}{row['salaries_pct_change']:.2f}%"

        # Add an annotation (rectangular box) above the revenue bar
        fig.add_annotation(
            x=i + 0.2,
            # Position the annotation above the revenue bar
            y=row[revenue_column] * 1.1,
            text=revenue_pct_change_str,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="center",
            bordercolor="black",
            borderwidth=1,
            borderpad=4,  # Padding inside the box
            bgcolor="white",  # Box background color
            opacity=0.9
        )

        # Add an annotation (rectangular box) above the salaries bar
        fig.add_annotation(
            x=i - 0.2,
            # Position the annotation above the salaries bar
            y=row[salary_column] * 1.3,
            text=salaries_pct_change_str,
            showarrow=False,
            font=dict(size=12, color="black"),
            align="center",
            bordercolor="black",
            borderwidth=1,
            borderpad=4,  # Padding inside the box
            bgcolor="white",  # Box background color
            opacity=0.9
        )

    # Customize the layout
    fig.update_layout(xaxis_title='Quarter', yaxis_title='Amount (USD)',
                      legend_title='Metric')

    # Display the figure in Streamlit
    st.plotly_chart(fig)


def visualize_cost_vs_collected_time_v1(df, salary_column, collected_time_column):

    # Create the bar plot
    fig = px.bar(df,
                 x='Quarter',
                 y=collected_time_column,
                 color='Practice Area',
                 facet_col='Practice Area',
                 title='USD Collected Time by Practice Area and Quarter',
                 labels={collected_time_column: 'USD Collected Time',
                         'Practice Area': 'Practice Area'},
                 height=500
                 )

    # Loop through layout annotations to remove facet labels
    for axis in fig.layout.annotations:
        axis['text'] = ""  # Set facet labels to empty

    fig.for_each_annotation(lambda a: a.update(text=''))

    # Customize the layout
    fig.update_layout(
        yaxis_title='USD Collected Time',
        showlegend=True,  # Keeps the legend visible
    )

    fig.update_xaxes(showticklabels=False)
    fig.update_xaxes(title_text="")  # This removes "Quarter" label
    fig.update_layout(xaxis_title=None)  # This removes any x-axis title

    # Display in Streamlit
    st.plotly_chart(fig)


def visualize_cost_vs_collected_time_v2(df, salary_column, collected_time_column):
    # Create the bar plot
    fig = px.bar(df,
                 x='Quarter',
                 y=collected_time_column,
                 color='Practice Area',
                 barmode='group',
                 title='USD Collected Time by Practice Area and Quarter',
                 labels={collected_time_column: 'USD Collected Time',
                         'Practice Area': 'Practice Area'},
                 height=500
                 )

    # Customize the layout
    fig.update_layout(
        yaxis_title='USD Collected Time',
        showlegend=True,  # Keeps the legend visible
    )

    # Remove x-axis tick labels for a cleaner look
    fig.update_xaxes(showticklabels=False)
    fig.update_xaxes(title_text="")  # This removes "Quarter" label
    fig.update_layout(xaxis_title=None)  # This removes any x-axis title

    # Display in Streamlit
    st.plotly_chart(fig)


def visualize_cost_vs_collected_time_v3(df, salary_column, collected_time_column):
    # Create the bar plot
    fig = px.bar(df,
                 x='Practice Area',  # Set Practice Area as x-axis
                 y=collected_time_column,
                 color='Quarter',
                 barmode='group',  # Group bars by Practice Area
                 title='USD Collected Time by Practice Area and Quarter',
                 labels={collected_time_column: 'USD Collected Time',
                         'Practice Area': 'Practice Area'},
                 height=500
                 )

    # Customize the layout
    fig.update_layout(
        yaxis_title='USD Collected Time',
        showlegend=True,  # Keeps the legend visible
    )

    # Remove x-axis tick labels for a cleaner look
    fig.update_xaxes(title_text="Practice Area")  # Set title for the x-axis

    # Display in Streamlit
    st.plotly_chart(fig)


def visualize_cost_vs_collected_time_v4(df, collected_time_column):
    # Assign specific colors to each practice area for consistency across quarters
    # color_discrete_map = {
    #     'Litigation': '#1f77b4',  # blue
    #     'Crypto Law': '#ff7f0e',  # orange
    #     'Family Law': '#2ca02c',  # green
    #     'Corporate': '#d62728',   # red
    #     'Intellectual Property': '#9467bd'  # purple
    #     # Add more practice areas and colors if needed
    # }

    # Create the bar plot
    df = df.groupby(['Practice Area', 'Quarter'], as_index=False)[
        collected_time_column].sum()
    
    fig = px.bar(
        df,
        y=collected_time_column,
        color='Practice Area',
        text='Quarter',  # Display quarter on each bar
        # barmode='group',  # Grouped bars by practice area
        title='Total USD Collected Time by Practice Area and Quarter',
        labels={collected_time_column: 'USD Collected Time'},
        height=600
    )

    # Customize layout
    fig.update_layout(
        xaxis_title='Practice Area',
        yaxis_title='Total USD Collected Time',
    )

    # Add text to each bar to indicate the quarter
    fig.update_traces(textposition='outside')

    # Display in Streamlit
    st.plotly_chart(fig)


def visualize_cost_vs_collected_time_v5(df, salary_column, collected_time_column):
    # --- Create sortable quarter components ---
    df[['Q', 'Y']] = df['Quarter'].str.split('_', expand=True)
    df['Y'] = df['Y'].astype(int)
    df['Q'] = df['Q'].str.replace('Q', '').astype(int)

    # Sort by year and quarter
    df = df.sort_values(['Y', 'Q'])

    # Restore the original quarter label order
    df['Quarter'] = df['Quarter'].astype(str)

    # --- Bar chart ---
    fig = px.bar(
        df,
        x='Practice Area',
        y=collected_time_column,
        color='Quarter',
        barmode='group',
        title='USD Collected Time by Practice Area and Quarter',
        labels={
            collected_time_column: 'USD Collected Time',
            'Practice Area': 'Practice Area'
        },
        height=500
    )

    # Layout tweaks
    fig.update_layout(
        yaxis_title='USD Collected Time',
        showlegend=True,
    )

    fig.update_xaxes(title_text="Practice Area")

    # Render
    st.plotly_chart(fig)
