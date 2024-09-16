import streamlit as st
import pandas as pd
import time
import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


# command line prompt to run test env:
# python -m streamlit run C:\Users\jchong\Downloads\stTest.py

# helper func to convert df between sigma-streamlit envs
def convertLabel(df, type, home):
    if home == 'sigma':
        if type == 'report':
            df['Report Status'].replace(True, 'Available', inplace=True)
            df['Report Status'].replace(False, 'Unavailable', inplace=True)
        if type == 'protocol':
            df['Protocol Status'].replace(True, 'Available', inplace=True)
            df['Protocol Status'].replace(False, 'Unavailable', inplace=True)
    if home == 'wavelit':
        if type == 'report':
            df['Report Status'].replace('Available', True, inplace=True)
            df['Report Status'].replace('Unavailable', False, inplace=True)
        if type == 'protocol':
            df['Protocol Status'].replace('Available', True, inplace=True)
            df['Protocol Status'].replace('Unavailable', False, inplace=True)
    return df

st.title('Wavelit Admin')

#lab_staff: devdashboards.lab_staff
#teammate_report_availability: devdashboards.teammate_report_availability
#teammate_protocol_availability: devdashboards.teammate_protocol_availability
report_path = 's3://lake-superior-dev/silver/wavelit_admin_dev/teammate_report_availability.csv'
protocol_path = 's3://lake-superior-dev/silver/wavelit_admin_dev/teammate_protocol_availability.csv'
#report_path = r"C:\Users\jchong\Downloads\teammate_report_availability.csv"
#protocol_path = r"C:\Users\jchong\Downloads\teammate_protocol_availability.csv"
report_df = convertLabel(pd.read_csv(report_path), 'report', 'wavelit')
protocol_df = convertLabel(pd.read_csv(protocol_path), 'protocol', 'wavelit')
edited_report = st.data_editor(data = report_df, disabled = ('RowNumber', 'Teammate'), hide_index = True)
edited_protocol = st.data_editor(data = protocol_df, disabled = ('RowNumber', 'Teammate'), hide_index = True)

if st.button("Update"):
    try:
        # Convert DataFrame to CSV and save it locally
        report_file_name = f"teammate_report_availability.csv"
        protocol_file_name = f"teammate_protocol_availability.csv"
        edited_report = convertLabel(edited_report, 'report', 'sigma')
        edited_protocol = convertLabel(edited_protocol, 'protocol', 'sigma')
        edited_report.to_csv(report_file_name, index=False)
        edited_protocol.to_csv(protocol_file_name, index=False)

        # S3 client setup
        s3 = boto3.client("s3")
        bucket_name = "lake-superior-dev"
        report_file_path = f"silver/wavelit_admin_dev/{report_file_name}"
        protocol_file_path = f"silver/wavelit_admin_dev/{protocol_file_name}"

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
