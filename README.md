# QMENTA SDK Tool Tutorial

<img src="assets/qmenta_logo.png" alt="QMENTA" style="width: 50%">

---

This repository contains the data, code, scripts and configuration files associated with the [Getting Started tutorial](https://docs.qmenta.com/sdk/getting_started.html) in the [QMENTA SDK documentation](https://docs.qmenta.com/sdk/) portal.

## Description

The tutorial helps you learn the foundations of using the QMENTA SDK and the technological ecosystem around it,
including Docker and the [QMENTA platform](https://client.qmenta.com/#/login).

### ANTs example

The tutorial goes partially over the [ANTs Tutorial](https://github.com/ANTsX/ANTsPy/blob/master/tutorials/10minTutorial.ipynb)
implementation, originally implemented as a Python notebook, into a QMENTA tool. 
The implementation will allow the user to select which processing steps to perform and also select a
variety of parameters for segmenting the images. The example will use a pair of T1-weighted MRI brain slices as input data. The tool will expose
several configurable input settings. In the QMENTA Platform interface the will allow the user to select which ANTs processing steps
to execute:

* Perform bias field correction
* Run tissue segmentation
* Compute cortical thickness
* Register two images using non-linear registration

The tissue segmentation step must be executed before cortical thickness estimation, 
as the latter depends on the segmentation results. For this reason, these two steps are linked within the workflow. 

All other steps are independent and can be run separately.

The resulting tool will extract some statistics, segment anatomical neuroimaging data (2D slice) and report the 
segmentation results in the online viewer, demonstrating how an existing analysis workflow can be 
transformed into a reusable and deployable QMENTA tool.

The tutorial can be found in the [QMENTA SDK documentation](https://docs.qmenta.com/sdk/tool_tutorial.html)

### Pyradiomics example [deprecated]

> The _pyradiomics_ library is only compatible with Python versions 3.5, 3.6, and 3.7, which are not supported by the QMENTA SDK. As a result, this tool may not function as expected. Nevertheless, it serves as a useful example of how to work with the QMENTA SDK directly, without relying on the Tool Maker features.

The tutorial goes over the implementation of a tool that takes as inputs an oncology medical image and a segmentation mask with one or more labels, and then uses the [pyradiomics library] to extract radiomic features from the data.
The tool will allow the user to select which classes of radiomic features they want to compute and also select a
variety of image filters to be applied before extracting the radiomic features.

[pyradiomics library]: https://pyradiomics.readthedocs.io/en/latest/

Pyradiomics is an open-source Python package for the extraction of radiomic features from medical images.
To learn more about the aim of the project and the features of the package you can read the following [publication](https://doi.org/10.1158/0008-5472.CAN-17-0339).

> Van Griethuysen, Joost JM, Andriy Fedorov, Chintan Parmar, Ahmed Hosny, Nicole Aucoin, Vivek Narayan, Regina GH Beets-Tan, Jean-Christophe Fillion-Robin, Steve Pieper, and Hugo JWL Aerts. "Computational radiomics system to decode the radiographic phenotype." Cancer research 77, no. 21 (2017): e104-e107.
