import streamlit as st
import streamlit.components.v1 as components

# Streamlit app setup
#st.set_page_config(page_title="Neuroref Report Dashboard", layout="wide")

# Title
st.title("EEG Reports Dashboard")


url = "https://app.sigmacomputing.com/embed/1-7katQ0rNGbMSHasd6Gzc25"

html=f'<iframe src="{url}" width="100%" height="900px"></iframe>'


components.html(html,height=1000,scrolling=False)
