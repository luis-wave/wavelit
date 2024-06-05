# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.11.0] - 2023-06-04
### Added
- Brought back NGBoost app with retrained model (bipolar transverse + 6-13 Hz frequency range).

### Changed
- NGBoost app now does batch processing with uploaded zip folders of eeg files.


## [1.10.0] - 2023-05-30
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



## [1.9.0] - 2023-05-28
### Added
- New users
### Changed
- EEG viewer line colors.


## [1.8.0] - 2023-05-24
### Added
- Download eeg files from MyWavePlatform



## [1.7.1] - 2023-05-21
### Fixed
- Sorting bug


## [1.7.0] - 2023-05-21
### Added
- Protocol dashboard

### Changed
- Protocol data is retrieved by PatientId instead of EEGId.


## [1.6.0] - 2023-05-17
### Added
- Login page

### Changed
- Increased confidence threshold for AEA detection from 0.2 to 0.75.



## [1.5.0] - 2023-05-15
### Added
- Added AHR and AEA button back.



## [1.4.1] - 2023-05-15
### Fixed
- ECG Viewer is null until record with ECG is uploaded.


## [1.4.0] - 2023-05-14
### Added
- ECG Viewer, heart rate calculation.
- AHR detection.




## [1.3.1] - 2023-05-11
### Removed
- AEA Detection button, app does not have permission to use it yet.




## [1.3.0] - 2023-05-11
### Added
- Seizure Detection invocation.
- Feedback mechanism with streamlit data editor and form components.
- EEG Graphs update with shading around the onset of seizure activity.



## [1.2.0] - 2023-05-09
### Added
- Automatically switch to Epoch generator page after EQI analysis is complete.

### Fixed
- Bipolar Transverse spelling error, which caused a bug preventing accurate plot generation.

### Removed
- File name and details, too much clutter.

### Changed
- Rounded EQI number to an integer


## [1.1.0] - 2023-05-08
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






## [1.0.0] - 2023-05-06
### Added
- Dockerfile for deployment.
- dockerignore file to keep the image lean and clean.


## [0.2.0] - 2023-05-03

### Added

- Streamlit application.
- EEG Upload logic
- Graphed out sorted eeg epochs and corresponding power spectral densities.
- Streamlit components to set the eeg reference and set the time length of the epochs.

## [0.1.0] - 2023-05-02

### Added

- Created a Persist pipeline to replicate logic in selecting synchronous portions of the eegs along the alpha band.
- Makefile for easy bash commands.
- Poetry package management.
- Local test script.
- Graph utils script.
