import time
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import pandas as pd
import streamlit as st
import os
import streamlit.components.v1 as components


# Helper func for transforming dfs
def convertLabel(df, type, home):
    if home == "sigma":
        if type == "report":
            df["Report_Status"].replace(True, "Available", inplace=True)
            df["Report_Status"].replace(False, "Unavailable", inplace=True)
        if type == "protocol":
            df["Protocol_Status"].replace(True, "Available", inplace=True)
            df["Protocol_Status"].replace(False, "Unavailable", inplace=True)
    if home == "wavelit":
        if type == "report":
            df["Report_Status"].replace("Available", True, inplace=True)
            df["Report_Status"].replace("Unavailable", False, inplace=True)
        if type == "protocol":
            df["Protocol_Status"].replace("Available", True, inplace=True)
            df["Protocol_Status"].replace("Unavailable", False, inplace=True)
    return df

DODS_PATIENT_DASHBOARD = os.getenv("DODS_PATIENT_DASHBOARD")
html = f'<iframe src="{DODS_PATIENT_DASHBOARD}" frameborder="0" width="100%" height="900px"></iframe>'
components.html(html, height=1000, scrolling=False)

st.title("Teammate Availability")

# S3 client setup
s3 = boto3.client("s3")
bucket_name = "lake-superior-dev"
report_file_name = f"teammate_report_availability.csv"
protocol_file_name = f"teammate_protocol_availability.csv"
report_file_path = f"silver/wavelit_admin_dev/{report_file_name}"
protocol_file_path = f"silver/wavelit_admin_dev/{protocol_file_name}"
report_obj = s3.get_object(Bucket=bucket_name, Key=report_file_path)
protocol_obj = s3.get_object(Bucket=bucket_name, Key=protocol_file_path)
report_df = convertLabel(pd.read_csv(report_obj["Body"]), "report", "wavelit")
protocol_df = convertLabel(pd.read_csv(protocol_obj["Body"]), "protocol", "wavelit")

edited_report = st.data_editor(
    data=report_df, disabled=("RowNumber", "Teammate"), hide_index=True
)
edited_protocol = st.data_editor(
    data=protocol_df, disabled=("RowNumber", "Teammate"), hide_index=True
)

if st.button("Availability: Update"):
    try:
        # Convert DataFrame to CSV and save it locally
        edited_report = convertLabel(edited_report, "report", "sigma")
        edited_protocol = convertLabel(edited_protocol, "protocol", "sigma")
        edited_report.to_csv(report_file_name, index=False)
        edited_protocol.to_csv(protocol_file_name, index=False)

        # Adding metadata
        processed_date = time.time()
        _ = s3.upload_file(
            report_file_name,
            bucket_name,
            report_file_path,
            ExtraArgs={
                "Metadata": {
                    "processed_date": str(processed_date),
                    "file_name": report_file_name,
                }
            },
        )
        _ = s3.upload_file(
            protocol_file_name,
            bucket_name,
            protocol_file_path,
            ExtraArgs={
                "Metadata": {
                    "processed_date": str(processed_date),
                    "file_name": protocol_file_name,
                }
            },
        )

        st.write("File uploaded successfully")
    except NoCredentialsError:
        st.error("Error: Unable to locate credentials")
    except PartialCredentialsError:
        st.error("Error: Incomplete credentials provided")
    except Exception as e:
        st.error(f"Error: {e}")

st.title("Shortened-Protocol Clinics")
st.header("Reference:")

SIGMA_DODS_CLINICS_URL = os.getenv("SIGMA_DODS_CLINICS_URL")
html = f'<iframe src="{SIGMA_DODS_CLINICS_URL}" frameborder="0" width="100%" height="900px"></iframe>'
components.html(html, height=1000, scrolling=False)

st.header("Table:")
shortened_clinics_name = f"shortened_protocols_clinics.csv"
shortened_path = f"silver/wavelit_admin_dev/{shortened_clinics_name}"
shortened_obj = s3.get_object(Bucket=bucket_name, Key=shortened_path)
shortened_df = pd.read_csv(shortened_obj["Body"])

edited_shortened = st.data_editor(
    data=shortened_df, hide_index=True, num_rows='dynamic'#, disabled=("ClinicId", "ClientId")
)

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")

csv = convert_df(edited_shortened)
st.download_button(
    label="Download",
    data=csv,
    file_name="shortened_protocols_clinics.csv",
    mime="text/csv",
)

if st.button("Shortened-Protocol Clinics: Update"):
    try:
        # Convert DataFrame to CSV and save it locally
        edited_shortened.to_csv(shortened_clinics_name, index=False)

        # Adding metadata
        processed_date = time.time()
        _ = s3.upload_file(
            shortened_clinics_name,
            bucket_name,
            shortened_path,
            ExtraArgs={
                "Metadata": {
                    "processed_date": str(processed_date),
                    "file_name": report_file_name,
                }
            },
        )
        st.write("File uploaded successfully")
    except NoCredentialsError:
        st.error("Error: Unable to locate credentials")
    except PartialCredentialsError:
        st.error("Error: Incomplete credentials provided")
    except Exception as e:
        st.error(f"Error: {e}")