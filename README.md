# QMENTA SDK Tool Tutorial

<img src="assets/qmenta_logo.png" alt="QMENTA" style="width: 50%">

---

This repository contains the data, code, scripts and configuration files associated with the [Getting Started tutorial](https://docs.qmenta.com/sdk/getting_started.html) in the [QMENTA SDK documentation](https://docs.qmenta.com/sdk/) portal.

## Description

The tutorial helps you learn the foundations of using the QMENTA SDK and the technological ecosystem around it,
including Docker and the [QMENTA platform](https://client.qmenta.com/#/login).

### ANTs example

As a case study, the tutorial goes partially over the [ANTs Tutorial](https://github.com/ANTsX/ANTsPy/blob/master/tutorials/10minTutorial.ipynb)
implementation. The implementation will allow the user to select which processing steps to perform and also select a
variety of parameters for segmenting the images.
If you want to start this tool example, please follow the instructions for ANTsPy on their official
documentation website first: [antspyx library]: https://github.com/antsx/antspy/blob/master/tutorials/Installation.md
The tutorial can be found in the [QMENTA SDK documentation](https://docs.qmenta.com/sdk/tool_tutorial.html)

### Pyradiomics example

Next, the tutorial goes over the implementation of a tool that takes as inputs an oncology medical image and a segmentation mask with one or more labels, and then uses the [pyradiomics library] to extract radiomic features from the data.
The tool will allow the user to select which classes of radiomic features they want to compute and also select a
variety of image filters to be applied before extracting the radiomic features.

[pyradiomics library]: https://pyradiomics.readthedocs.io/en/latest/

Pyradiomics is an open-source Python package for the extraction of radiomic features from medical images.
To learn more about the aim of the project and the features of the package you can read the following [publication](https://doi.org/10.1158/0008-5472.CAN-17-0339).

> Van Griethuysen, Joost JM, Andriy Fedorov, Chintan Parmar, Ahmed Hosny, Nicole Aucoin, Vivek Narayan, Regina GH Beets-Tan, Jean-Christophe Fillion-Robin, Steve Pieper, and Hugo JWL Aerts. "Computational radiomics system to decode the radiographic phenotype." Cancer research 77, no. 21 (2017): e104-e107.
