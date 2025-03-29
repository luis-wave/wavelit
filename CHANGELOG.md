# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.18.0] - 2025-03-25
### Added
- Protocol phase editor via streamlit dialog
- readded HRV history table.

## [2.17.2] - 2025-03-25
### Changed
- Protocol tab UI

## [2.17.1] - 2025-03-21
### Fixed
- S3 reference issue.

## [2.17.0] - 2025-03-20
### Added
- New table with ecg_statistics re. patients' historical HR values.

## [2.16.3] - 2025-03-19
### Fixed
- Addendum logic, page will reload with addendum eegId, all MWP data will load with original eegid.
- Phase editor precision rounding error.
- Addendum button will only be available when eeg review is complete.
- User can edit notes when review state is not rejected, completed, or under clinical review.


## [2.16.2] - 2025-03-19
### Fixed
- Addendum was still pointing to local url


## [2.16.1] - 2025-03-14
### Fixed
- Selected eeg was not rendering.

### Changed
- Queue is now Home in the navbar.


## [2.16.0] - 2025-03-14
### Fixed
- Add drop down, user can select eeg and load data across any scan in the patient history.


## [2.15.0] - 2025-03-11
### Added
- Allow lab to copy Patient Id with a mouse click.
- Direct eeg download endpoint from MeRT 2.
- EEG Report History

### Fixed
- Note sorting logic by datetime.


## [2.14.4] - 2025-03-11
- Code block essentially duplicated in py file for Wavelit review page to allow for query parameter feature. Structure reorganized so that it is easier to read for future development.


## [2.14.3] - 2025-03-11
### Fixed
- Artifact statements in other category are no longer automatically capitalized.


## [2.14.2] - 2025-03-10
### Fixed
- Removed First/Second Review column + moved review status on protocol review page to 1st column.
- Changed Protocol Queue on Review Page to FFT view only.

## [2.14.1] - 2025-02-28
### Fixed
- Make NGBoost protocol graph visible in dark mode.


## [2.14.0] - 2025-02-27
### Added
- As requested by AJR, initial release of the NGBoost model + algorithm for ASD protocol generation.
### Fixed
- AEA annotations will appear even if there is an error in the annotation retrieval step for AHR.



## [2.13.3] - 2025-02-27
### Fixed
- Minimized Protocol History Column in Protocol Review tab.
### Added
- Download EEG Button in EEG Review tab.

## [2.13.2] - 2025-02-25
### Fixed
- Add/Remove phases with a click of button.
### Remove
- Include column from protocol data editor.

## [2.13.1] - 2025-02-25
### Fixed
- Unbound protocol frequency range, allow train number to be a float.
- Adding a third phase

## [2.13.0] - 2025-02-23
### Added
- Shareable url

### Fixed
- Removed quotes from uploaded report files.
- Note date logic

## [2.12.6] - 2025-02-21
### Changed
- Additional column in protocol review page; protocol history now also at the top of the page adjacent to the other patient metadata.
- Protocols presets logic resets to previous business logic.




## [2.12.5] - 2025-02-18
### Fixed
- Set other fields to be explicitly 0 after approval.
- Add in phaseDuration, set to 0 as default in MeRT 2.

## [2.12.4] - 2025-02-17
### Fixed
- Prevent user from saving null values in the protocol editor.



## [2.12.3] - 2025-02-14
### Fixed
- Deleting phase. It only takes once click now.

## [2.12.2] - 2025-02-13
### Fixed
- Note format.
- ECG onsets.
- Artifact/abnormality statements.

### Changed
- Increased pdf report size.
- Added chief complaint to protocol page.



## [2.12.1] - 2025-02-06
### Fixed
- Query parameter feature for protocol review page did not redirect user to correct tab.
### Added
- Protocol link within Protocol Dashboard now filters the sigma dashboard via query parameters in the URL.


## [2.12.0] - 2025-02-05
### Added
- Added query parameter feature, which allows suffixes to Wavelit URL to redirect link to designated page tab.


## [2.11.0] - 2025-01-29
### Fixed
- Review button disappears when review is complete.

### Changed
- Notes have been redesigned to be more compact. Ordered in descending order.

### Added
- Brought back the epoch generator to automate Persyst style graphs. Automated graph selection.



## [2.10.2] - 2025-01-16
### Fixed
- Missing primary complaint key.
- Hyperlinks for eeg viewer



## [2.10.1] - 2025-01-16
### Fixed
- Missing primary complaint key.
- Hyperlinks for eeg viewer


## [2.10.0] - 2025-01-11
### Changed
- Updated the design of the Nerosynchrony and Protocol page.
- Same day notes are consolidated.
- Artifact and abnormality statements have been expanded.

### Removed
- Experimental heart rate calculator with ECG artifacter.


## [2.9.0] - 2025-01-10
### Added
- Irregular EEG dashboard for Alex.
- EEG Download button for Alex.




## [2.8.0] - 2024-12-26
### Added
- Patient dashboard for Alex.



## [2.7.7] - 2024-11-21
### Fixed
- 1-25 Hz FIR bandpass filter.
- Missing slider window variable in the eeg graph function.
- EEG Viewer stand alone streamlit app now shows AEA for both linked ears and centroid when switching references.
- Fix access control.

## [2.7.6] - 2024-11-20
### Removed
- Bring back heart rate calculation for uploaded eegs.

## [2.7.5] - 2024-11-20
### Removed
- Disabled heart rate calculation for now.

## [2.7.0] - 2024-11-14
### Changed
- EEG Viewer UI/UX was updated once again, ML onset highlights, update table.
- Annotation colors changed from red to purple for AEA, green to blue for Autoreject.
- The scrollbar height was minimized, the X and Y axis borders were removed for a cleaner look.
- Updated lockfile


### Added
- Brought back sensitivity slider.
- New sigma dashboard, add table to send updates to the Databricks for shortened protocols.

### Fixed
- Converting points to datetime strings slowed EEG rendering, updated logic drastically improved render performance.



## [2.6.0] - 2024-10-25
### Changed
- EEG Viewer UI/UX was updated.
- Annotation colors changed from red to purple for AEA, green to blue for Autoreject.
- The scrollbar height was minimized, the X and Y axis borders were removed for a cleaner look.

### Added
- Add pulse button, the lab can add additional treatment location in the MeRT protocol.



## [2.5.4] - 2024-10-21
### Fixed
- User config error

## [2.5.3] - 2024-10-20
### Fixed
- Wavelit would error out if users did not have a MeRT Id or username field.

## [2.5.2] - 2024-10-16
### Changed
- Split up code in Neurosynchrony into several modules to improve separation of concerns and code maintenance.


## [2.5.1] - 2024-10-15
### Fixed
- Protocol update logic, protocol can only be updated between 8-13 Hz.
- Base protocol data is provided if updated protocol is not provided.
- Update review logic to proceed to second review status.

## [2.5.0] - 2024-10-02
### Added
- Neurosynchrony report page. Enables lab to approve, reject reports without using MeRT2.
- MeRT2Api, makes api calls to MeRT2 macroservice.
- MeRT2 data manager, loads responses from API calls to streamlit session state.
- Render functions for displaying patient, clinic, report, artifact, and abnormality data.
- Streamlit pdf viewer component.
- Report page, approve/reject/edit protocol treatment parameters.
- Organize MeRT 2 components in tabs.
- View and add notes



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
