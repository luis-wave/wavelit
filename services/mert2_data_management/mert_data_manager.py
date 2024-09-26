import asyncio
import streamlit as st
from services.mert2_data_management.mert_api import MeRTApi
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class MeRTDataManager:
    def __init__(self, patient_id, eeg_id, clinic_id):
        self.patient_id = patient_id
        self.eeg_id = eeg_id
        self.clinic_id = clinic_id
        self.api = MeRTApi(patient_id=patient_id, eeg_id=eeg_id, clinic_id=clinic_id)

    async def initialize(self):
        await self.api._login()

    async def load_all_data(self):
        await self.initialize()
        await asyncio.gather(
            self.load_user_info(),
            self.load_user_profile(),
            self.load_patient_data(),
            self.load_all_eeg_info(),
            self.load_clinic_info(),
            self.load_treatment_count(),
            self.load_eeg_reports()
        )
        await self.load_neuroref_reports()

    async def load_user_info(self):
        st.session_state.user_info = await self.api.get_user()

    async def load_user_profile(self):
        st.session_state.user_profile = await self.api.get_user_profile(
            user_id="STF-e465eb68-ba87-11eb-8611-06b700432873",
            user_group_id="a9cf82fc-7c4d-11eb-b3ca-0a508de74e57"
        )

    async def load_patient_data(self):
        st.session_state.patient_data = await self.api.fetch_patient_by_id()

    async def load_all_eeg_info(self):
        st.session_state.all_eeg_info = await self.api.fetch_all_eeg_info_by_patient_id()
        st.session_state.eeg_history = self.parse_eeg_data_extended(st.session_state.all_eeg_info)

    async def load_clinic_info(self):
        st.session_state.clinic_info = await self.api.fetch_clinic_info()

    async def load_treatment_count(self):
        st.session_state.treatment_count = await self.api.get_completed_treatment_count_by_patient_id()

    async def load_eeg_reports(self):
        st.session_state.eeg_reports = await self.api.get_eeg_report()

    async def load_neuroref_reports(self):
        if 'eeg_reports' not in st.session_state:
            await self.load_eeg_reports()

        neuroref_linked_ear_report_ids = list(st.session_state.eeg_reports.get('neuroRefReports', {}).keys())
        neuroref_centroid_report_ids = list(st.session_state.eeg_reports.get('neurorefcz', {}).keys())

        st.session_state.downloaded_neuroref_report = await self.download_reports(
            neuroref_linked_ear_report_ids, self.api.download_neuroref_report
        )
        st.session_state.downloaded_neuroref_cz_report = await self.download_reports(
            neuroref_centroid_report_ids, self.api.download_neuroref_cz_report
        )

    async def download_reports(self, report_ids, download_function):
        tasks = [download_function(report_id=report_id) for report_id in report_ids]
        responses = await asyncio.gather(*tasks)
        return list(zip(responses, report_ids))

    async def update_neuroref_reports(self, eeg_ids):
        st.session_state.neuroref_report = await self.api.get_neuroref_report(eeg_ids=eeg_ids)
        st.session_state.downloaded_neuroref_report = await self.api.download_neuroref_report(
            report_id=st.session_state.neuroref_report["reportId"]
        )

    async def update_neuroref_cz_reports(self, eeg_ids):
        st.session_state.neuroref_cz_report = await self.api.get_neuroref_cz_report(eeg_ids=eeg_ids)
        st.session_state.downloaded_neuroref_cz_report = await self.api.download_neuroref_cz_report(
            report_id=st.session_state.neuroref_cz_report["reportId"]
        )


    async def delete_neuroref_report(self, report_id):
        await self.api.delete_neuroref_report(report_id=report_id)

    async def delete_neuroref_cz_report(self, report_id):
        await self.api.delete_neuroref_cz_report(report_id=report_id)

    async def save_artifact_distortions(self, artifacts):
        await self.api.save_artifact(artifacts=artifacts)

    async def save_abnormalities(self, abnormalities):
        try:
            # Convert the abnormalities to the format expected by the API
            api_abnormalities = []
            for abnormality in abnormalities:
                if abnormality == "Irregular EEG Activity (AEA)":
                    api_abnormalities.append("aea")
                elif abnormality == "Irregular Heart Rhythm (AHR)":
                    api_abnormalities.append("ahr")
                else:
                    api_abnormalities.append(abnormality)

            await self.api.save_abnormality(abnormality=api_abnormalities)
            logger.info("Abnormalities saved successfully")
        except Exception as e:
            logger.error(f"Failed to save abnormalities: {str(e)}")
            st.error("Failed to save abnormalities.")

    async def save_document(self, uploaded_file):
        try:
            url = f"{self.api.config.macro.url}/report_management/save_document"

            form_data = aiohttp.FormData()
            form_data.add_field('userGroupId', self.clinic_id)
            form_data.add_field('patientId', self.patient_id)
            form_data.add_field('eegId', self.eeg_id)
            form_data.add_field('file', uploaded_file.getvalue(),
                                filename=uploaded_file.name,
                                content_type=uploaded_file.type)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form_data, headers=self.api._get_headers()) as response:
                    if response.status == 200:
                        document_id = await response.text()
                        logger.info(f"Document {uploaded_file.name} saved successfully with ID: {document_id}")
                        return document_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to save document {uploaded_file.name}. Status: {response.status}, Error: {error_text}")
                        raise Exception(f"Failed to save document. Status: {response.status}")
        except Exception as e:
            logger.error(f"Exception while saving document {uploaded_file.name}: {str(e)}")
            raise


    @staticmethod
    def parse_eeg_data_extended(data):
        rows = []
        for key, content in data.items():
            recording_date = content.get('baseProtocol', {}).get('recordingDate', None)
            rows.append({
                'EEGId': key,
                'RecordingDate': recording_date,
            })

        df = pd.DataFrame(rows)
        df['RecordingDate'] = pd.to_datetime(df['RecordingDate'], errors='coerce')
        df = df.sort_values(by='RecordingDate', ascending=False)
        df['include?'] = True
        return df