# Start from the following base image

FROM qmentasdk/minimal:latest

COPY tool.py /root/tool.py

RUN pip install SimpleITK nibabel numpy pandas

RUN python -m pip install pyradiomics

