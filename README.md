# QMENTA SDK TOOL TUTORIAL

<img src="assets/qmenta_logo.png" alt="QMENTA" style="width: 50%">

---

## Introduction

TODO: First link this repo to the documentation page
TODO: Rewrite introduction more along the lines of the documentation

In this repository we will guide you through the process of deploying a tool into the [QMENTA platform](https://client.qmenta.com/#/login) and then run it.

To get more detailed and technical information about the QMENTA SDK and its capabilities, please refer to it's [documentation](https://docs.qmenta.com/sdk/).

As a case study, we will implement a tool that takes as inputs an oncology medical image and a segmentation mask with one or more labels, and then it uses the [Pyradiomics library](https://pyradiomics.readthedocs.io/en/latest/index.html) to extract radiomic features from the data. 
The tool will allow the user to select which classes of radiomic features wants to compute and also select.

Pyradiomics is an open-source python package for the extraction of Radiomics features from medical imaging. To learn more about the aim of the project and the features of the package take a look to the following publication: [van Griethuysenet al. 2017](https://doi.org/10.1158/0008-5472.CAN-17-0339)

TODO: Decide relevant sections

## Test the SDK tool in a Docker container

```
python test_container_sdk.py qmenta-sdk-tutorial:1.0 ./data/input ./data/output/ --settings settings.json --values settings_values.json
```