# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [1.2.0] - 2023-05-09
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
