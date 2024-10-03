import streamlit as st
import pandas as pd
import time
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def convertLabel(df, type, home):
    if home == 'sigma':
        if type == 'report':
            df['Report_Status'].replace(True, 'Available', inplace=True)
            df['Report_Status'].replace(False, 'Unavailable', inplace=True)
        if type == 'protocol':
            df['Protocol_Status'].replace(True, 'Available', inplace=True)
            df['Protocol_Status'].replace(False, 'Unavailable', inplace=True)
    if home == 'wavelit':
        if type == 'report':
            df['Report_Status'].replace('Available', True, inplace=True)
            df['Report_Status'].replace('Unavailable', False, inplace=True)
        if type == 'protocol':
            df['Protocol_Status'].replace('Available', True, inplace=True)
            df['Protocol_Status'].replace('Unavailable', False, inplace=True)
    return df

st.title('Teammate Availability')

# S3 client setup
s3 = boto3.client("s3")
bucket_name = "lake-superior-dev"
report_file_name = f"teammate_report_availability.csv"
protocol_file_name = f"teammate_protocol_availability.csv"
report_file_path = f"silver/wavelit_admin_dev/{report_file_name}"
protocol_file_path = f"silver/wavelit_admin_dev/{protocol_file_name}"
report_obj = s3.get_object(Bucket=bucket_name, Key=report_file_path)
protocol_obj = s3.get_object(Bucket=bucket_name, Key=protocol_file_path)
report_df = convertLabel(pd.read_csv(report_obj['Body']), 'report', 'wavelit')
protocol_df = convertLabel(pd.read_csv(protocol_obj['Body']), 'protocol', 'wavelit')
edited_report = st.data_editor(data = report_df, disabled = ('RowNumber', 'Teammate'), hide_index = True)
edited_protocol = st.data_editor(data = protocol_df, disabled = ('RowNumber', 'Teammate'), hide_index = True)

if st.button("Update"):
    try:
        # Convert DataFrame to CSV and save it locally
        edited_report = convertLabel(edited_report, 'report', 'sigma')
        edited_protocol = convertLabel(edited_protocol, 'protocol', 'sigma')
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

# Footer section
version = get_version_from_pyproject()
footer_html = f"""
    <div style='position: fixed; bottom: 0; left: 0; padding: 10px;'>
        <span>Version: {version}</span>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
