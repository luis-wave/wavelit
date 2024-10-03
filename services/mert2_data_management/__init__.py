import datetime
import time
import traceback
import uuid
from typing import Optional

from pydantic import BaseModel

# from . import settings


class BaseProtocol(BaseModel, extra="allow"):
    burstDuration: Optional[int | float | str]
    burstFrequency: Optional[int | float | str]
    burstNumber: Optional[int | float | str]
    frequency: float
    interBurstInterval: Optional[int | float | str]
    interTrainInterval: Optional[int | float]
    recordingDate: Optional[str]
    trainDuration: Optional[int | float]
    trainNumber: Optional[int | float]


def extract_ids_from_eeg_info(eeg_info: dict) -> tuple[uuid.UUID, str, str]:
    usergroup = uuid.UUID(eeg_info["clinicId"])
    patient_id: str = eeg_info["patientId"]
    eeg_id: str = eeg_info["eegId"]
    assert patient_id.startswith("PAT-")
    assert eeg_id.startswith("EEG-")
    return usergroup, patient_id, eeg_id


def is_eeg_to_reject(eeg_info: dict):
    usergroup, patient_id, eeg_id = extract_ids_from_eeg_info(eeg_info)
    if usergroup != settings.target_clinic_id:
        print(f"usergroup: {usergroup} not in target clinic id")
        return False
    is_processed = eeg_info.get("eegInfo", {}).get("isProcessed", False)
    if not is_processed:
        print("not processed processed")
        return False
    status = eeg_info.get("eegInfo", {}).get("eegProtocolStatus", "NOT_READY")
    if not status == "PENDING":
        print(f"eeg status is pending")
        return False
    is_rejected = (
        eeg_info.get("eegInfo", {}).get("analysisMeta", {}).get("rejectionDatetime", "")
        or eeg_info.get("eegInfo", {})
        .get("analysisMeta", {})
        .get("rejectionReason", "")
        or eeg_info.get("eegInfo", {})
        .get("analysisMeta", {})
        .get("rejectionReviewerStaffId", "")
    )
    if is_rejected:
        print("eeg was rejected")
        return False
    return True


def extract_eeg_id_from_pending_eeg(pending_eeg: dict) -> str:
    eeg_id = pending_eeg["eegInfo"]["eegId"]
    assert eeg_id.startswith("EEG-")
    return eeg_id


def extract_base_protocol(pending_eeg: dict) -> BaseProtocol:
    return BaseProtocol.model_validate(pending_eeg["baseProtocol"])


def build_payload(eeg_id, patient_id, base_protocol: BaseProtocol):
    return {
        "userGroupId": f"{settings.target_clinic_id}",
        "patientId": f"{patient_id}",
        "eegId": f"{eeg_id}",
        "rejectionReason": "Clinic not subscribed for MeRT protocols",
        "rejectedBy": "MyWavePlatform, AutoRejectProtocol",
        "protocol": {
            "acknowledgeState": {
                "clinician": {
                    "approved": False,
                    "datetime": "",
                    "firstName": "",
                    "lastName": "",
                },
                "physician": {
                    "approved": False,
                    "datetime": "",
                    "firstName": "",
                    "lastName": "",
                },
            },
            "approvedByName": "",
            "approvedDate": "",
            "createdByName": "",
            "createdDate": "",
            "eegId": f"{eeg_id}",
            "patientId": f"{patient_id}",
            "numPhases": settings.approval.num_phases,
            "subtype": "CORTICAL",
            "totalDuration": settings.approval.total_duration,
            "type": "TREATMENT",
            "isRejected": True,
            "rejectionReason": "Incorrect patient upload",
            "phases": [
                {
                    "burstDuration": base_protocol.burstDuration,
                    "burstFrequency": base_protocol.burstFrequency,
                    "burstNumber": base_protocol.burstNumber,
                    "frequency": base_protocol.frequency,
                    "goalIntensity": settings.approval.goal_intensity,
                    "interBurstInterval": base_protocol.interBurstInterval,
                    "interTrainInterval": base_protocol.interTrainInterval,
                    "location": settings.approval.location,
                    "phaseDuration": settings.approval.phase_duration,
                    "pulseParameters": {"phase": settings.approval.phase},
                    "trainDuration": base_protocol.trainDuration,
                    "trainNumber": base_protocol.trainNumber,
                }
            ],
        },
    }


# def process_eeg_info(token: str, eeg_info: dict):
#     if not is_eeg_to_reject(eeg_info):
#         return
#     usergroup, patient_id, eeg_id = extract_ids_from_eeg_info(eeg_info)
#     eeg = macro.get_eeg(
#         token=token, usergroup=usergroup, patient_id=patient_id, eeg_id=eeg_id
#     )
#     time.sleep(settings.delay)
#     base_protocol = extract_base_protocol(eeg)
#     payload = build_payload(
#         eeg_id=eeg_id, patient_id=patient_id, base_protocol=base_protocol
#     )
#     macro.reject(token, payload)
#     print(
#         f"{datetime.datetime.utcnow().isoformat()} | CLI-{usergroup} | {patient_id} | {eeg_id}"
#     )


# def run(eeg_info):
#     print(f"Auto-approve initiated for: CLI-{settings.target_clinic_id}")
#     token = cybermed.get_token()
#     try:
#         process_eeg_info(token, eeg_info)
#     except Exception:
#         print(traceback.format_exc())
#         time.sleep(settings.delay)
#     print("Done")
