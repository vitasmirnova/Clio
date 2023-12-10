# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
#from openai import OpenAI
import pandas as pd
import streamlit as st
import plotly.express as px
# import streamlit_pandas as sp

st.title('Clio reports analyser')

RR_csv = st.file_uploader(
    "Upload a a CSV 'Revenue report'", type=["csv"])

if RR_csv is not None:
    st.success("File uploaded successfully!")

    # Read the uploaded CSV file into a DataFrame
    RR = pd.read_csv(RR_csv)
st.header('Data Editor')
new_RR = st.data_editor(RR, num_rows='dynamic', hide_index=False)

# Save the edited DataFrame to a new CSV file
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

csv = convert_df(new_RR)

st.download_button(
    "Press to download the edited CSV",
    csv,
    "RR_edited.csv",
    "text/csv",
    key='download-csv'
)


# Add separate data viewer
st.header('Data Viewer')
st.write(new_RR)

# From streamlit - pandas library

# create_data = {"Practice Area": "multiselect"}

# all_widgets = sp.create_widgets(RR, create_data)
# res = sp.filter_df(RR, all_widgets)

# st.write(res)

#Find what columns we have
# st.write(new_RR.columns)
# '''Client
# # Practice Area
# # Matter Number
# # Matter Description
# # Responsible Attorney
# # Unbilled Time
# # Unbilled Hours
# # Unbilled Expense
# # Billed Time
# # Billed Hours
# Billed Expense
# Discounted Time
# Discounted Expense
# Credit Notes
# Collected Time
# Collected Expense
# Currency
# USD_collected_time
# '''

st.header('Charts')

st.header("Revenue by Practice Area")
# Create a bar chart using Plotly Express
fig = px.bar(new_RR, x='Practice Area', y='USD_collected_time',
             title='Revenue Analysis by Practice Area',
             labels={'USD_collected_time': 'Total Revenue',
                     'Practice Area': 'Practice Area'},
             color="Practice Area",
             color_discrete_sequence=px.colors.qualitative.G10)

st.plotly_chart(fig, use_container_width=True)


st.header("Currency Distribution")

currency_distribution = new_RR.groupby(
    'Currency')['USD_collected_time'].sum().reset_index()

# Create a pie chart using Plotly Express
fig = px.pie(
    currency_distribution,
    names='Currency',
    values='USD_collected_time',
    title='Currency Distribution of Collected Revenue',
    hole=0.3,  # Set to 0 for a pie chart or adjust for a donut chart
)

# Show the interactive plot
st.plotly_chart(fig, use_container_width=True)







st.header("Client's contribution to collected time")

#  title='Top 20% Clients Contribution to Revenue
n = st.slider("Pick a %", 0, 100, value  = 20, step=5)/100

# Group by client and sum the collected time
client_contribution = new_RR.groupby(
    'Client')['USD_collected_time'].sum().reset_index()

# Calculate the total revenue
total_revenue = client_contribution['USD_collected_time'].sum()

# Sort clients by contribution and select the top 10%
top_clients = client_contribution.sort_values(
    'USD_collected_time', ascending=False).head(int(len(client_contribution) * n))

# Group the remaining clients as 'Other'
other_clients = client_contribution[~client_contribution['Client'].isin(
    top_clients['Client'])]
other_clients = pd.DataFrame({'Client': ['Other'], 'USD_collected_time': [
                             other_clients['USD_collected_time'].sum()]})

# Concatenate top clients and 'Other'
grouped_data = pd.concat([top_clients, other_clients])

# Create a pie chart using Plotly Express
fig = px.pie(
    grouped_data,
    names='Client',
    values='USD_collected_time',
    title=f'Top {round(n*100)}% Clients Contribution to Revenue',
    hole=0.3,  # Set to 0 for a pie chart or adjust for a donut chart
)

# Show the interactive plot
st.plotly_chart(fig, use_container_width=True)



# st.header('Matter Descriptions')
# all_descriptions = ' '.join(new_RR['Matter Description'].astype(str))

# # Generate the word cloud
# wordcloud = WordCloud(width=800, height=400,
#                       background_color='white').generate(all_descriptions)

# # Plot the word cloud using Streamlit
# st.image(wordcloud.to_array())

# # Optionally, you can display the raw text







# Set your OpenAI API key



# Просто чат-помощник

# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "gpt-3.5-turbo"

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# if prompt := st.chat_input("What is up?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
#         for response in client.chat.completions.create(
#             model=st.session_state["openai_model"],
#             messages=[
#                 {"role": m["role"], "content": m["content"]}
#                 for m in st.session_state.messages
#             ],
#             stream=True,
#         ):
#             full_response += (response.choices[0].delta.content or "")
#             message_placeholder.markdown(full_response + "▌")
#         message_placeholder.markdown(full_response)
#     st.session_state.messages.append(
#         {"role": "assistant", "content": full_response})


## БУДУ ДЕЛАТЬ ДАЛЬШЕ
# st.header("GPT Chart Generator")

# sample_data = new_RR.head(3)
# st.write(sample_data)

# # Allow the user to enter a prompt for GPT
# gpt_prompt = st.text_area("Enter a prompt for GPT:", "Generate charts for the data.")

# # Generate charts using GPT
# if st.button("Generate Charts"):
#     # Call GPT to generate charts based on the edited CSV data
#     gpt_response = client.chat.completions.create(
#         engine="text-davinci-002",
#         prompt=gpt_prompt,
#         max_tokens=300,
#         n=1,
#         stop=None
#     )
    
#     # Extract generated charts from GPT response
#     generated_charts = gpt_response.choices[0].text
    
#     # Display the generated charts
#     st.markdown("### Generated Charts:")
#     st.markdown(generated_charts)