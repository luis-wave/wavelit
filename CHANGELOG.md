# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.0] - 2024-09-27
### Added
- Neurosynchrony report page. Enables lab to approve, reject reports without using MeRT2.
- MeRT2Api, makes api calls to MeRT2 macroservice.
- MeRT2 data manager, loads responses from API calls to streamlit session state.
- Render functions for displaying patient, clinic, report, artifact, and abnormality data.
- Streamlit pdf viewer component.



## [2.4.0] - 2024-09-01
### Added
- Query parameter for EEG reference.

## [2.3.0] - 2024-08-31
### Added
- EDF file from simulated oscillations.
- Simulated EEG file and streamlit app for faster development on the EEG Viewer.

### Changed
- Moved typeforms surveys lower in the navigation bar.
- Formatted files with Ruff.


## [2.2.0] - 2024-08-30
### Added
- Typeform survey page

## [2.1.0] - 2024-08-29
### Added
- Added a buildspec.yml for automated deployment via CI/CD pipeline.

### Changed
- Config.yml now included in Dockerbuild.



## [2.0.4] - 2024-08-27
### Fixed
- Optimal time window for NGBoost model was 5.12s not 2.56s



## [2.0.3] - 2024-08-23
### Fixed
- Missing nvironment variables arguments in Dockerfile.


## [2.0.2] - 2024-08-22
### Fixed
- Fixed channel order in epoch plots.


## [2.0.1] - 2024-08-14
### Fixed
- EQI time window set logic


## [2.0.0] - 2024-07-20
### Added
- Sigma Dashboard for EEG Report and Protocol Review. Kudos to our Data Engineer.
- EEGId can now be entered as a query parameter.
- Protocol and Report dashboards have all of the visualizations for EEG, ECG, and epoch review.
- Support for retrieving consumer EEG record data.
- Direct urls to direct to AEA/AHR reviews in Streamlit app.
- Annotations are saved in an S3 bucket 'streamlit_validations'

### Changed
- Navigation bar is more streamlined.
- Login and authentication protects all pages across the streamlit app.
- Increased offset threshold (20 to 35) for lead off removal.

### Fixed
- Epoch sorting algorithm; relative power sum calculation.


## [1.14.1] - 2024-06-23
### Fixed
- EEG Viewer would not render if Autoreject checked for bipolar longitudinal key in autoreject field.


## [1.14.0] - 2024-06-22
### Added
- Autoreject annotations in EEG viewer.
- EEGid is now added as part of the feedback table for AEA/AHR annots.


### Changed
- EEGs downloaded by EEGId are preloaded with AEA/AHR/Autoreject annotations across viewers. No need to invoke Sagemaker endpoints.
- Code has been refactored to increased modularity.
- Correct EEG Channel Order for Linked Ears and centroid data.



## [1.13.0] - 2024-06-10
### Added
- Asynchronous calls to AEA, AHR, Autoreject endpoints to MyWavePlatform.
- Loaded data from asynchronous calls to session state. All eegs called by eeg_ids will instantly have abnormal EEG data available for visualizations.
- Installed aihttp, aidns libraries.

### Changed
- X-axis for EEG and ECG viewer now show time in 'mm:ss:sss' format instead of just seconds.



## [1.12.0] - 2024-06-10
### Added
- Bad lead removal across all epochs. Currently works for monopolar montages.
- Epoch dataframe to review sync score, alpha score, and average psds.

### Removed
- Wavelet viewer



## [1.11.0] - 2024-06-04
### Added
- Brought back NGBoost app with retrained model (bipolar transverse + 6-13 Hz frequency range).

### Changed
- NGBoost app now does batch processing with uploaded zip folders of eeg files.


## [1.10.0] - 2024-05-30
### Added
- Interactive 3d plot of all Power Spectra across epochs.
- Selective mode to generate a single plot.
- EEG Data Manager
- MyWavePlatform API support.
- Wavelet viewer

### Changed
- Generate top 20 plots.
- Logic to handle eeg uploads.
- All headers now have either filename (uploaded eegs), eeg_ids (downloaded_eegs), and recording date.
- Added an icon next to epochs.py.
- Wavelet viewer renders spectrograph in 3d again.


## [1.9.0] - 2024-05-28
### Added
- New users
### Changed
- EEG viewer line colors.



## [1.8.0] - 2024-05-24
### Added
- Download eeg files from MyWavePlatform



## [1.7.1] - 2024-05-21
### Fixed
- Sorting bug


## [1.7.0] - 2024-05-21
### Added
- Protocol dashboard

### Changed
- Protocol data is retrieved by PatientId instead of EEGId.


## [1.6.0] - 2024-05-17
### Added
- Login page

### Changed
- Increased confidence threshold for AEA detection from 0.2 to 0.75.



## [1.5.0] - 2024-05-15
### Added
- Added AHR and AEA button back.



## [1.4.1] - 2024-05-15
### Fixed
- ECG Viewer is null until record with ECG is uploaded.


## [1.4.0] - 2024-05-14
### Added
- ECG Viewer, heart rate calculation.
- AHR detection.




## [1.3.1] - 2024-05-11
### Removed
- AEA Detection button, app does not have permission to use it yet.




## [1.3.0] - 2024-05-11
### Added
- Seizure Detection invocation.
- Feedback mechanism with streamlit data editor and form components.
- EEG Graphs update with shading around the onset of seizure activity.



## [1.2.0] - 2024-05-09
### Added
- Automatically switch to Epoch generator page after EQI analysis is complete.

### Fixed
- Bipolar Transverse spelling error, which caused a bug preventing accurate plot generation.

### Removed
- File name and details, too much clutter.

### Changed
- Rounded EQI number to an integer


## [1.1.0] - 2024-05-08
### Added
- Bipolar Longitudinal Montage
- Bipolar Transverse Montage
- EQI Score
- EQI guided tine window and reference selection. Really bad eegs are switched to centroid montage, the lower the eqi the lower the time window. This should make it more convenient for app to find sync alpha bursts.
- EEG Viewer
- NGBoost protocol

### Removed
- Temporal Central Parasaggital montage option.
- Deploy Image github action

### Changed
- MyWaveObject loads outside of the persist pipeline.



## [1.0.0] - 2024-05-06
### Added
- Dockerfile for deployment.
- dockerignore file to keep the image lean and clean.


## [0.2.0] - 2024-05-03

### Added

- Streamlit application.
- EEG Upload logic
- Graphed out sorted eeg epochs and corresponding power spectral densities.
- Streamlit components to set the eeg reference and set the time length of the epochs.

## [0.1.0] - 2024-05-02

### Added

- Created a Persist pipeline to replicate logic in selecting synchronous portions of the eegs along the alpha band.
- Makefile for easy bash commands.
- Poetry package management.
- Local test script.
- Graph utils script.
