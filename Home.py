"""
Run with `streamlit run Home.py`
"""

import streamlit as st

st.set_page_config(
    # page_icon="🏠",
    page_title='BK reports',
    layout='wide'
    )
st.write("Streamlit version:", st.__version__)
st.header("Welcome! 👋")
st.info('Choose a practice from the sidebar', icon='ℹ️')

st.write(f'User: {st.experimental_user.email}')

roles = {
    'Management': st.secrets['management_emails'],
    'Crypto law': st.secrets['crypto_law_emails'],
    'Russian_law': st.secrets['russian_law_emails'],
    'US General': st.secrets['us_general_emails'],
    'Litigation': st.secrets['litigation_emails']

}

def get_user_role(email):
    for role, emails in roles.items():
        if email in emails:
            return role
    return 'Other'


st.write(f'Role: {get_user_role(st.experimental_user.email)}')

