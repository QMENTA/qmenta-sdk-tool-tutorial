FROM ubuntu:20.04

ENV WORKDIR "/root/"

RUN apt-get update
RUN apt-get install -y python3-pip python-dev build-essential
RUN pip install --upgrade pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
# Does it require any specific 3rd party tool? Install here.

# Install requirements and dependencies (both treated as normal python packages)
COPY requirements.txt ${WORKDIR}/requirements.txt

RUN pip install -r ${WORKDIR}/requirements.txt

# Add tool script
RUN mkdir -p ${WORKDIR}/
COPY tool.py ${WORKDIR}/tool.py

# Configure entrypoint
RUN ln -fs /usr/bin/python3 /usr/bin/python \
    && ln -fs /usr/bin/pip3 /usr/bin/pip

RUN python -m qmenta.sdk.make_entrypoint ${WORKDIR}/entrypoint.sh ${WORKDIR}/
RUN chmod +x ${WORKDIR}/entrypoint.sh