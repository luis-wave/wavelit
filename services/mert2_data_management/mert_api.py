import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
import dotenv
import streamlit as st
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Credentials(BaseSettings):
    username: str
    password: str
    usergroup: uuid.UUID


class ScientistCredentials(Credentials):
    model_config = SettingsConfigDict(env_prefix="APP_CYBERMED_SCIENTIST_")
    usergroup: Optional[uuid.UUID] = Field(default=None)


class CybermedConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_CYBERMED_CLOUD_")
    url: str
    project_prefix: Optional[str] = Field(default=None)
    scientist: ScientistCredentials = Field(default_factory=ScientistCredentials)


class MacroServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_MACRO_SERVICE_")
    url: str

class NeuralinkServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_NEURALINK_SERVICE_")
    url: str


class DefaultValues(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEFAULT_")
    approve_by: Optional[str] = Field(default="Auto Approve")
    location: Optional[str] = Field(default="F1-FZ-F2")
    phase: Optional[str] = Field(default="BIPHASIC")
    phase_duration: Optional[int] = Field(default=0)
    total_duration: Optional[int] = Field(default=0)
    num_phases: Optional[int] = Field(default=1)
    goal_intensity: Optional[int] = Field(default=0)


class Config(BaseSettings):
    cybermed: CybermedConfig = Field(default_factory=CybermedConfig)
    macro: MacroServiceConfig = Field(default_factory=MacroServiceConfig)
    neuralink: NeuralinkServiceConfig = Field(default_factory=NeuralinkServiceConfig)
    approval: DefaultValues = Field(default_factory=DefaultValues)
    target_clinic_id: uuid.UUID = Field(default="TARGET_CLINIC_ID")
    delay: float = Field(default=0.3)
    timeout: int = Field(default=120)


def load_settings():
    return Config()


class MeRTApi:
    def __init__(
        self,
        eeg_id: str,
        patient_id: str,
        clinic_id: str,
        config: Optional[Config] = None,
    ):
        self.config = config or load_settings()
        self.token = None
        self.eeg_id = eeg_id
        self.patient_id = patient_id
        self.clinic_id = clinic_id

    async def _login(self) -> str:
        url = urljoin(self.config.cybermed.url, "auth/api/v1/get-access-token/")
        auth = aiohttp.BasicAuth(
            f"{self.config.cybermed.project_prefix}{self.config.cybermed.scientist.username}",
            self.config.cybermed.scientist.password,
        )

        if not self.config.cybermed.url:
            raise ValueError("The base URL (self.config.cybermed.url) is not set.")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, auth=auth, timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                result = await response.json()
                self.token = result["token"]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = urljoin(self.config.macro.url, f"{endpoint}")
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self._get_headers(),
                json=data,
                timeout=self.config.timeout,
            ) as response:
                response.raise_for_status()
                if "text/html" in response.headers.get("Content-Type", ""):
                    return await self._parse_html_response(response)
                else:
                    return await response.json()

    async def _make_neuralink_request(
        self, method: str, endpoint: str
    ) -> Dict[str, Any]:
        eeg_id = self.eeg_id.replace("EEG-","")
        patient_id = self.patient_id.replace("PAT-","")

        url = urljoin(self.config.neuralink.url, f"{endpoint}?usergroup={self.clinic_id}&eeg_id={eeg_id}&patient_id={patient_id}")
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout,
            ) as response:
                response.raise_for_status()
                if "text/html" in response.headers.get("Content-Type", ""):
                    return await self._parse_html_response(response)
                else:
                    return await response.json()

    async def _parse_html_response(self, response: aiohttp.ClientResponse) -> str:
        raw_content = await response.read()
        return raw_content

    async def get_user(self) -> str:
        url = urljoin(self.config.cybermed.url, "auth/api/v1/user")
        auth = aiohttp.BasicAuth(
            f"{self.config.cybermed.project_prefix}{self.config.cybermed.scientist.username}",
            self.config.cybermed.scientist.password,
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, auth=auth, timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def mert_login(self, login: bool, username: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "neurolink-service/v2/events/login",
            {"successful_login": login, "username": username},
        )

    async def get_user_profile(
        self, user_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/administration/get_user_profile",
            {"userId": user_id, "userGroupId": user_group_id},
        )

    async def fetch_all_eeg_info_by_patient_id(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/fetch_all_eeg_info_by_patient_id",
            {"patientId": self.patient_id, "userGroupId": self.clinic_id},
        )

    async def fetch_patient_by_id(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/patient_management/fetch_patient_by_id",
            {"patientId": self.patient_id, "userGroupId": self.clinic_id},
        )

    async def get_completed_treatment_count_by_patient_id(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/treatment_management/get_completed_treatment_count_by_patient_id",
            {"patientId": self.patient_id, "userGroupId": self.clinic_id},
        )

    async def fetch_clinic_info(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/clinic_management/fetch_clinic_info",
            {"userGroupId": self.clinic_id},
        )

    async def get_report_approval_state(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/get_report_approval_state",
            {
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def fetch_all_staff(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/administration/fetch_all_staff",
            {"userGroupId": self.clinic_id},
        )

    async def fetch_eeg_info_by_patient_id_and_eeg_id(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/fetch_eeg_info_by_patient_id_and_eeg_id",
            {
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def fetch_all_eeg_info_by_patient_id(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/fetch_all_eeg_info_by_patient_id",
            {
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def get_eeg_report(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/get_eeg_report",
            {
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def save_patient_note(
        self, note: str, note_creation_date: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/patient_management/save_patient_note",
            {
                "note": note,
                "noteCreationDate": note_creation_date,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def get_neuroref_report(self, eeg_ids: list) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_analytics/get_neuroref_report",
            {
                "eegId": self.eeg_id,
                "eegIds": eeg_ids,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def download_neuroref_report(self, report_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/download_neuroref_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "reportId": report_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def get_neuroref_cz_report(self, eeg_ids: list) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_analytics/get_neuroref_cz_report",
            {
                "eegId": self.eeg_id,
                "eegIds": eeg_ids,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def download_neuroref_cz_report(self, report_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/download_neuroref_cz_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "reportId": report_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def save_hr_report(
        self, heart_rate_bpm: int, st_dev_bpm: int
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/save_hr_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "heartrateBpm": heart_rate_bpm,
                "stdevBpm": st_dev_bpm,
            },
        )

    async def delete_hr_report(
        self, heart_rate_bpm: int, st_dev_bpm: int
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_hr_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
            },
        )

    async def delete_neuroref_report(self, report_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_neuroref_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "reportId": report_id,
            },
        )

    async def delete_neuroref_cz_report(self, report_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_neuroref_cz_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "reportId": report_id,
            },
        )

    async def save_abnormality(self, abnormality: List[str]) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/save_abnormality",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "names": abnormality,
            },
        )

    async def delete_abnormality(self, abnormality_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_abnormality",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "abnormalityId": abnormality_id,
            },
        )

    async def approve_abnormality(self, abnormality_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/approve_abnormality",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "abnormalityId": abnormality_id,
            },
        )

    async def save_artifact(self, artifacts: List[str]) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/save_artifact",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "names": artifacts,
            },
        )

    async def delete_artifact(self, artifact_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_artifact",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "artifactId": artifact_id,
            },
        )

    async def save_document(self, file) -> str:
        url = (
            f"{self.config.macro.url}"
            + "macro-service/api/v1/report_management/save_document"
        )

        # Create a multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field("userGroupId", self.clinic_id)
        form_data.add_field("patientId", self.patient_id)
        form_data.add_field("eegId", self.eeg_id)

        # Add the file as a separate part
        form_data.add_field(
            "file", file.getvalue(), filename=file.name, content_type=file.type
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=form_data,
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
            ) as response:
                if response.status in (200, 204):
                    return await response.text()  # This should be the document_id
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to save document. Status: {response.status}, Error: {error_text}"
                    )

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_document",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "documentId": document_id,
            },
        )

    async def download_document(self, document_id: str) -> bytes:
        response = await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/download_document",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "documentId": document_id,
            },
        )
        return response

    async def update_eeg_review(self, payload: Dict) -> Dict[str, Any]:
        response = await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/update_eeg_review",
            payload,
        )
        return response

    async def save_protocol(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._make_request(
            "POST",
            "macro-service/api/v1/protocol_management/save_protocol",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "protocol": protocol,
            },
        )
        return response

    async def reject_protocol(
        self, protocol: Dict[str, Any], rejection_reason: str
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/protocol_management/reject_protocol",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
                "protocol": protocol,
                "rejectionReason": rejection_reason,
            },
        )

    async def get_doctor_approval_state(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/protocol_management/get_doctor_approval_state",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "eegId": self.eeg_id,
            },
        )

    async def save_eeg_scientist_patient_note(
        self, note: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/patient_management/save_eeg_scientist_patient_note",
            {
                "userGroupId": self.clinic_id,
                "patientId": self.patient_id,
                "noteCreationDate": datetime.utcnow().isoformat() + "Z",
                "eegScientistPatientNote": {
                    "recordingDate": note["recordingDate"],
                    "subject": note["subject"],
                    "content": note["content"],
                    "dateEdited": datetime.utcnow().isoformat() + "Z",
                },
            },
        )

    async def get_protocol_review_default_values(self) -> Dict[str, Any]:
        return await self._make_neuralink_request(
            "GET",
            "get_protocol_review_default_values",
        )
