import uuid
from typing import Optional

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
    dotenv.load_dotenv(".env")
    return Config()


settings = load_settings()
