"""
Performance caching utilities for MERT Streamlit application.
Provides optimized caching strategies for API calls and data loading.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
import streamlit as st
from services.mert2_data_management.mert_data_manager import MeRTDataManager


def performance_monitor(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = []
        
        st.session_state.performance_metrics.append({
            'function': func.__name__,
            'duration': end_time - start_time,
            'timestamp': time.time()
        })
        
        return result
    return wrapper


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_protocol_defaults_by_phase_count(n_phases: int, patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache protocol defaults by phase count"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.get_protocol_review_default_values(n_phases=n_phases))


@st.cache_data(ttl=600)  # Cache for 10 minutes
def preload_all_protocol_defaults(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[int, Dict[str, Any]]:
    """Preload defaults for all common phase counts"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    
    defaults = {}
    for n_phases in [1, 2, 3]:  # Common phase counts
        try:
            result = asyncio.run(data_manager.get_protocol_review_default_values(n_phases=n_phases))
            defaults[n_phases] = result
        except Exception as e:
            st.warning(f"Could not preload defaults for {n_phases} phases: {e}")
    
    return defaults


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_patient_data_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache patient data loading"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.fetch_patient_by_id())


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_clinic_info_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache clinic info loading"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.fetch_clinic_info())


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_eeg_info_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache EEG info loading"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.fetch_eeg_info_by_patient_id_and_eeg_id())


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_treatment_count_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache treatment count loading"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.get_completed_treatment_count_by_patient_id())


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_eeg_reports_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache EEG reports loading"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.get_eeg_report())


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_doctor_approval_state_cached(patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Cache doctor approval state"""
    data_manager = MeRTDataManager(patient_id, eeg_id, clinic_id)
    return asyncio.run(data_manager.api.get_doctor_approval_state())


def get_protocol_defaults_optimized(n_phases: int, patient_id: str, eeg_id: str, clinic_id: str) -> Dict[str, Any]:
    """Get protocol defaults with fallback to API if not preloaded"""
    preloaded = preload_all_protocol_defaults(patient_id, eeg_id, clinic_id)
    
    if n_phases in preloaded:
        return preloaded[n_phases]
    else:
        # Fallback to direct API call for unusual phase counts
        return get_protocol_defaults_by_phase_count(n_phases, patient_id, eeg_id, clinic_id)


def load_data_conditionally(patient_id: str, eeg_id: str, clinic_id: str) -> None:
    """Load data only if not already in session state"""
    
    # Check what data needs to be loaded
    data_to_load = []
    
    if 'patient_data' not in st.session_state:
        data_to_load.append('patient_data')
    
    if 'clinic_info' not in st.session_state:
        data_to_load.append('clinic_info')
    
    if 'treatment_count' not in st.session_state:
        data_to_load.append('treatment_count')
    
    if 'eeg_reports' not in st.session_state:
        data_to_load.append('eeg_reports')
    
    # Load only what's needed
    if data_to_load:
        with st.spinner(f"Loading {', '.join(data_to_load)}..."):
            if 'patient_data' in data_to_load:
                st.session_state.patient_data = get_patient_data_cached(patient_id, eeg_id, clinic_id)
            
            if 'clinic_info' in data_to_load:
                st.session_state.clinic_info = get_clinic_info_cached(patient_id, eeg_id, clinic_id)
            
            if 'treatment_count' in data_to_load:
                st.session_state.treatment_count = get_treatment_count_cached(patient_id, eeg_id, clinic_id)
            
            if 'eeg_reports' in data_to_load:
                st.session_state.eeg_reports = get_eeg_reports_cached(patient_id, eeg_id, clinic_id)


def validate_phase_change(current_count: int, new_count: int) -> tuple[bool, str]:
    """Validate if phase change is necessary and valid"""
    if new_count == current_count:
        return False, "No change needed"
    
    if new_count < 1:
        return False, "Must have at least 1 phase"
    
    if new_count > 3:
        return False, "Cannot have more than 3 phases"
    
    return True, "Valid change"


def clear_performance_cache():
    """Clear all performance-related caches"""
    st.cache_data.clear()
    if 'performance_metrics' in st.session_state:
        del st.session_state.performance_metrics


def show_performance_metrics():
    """Display performance metrics in sidebar"""
    if 'performance_metrics' in st.session_state and st.session_state.performance_metrics:
        with st.sidebar:
            st.subheader("Performance Metrics")
            
            recent_metrics = st.session_state.performance_metrics[-10:]  # Show last 10
            
            for metric in recent_metrics:
                st.text(f"{metric['function']}: {metric['duration']:.3f}s")
            
            if st.button("Clear Metrics"):
                st.session_state.performance_metrics = []
                st.rerun() 