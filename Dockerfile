# Start from a QMENTA public container containing python 3, qmenta-sdk library and a configured entrypoint.
FROM qmentasdk/minimal:latest

#Copy the tool script to the container.
COPY tool.py /root/tool.py

# Install all the required libraries and tools (in this case only python libraries are needed).
RUN pip install SimpleITK nibabel numpy pandas
RUN python -m pip install pyradiomics