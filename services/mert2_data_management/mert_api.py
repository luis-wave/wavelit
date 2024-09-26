import uuid
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin

import aiohttp
import dotenv
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
    approval: DefaultValues = Field(default_factory=DefaultValues)
    target_clinic_id: uuid.UUID = Field(default="TARGET_CLINIC_ID")
    delay: float = Field(default=0.3)
    timeout: int = Field(default=120)


def load_settings():
    dotenv.load_dotenv("services/mert2_data_management/.env")
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
                print(response)
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

    async def update_eeg_review(self) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/update_eeg_review",
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

    # Protocol Management endpoints
    async def save_protocol(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request(
            "POST", "protocol_management/save_protocol", protocol_data
        )

    async def reject_protocol(self, rejection_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request(
            "POST", "protocol_management/reject_protocol", rejection_data
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

    async def save_hr_report(self, heart_rate_bpm: int, st_dev_bpm:int) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/save_hr_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id,
                "heartrateBpm": heart_rate_bpm,
                "stdevBpm": st_dev_bpm
            },
        )

    async def delete_hr_report(self, heart_rate_bpm: int, st_dev_bpm:int) -> Dict[str, Any]:
        return await self._make_request(
            "POST",
            "macro-service/api/v1/report_management/delete_hr_report",
            {
                "eegId": self.eeg_id,
                "patientId": self.patient_id,
                "userGroupId": self.clinic_id
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
                "reportId": report_id
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
                "reportId": report_id
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
                "names": abnormality
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
                "abnormalityId": abnormality_id
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
                "abnormalityId": abnormality_id
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
                "names": artifacts
            },
        )

