# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]



## [1.0.0] - 2023-05-06
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
