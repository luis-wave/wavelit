import asyncio
import logging
from typing import Any, Dict, List

import aiohttp
import pandas as pd
import streamlit as st

from services.mert2_data_management.mert_api import MeRTApi

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

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
            self.load_eeg_reports(),
        )
        await self.load_neuroref_reports()

    async def load_user_info(self):
        st.session_state.user_info = await self.api.get_user()

    async def load_user_profile(self):
        st.session_state.user_profile = await self.api.get_user_profile(
            user_id="STF-e465eb68-ba87-11eb-8611-06b700432873",
            user_group_id="a9cf82fc-7c4d-11eb-b3ca-0a508de74e57",
        )

    async def load_patient_data(self):
        st.session_state.patient_data = await self.api.fetch_patient_by_id()

    async def load_all_eeg_info(self):
        st.session_state.all_eeg_info = (
            await self.api.fetch_all_eeg_info_by_patient_id()
        )
        st.session_state.eeg_history = self.parse_eeg_data_extended(
            st.session_state.all_eeg_info
        )

    async def load_clinic_info(self):
        st.session_state.clinic_info = await self.api.fetch_clinic_info()

    async def load_treatment_count(self):
        st.session_state.treatment_count = (
            await self.api.get_completed_treatment_count_by_patient_id()
        )

    async def load_eeg_reports(self):
        st.session_state.eeg_reports = await self.api.get_eeg_report()

    async def fetch_eeg_info_by_patient_id_and_eeg_id(self) -> Dict[str, Any]:
        try:
            return await self.api.fetch_eeg_info_by_patient_id_and_eeg_id()
        except Exception as e:
            logger.error(f"Failed to fetch EEG info: {str(e)}")
            raise

    async def update_eeg_review(
        self, is_first_reviewer: bool, state: str, rejection_reason: List[str] = None
    ) -> Dict[str, Any]:
        try:
            payload = {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "staffId": st.session_state["id"],
                "isProtocol": False,
                "isFirstReviewer": is_first_reviewer,
                "state": state,
            }
            if state == "REJECTED" and rejection_reason:
                payload["rejectionReason"] = rejection_reason

            return await self.api.update_eeg_review(payload)
        except Exception as e:
            logger.error(f"Failed to update EEG review: {str(e)}")
            raise

    async def load_neuroref_reports(self):
        if "eeg_reports" not in st.session_state:
            await self.load_eeg_reports()

        neuroref_linked_ear_report_ids = list(
            st.session_state.eeg_reports.get("neuroRefReports", {}).keys()
        )
        neuroref_centroid_report_ids = list(
            st.session_state.eeg_reports.get("neurorefcz", {}).keys()
        )

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
        st.session_state.neuroref_report = await self.api.get_neuroref_report(
            eeg_ids=eeg_ids
        )
        st.session_state.downloaded_neuroref_report = (
            await self.api.download_neuroref_report(
                report_id=st.session_state.neuroref_report["reportId"]
            )
        )

    async def update_neuroref_cz_reports(self, eeg_ids):
        st.session_state.neuroref_cz_report = await self.api.get_neuroref_cz_report(
            eeg_ids=eeg_ids
        )
        st.session_state.downloaded_neuroref_cz_report = (
            await self.api.download_neuroref_cz_report(
                report_id=st.session_state.neuroref_cz_report["reportId"]
            )
        )

    async def delete_neuroref_report(self, report_id):
        await self.api.delete_neuroref_report(report_id=report_id)

    async def delete_neuroref_cz_report(self, report_id):
        await self.api.delete_neuroref_cz_report(report_id=report_id)

    async def save_artifact_distortions(self, artifacts):
        await self.api.save_artifact(artifacts=artifacts)

    async def delete_artifact(self, artifact_id):
        try:
            await self.api.delete_artifact(artifact_id)
            logger.info(f"Artifact {artifact_id} deleted successfully")

            # Remove the artifact from the local state
            if (
                "eeg_reports" in st.session_state
                and "artifacts" in st.session_state.eeg_reports
            ):
                if artifact_id in st.session_state.eeg_reports["artifacts"]:
                    del st.session_state.eeg_reports["artifacts"][artifact_id]

        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {str(e)}")
            raise

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

    async def delete_abnormality(self, abnormality_id):
        try:
            # Call the API to delete the abnormality
            await self.api.delete_abnormality(abnormality_id=abnormality_id)
            logger.info(f"Abnormality {abnormality_id} deleted successfully")

            # Remove the abnormality from the local state
            if (
                "eeg_reports" in st.session_state
                and "abnormalities" in st.session_state.eeg_reports
            ):
                if abnormality_id in st.session_state.eeg_reports["abnormalities"]:
                    del st.session_state.eeg_reports["abnormalities"][abnormality_id]

            # Optionally, you can refresh the entire EEG report here if needed
            # await self.load_eeg_reports()
        except Exception as e:
            logger.error(f"Failed to delete abnormality {abnormality_id}: {str(e)}")
            raise

    async def approve_abnormality(self, abnormality_id):
        try:
            # Call the API to approve the abnormality
            await self.api.approve_abnormality(abnormality_id=abnormality_id)
            logger.info(f"Abnormality {abnormality_id} approved successfully")

            # Update the abnormality status in the local state
            if (
                "eeg_reports" in st.session_state
                and "abnormalities" in st.session_state.eeg_reports
            ):
                if abnormality_id in st.session_state.eeg_reports["abnormalities"]:
                    st.session_state.eeg_reports["abnormalities"][abnormality_id][
                        "isApproved"
                    ] = True
        except Exception as e:
            logger.error(f"Failed to approve abnormality {abnormality_id}: {str(e)}")
            raise

    async def save_document(self, uploaded_file):
        try:
            document_id = await self.api.save_document(uploaded_file)
            logger.info(f"Document saved successfully")
            await self.load_eeg_reports()  # Refresh the EEG reports
            return document_id
        except Exception as e:
            logger.error(
                f"Exception while saving document {uploaded_file.name}: {str(e)}"
            )
            raise

    async def delete_document(self, document_id):
        try:
            response, status = await self.api.delete_document(document_id)
            if status in (200, 34):
                logger.info(f"Document deleted successfully")
                await self.load_eeg_reports()  # Refresh the EEG reports
            else:
                raise Exception(f"Failed to delete document. Status: {status}")
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise

    async def download_document(self, document_id):
        try:
            content = await self.api.download_document(document_id)
            logger.info(f"Document {document_id} downloaded successfully")

            return content
        except Exception as e:
            logger.error(f"Failed to download document {document_id}: {str(e)}")
            raise

    async def save_protocol(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self.api.save_protocol(protocol=protocol)
            logger.info(f"Protocol saved successfully for EEG ID: {self.eeg_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save protocol: {str(e)}")
            raise

    async def reject_protocol(
        self, rejection_reason: str, protocol: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self.api.reject_protocol(
                rejection_reason=rejection_reason, protocol=protocol
            )
            logger.info(f"Protocol rejected successfully for EEG ID: {self.eeg_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to reject protocol: {str(e)}")
            raise

    async def get_doctor_approval_state(self) -> Dict[str, Any]:
        try:
            result = await self.api.get_doctor_approval_state()
            logger.info(f"Retrieved doctor approval state for EEG ID: {self.eeg_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get doctor approval state: {str(e)}")
            raise

    async def save_eeg_scientist_patient_note(
        self, note: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self.api.save_eeg_scientist_patient_note(note=note)
            logger.info(
                f"EEG scientist patient note saved successfully for patient ID: {self.patient_id}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to save EEG scientist patient note: {str(e)}")
            raise

    async def get_protocol_review_default_values(
        self
    ) -> Dict[str, Any]:
        try:
            result = await self.api.get_protocol_review_default_values()
            logger.info(
                f"EEG presets retrieved successfully for patient ID: {self.patient_id}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to save EEG presets: {str(e)}")
            raise

    @staticmethod
    def parse_eeg_data_extended(data):
        rows = []
        for key, content in data.items():
            recording_date = content.get("baseProtocol", {}).get("recordingDate", None)
            rows.append(
                {
                    "EEGId": key,
                    "RecordingDate": recording_date,
                }
            )

        df = pd.DataFrame(rows)
        df["RecordingDate"] = pd.to_datetime(df["RecordingDate"], errors="coerce")
        df = df.sort_values(by="RecordingDate", ascending=False)
        df["include?"] = True
        return df


    async def add_report_addendum(self):
        try:
            response = await self.api.add_report_addendum()
            eeg_id = response["addendumId"]
            logger.info(f"Addendum eeg id {eeg_id} successfully generated.")

            return eeg_id
        except Exception as e:
            logger.error(f"Failed to generate addendum: {str(e)}")
            raise
