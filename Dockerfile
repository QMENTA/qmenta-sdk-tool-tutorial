FROM python:3.6
LABEL mantainer="QMENTA Inc."
WORKDIR '/root'

# Add tool script
COPY tool.py /root/tool.py

# Install and upgrade all the required libraries and tools (in this case only python libraries are needed)
RUN python -m pip install --upgrade pip
RUN python -m pip install pyradiomics SimpleITK nibabel numpy pandas qmenta-sdk-lib

# Configure entrypoint
RUN python -m qmenta.sdk.make_entrypoint /root/entrypoint.sh /root/
RUN chmod +x /root/entrypoint.sh