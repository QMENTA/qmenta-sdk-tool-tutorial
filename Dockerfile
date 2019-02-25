# Start from the following base image

FROM qmentasdk/minimalpy2:latest

COPY /home/guillem/dev/qmenta-sdk-tool-tutorial/tool.py /root/tool.py

# Execute some commands
RUN pip install SimpleITK, nibabel, numpy, pandas, radiomics, radiomics
