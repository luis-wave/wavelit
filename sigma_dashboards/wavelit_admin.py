import time
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import pandas as pd
import streamlit as st
import os
import streamlit.components.v1 as components


s3 = boto3.client("s3")
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

# helper func for checking key exists in s3
def key_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print(f"Key: '{key}' does not exist!")
        else:
            print("Something else went wrong")
            raise
        return False

# Embedded Patient Dashboard
DODS_PATIENT_DASHBOARD = os.getenv("DODS_PATIENT_DASHBOARD")
html = f'<iframe src="{DODS_PATIENT_DASHBOARD}" frameborder="0" width="100%" height="900px"></iframe>'
components.html(html, height=1000, scrolling=False)
eeg_dload = pd.DataFrame(
    [
        {"Platform": "MeRT 2.0", "EEGId": ""},
    ]
)
eeg_dload_df = st.data_editor(
    data=eeg_dload,
    hide_index=True,
    column_config={
        "Platform": st.column_config.SelectboxColumn(
            options=["MeRT 2.0", "BrainCare", "MeRT 1.0"],
            required=True,
        )
    },
)
platform = eeg_dload_df["Platform"].iloc[0]
eegid = eeg_dload_df["EEGId"].iloc[0]
if eegid != "":
    if platform == "MeRT 2.0":
        clientid = "clinical"
    elif platform == "BrainCare":
        clientid = "consumer2"
    else:
        clientid = "btc2"
    eeg_bucket = "lake-superior-prod"
    eeg_s3_path = f"bronze/eegs/{clientid}/{eegid}.dat"
    if not key_exists(eeg_bucket, eeg_s3_path):
        edf_path = f"bronze/eegs/{clientid}/{eegid}.edf"
        if not key_exists(eeg_bucket, edf_path):
            raise Exception("EEG could not be found.")
        else:
            eeg_obj = s3.get_object(Bucket=eeg_bucket, Key=edf_path)
            eeg_content = eeg_obj["Body"].read()
            fname = f"{eegid}.edf"
    else:
        eeg_obj = s3.get_object(Bucket=eeg_bucket, Key=eeg_s3_path)
        eeg_content = eeg_obj["Body"].read()
        fname = f"{eegid}.dat"
else:
    eeg_content = "empty file"
    fname = "empty_file.txt"
if st.download_button(label="Download EEG", data=eeg_content, file_name=fname):
    try:
        st.write(f"EEG:'{eegid}' downloaded successfully")
    except NoCredentialsError:
        st.error("Error: Unable to locate credentials")
    except PartialCredentialsError:
        st.error("Error: Incomplete credentials provided")
    except Exception as e:
        st.error(f"Error: {e}")

# Embedded DoDS Teammate Availability Dashboard
st.title("Teammate Availability")
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
        edited_report = convertLabel(edited_report, "report", "sigma")
        edited_protocol = convertLabel(edited_protocol, "protocol", "sigma")
        edited_report.to_csv(report_file_name, index=False)
        edited_protocol.to_csv(protocol_file_name, index=False)
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

# Embedded Shortened-Protocols Dashboard
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
    data=shortened_df, hide_index=True, num_rows="dynamic"
)
@st.cache_data
def convert_df(df):
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
        edited_shortened.to_csv(shortened_clinics_name, index=False)
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