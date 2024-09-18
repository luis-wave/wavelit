import uuid
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import dotenv
import requests
from pydantic import BaseModel, Field
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
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_settings()
        self.token = self._login()

    def _login(self) -> str:
        url = urljoin(self.config.cybermed.url, "auth/api/v1/get-access-token/")
        print(url)
        auth = (
            f"{self.config.cybermed.project_prefix}{self.config.cybermed.scientist.username}",
            self.config.cybermed.scientist.password,
        )
        response = requests.get(url, auth=auth, timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()["token"]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = urljoin(self.config.macro.url, f"{endpoint}")
        response = requests.request(
            method,
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.config.timeout,
        )
        response.raise_for_status()

        # Check Content-Type to decide how to handle the response
        if 'text/html' in response.headers.get('Content-Type', ''):
            return self._parse_html_response(response)
        else:
            return response.json()

    def _parse_html_response(self, response: requests.Response) -> Dict[str, Any]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else ''
        body_content = soup.body.get_text() if soup.body else ''

        # Create a dictionary to return
        return {
            'title': title,
            'body': body_content
        }

    def get_user(self) -> str:
        url = urljoin(self.config.cybermed.url, "macro-service/auth/api/v1/user")
        auth = (
            f"{self.config.cybermed.project_prefix}{self.config.cybermed.scientist.username}",
            self.config.cybermed.scientist.password,
        )
        response = requests.get(url, auth=auth, timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()

    def mert_login(self, login: bool, username: str) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "neurolink-service/v2/events/login",
            {"successful_login": login, "username": username},
        )

    def get_user_profile(self, user_id: str, user_group_id: str) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/administration/get_user_profile",
            {"userId": user_id, "userGroupId": user_group_id},
        )

    def fetch_all_eeg_info_by_patient_id(
        self, patient_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/fetch_all_eeg_info_by_patient_id",
            {"patientId": patient_id, "userGroupId": user_group_id},
        )

    def fetch_patient_by_id(
        self, patient_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/patient_management/fetch_patient_by_id",
            {"patientId": patient_id, "userGroupId": user_group_id},
        )

    def get_completed_treatment_count_by_patient_id(
        self, patient_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/treatment_management/get_completed_treatment_count_by_patient_id",
            {"patientId": patient_id, "userGroupId": user_group_id},
        )

    def fetch_clinic_info(self, user_group_id: str) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/clinic_management/fetch_clinic_info",
            {"userGroupId": user_group_id},
        )

    def get_report_approval_state(
        self, patient_id: str, eeg_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/report_management/get_report_approval_state",
            {"patientId": patient_id, "eegId": eeg_id, "userGroupId": user_group_id},
        )

    def fetch_all_staff(self, user_group_id: str) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/administration/fetch_all_staff",
            {"userGroupId": user_group_id},
        )

    def fetch_eeg_info_by_patient_id_and_eeg_id(
        self, patient_id: str, eeg_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/fetch_eeg_info_by_patient_id_and_eeg_id",
            {"patientId": patient_id, "eegId": eeg_id, "userGroupId": user_group_id},
        )

    def update_eeg_review(
        self, patient_id: str, eeg_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/eeg_management/update_eeg_review",
            {"patientId": patient_id, "eegId": eeg_id, "userGroupId": user_group_id},
        )

    def save_patient_note(
        self, note: str, note_creation_date: str, patient_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/patient_management/save_patient_note",
            {
                "note": note,
                "noteCreationDate": note_creation_date,
                "patientId": patient_id,
                "userGroupId": user_group_id,
            },
        )

    # Protocol Management endpoints
    def save_protocol(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request(
            "POST", "protocol_management/save_protocol", protocol_data
        )

    def reject_protocol(self, rejection_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request(
            "POST", "protocol_management/reject_protocol", rejection_data
        )

    # Patient Management endpoints
    def fetch_all_patients_paginated(
        self, page: int = 1, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "patient_management/fetch_all_patients_paginated",
            {"page": page, "filters": filters or {}},
        )

    def get_neuroref_report(
        self, eeg_id: str, eeg_ids: dict, patient_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/eeg_analytics/get_neuroref_report",
            {
                "eegId": eeg_id,
                "eegIds": eeg_ids,
                "patientId": patient_id,
                "userGroupId": user_group_id,
            },
        )

    def download_neuroref_report(
        self, eeg_id: str, patient_id: str, report_id: str, user_group_id: str
    ) -> Dict[str, Any]:
        return self._make_request(
            "POST",
            "macro-service/api/v1/report_management/download_neuroref_report",
            {
                "eegId": eeg_id,
                "patientId": patient_id,
                "reportId": report_id,
                "userGroupId": user_group_id,
            },
        )
