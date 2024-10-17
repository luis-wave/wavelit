![Python Version](https://img.shields.io/badge/python-%3E%3D3.10%2C%3C3.13-green)
[![Lint with Ruff](https://github.com/luis-wave/wavelit/actions/workflows/ruff-linter.yml/badge.svg)](https://github.com/luis-wave/wavelit/actions/workflows/ruff-linter.yml)


# Wavelit

Wavelit is a Streamlit application designed to streamline and enhance the workflow of the lab. Wavelit offers an integrated platform that hosts a variety of web applications, each tailored to improve the efficiency and effectiveness of EEG-related tasks.

 
## Key Features

### Sigma Dashboards
Seamless integration with our data platform. These dashboards are specifically designed to pull EEG records on the queue for report and protocol processing. Data from this platform is automatically pulled into Wavelit, allowing for easy retrieval, processing, and analysis. This integration eliminates the need for manual data entry, reducing the risk of errors and freeing up valuable time for lab personnel.

![sigma](images/sigma.png)

 
### Automatic EEG Viewer (AEV)
EEG visualization tool for highlighting and annotating abnormal EEG activity (seizure, artifact). Enables feedback for Wave's set of neural networks and machine learning models.

![aea](images/aea.png)
![ahr](images/ahr.png)



### Automatic Epoch Plot Generation
The app scans the entire EEG recording to identify time windows that exhibit characteristics of eyes-closed activity. The heuristic is tuned to recognize increased alpha wave activity, relative to the EEG's signal quality level.

![epoch plot generation](images/epochs.png)



### Seamless Data Integration
One of the standout features of Wavelit is its seamless integration with the MyWavePlatform.
