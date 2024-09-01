import streamlit as st
import streamlit.components.v1 as components

from access_control import get_version_from_pyproject

st.title("Typeform Surveys")


typeform_embed_code = """
<div data-tf-live="01J6J6Y82RQZA6SA7ATA2TXJH6"></div>
<script src="//embed.typeform.com/next/embed.js"></script>
"""

components.html(typeform_embed_code, height=1000, scrolling=False)


# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
