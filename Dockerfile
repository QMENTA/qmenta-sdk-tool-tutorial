# Start from a QMENTA public container containing python 3, qmenta-sdk library and a cofigured entrypoint.
FROM qmentasdk/minimal:latest

#Copy the tool script to the container
COPY tool.py /root/tool.py

# Install all the python libraries that the tool requires
RUN pip install SimpleITK nibabel numpy pandas
RUN python -m pip install pyradiomics