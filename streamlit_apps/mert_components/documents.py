"""
Enables the uploading of custom documents, i.e Persyst report
"""

import asyncio

import streamlit as st


@st.fragment
def render_documents(data_manager):
    st.subheader("Documents")

    if (
        "eeg_reports" in st.session_state
        and "documents" in st.session_state.eeg_reports
    ):
        documents = st.session_state.eeg_reports["documents"]
        if documents:
            st.write("Existing Documents:")
            for doc_id, doc_info in documents.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"- {doc_info['filename']}")
                with col2:
                    try:
                        document_content = asyncio.run(
                            data_manager.download_document(doc_id)
                        )
                        st.download_button(
                            label="Download",
                            data=document_content,
                            file_name=doc_info["filename"],
                        )
                    except Exception as e:
                        st.error(
                            f"Failed to download {doc_info['filename']}. Please try again. Failed for following reason {e}"
                        )
                with col3:
                    if st.button("Delete", key=f"delete_{doc_id}"):
                        try:
                            asyncio.run(data_manager.delete_document(doc_id))
                            st.success(
                                f"Document {doc_info['filename']} deleted successfully."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(
                                f"Failed to delete {doc_info['filename']}. Please try again.{e}"
                            )
        else:
            st.write("No existing documents found.")
    else:
        st.write("No document data available.")

    with st.popover("Add documents", use_container_width=True):
        uploaded_file = st.file_uploader("Upload a Persyst report", type="pdf")

        if uploaded_file is not None:
            if st.button("Submit Document"):
                try:
                    document_id = asyncio.run(data_manager.save_document(uploaded_file))
                    st.success(
                        f"Document uploaded successfully! Document ID: {document_id}"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload document. Error: {str(e)}")
