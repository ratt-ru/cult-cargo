FROM {CULT_REGISTRY}/base-cult:base-cc{CULT_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install apt-utils && \
    apt-get install -y casacore-data casacore-tools python{VERSION} python3-pip python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

# upgrade pip
RUN pip install --no-cache-dir -U pip setuptools wheel 

# add useful astro stuff
RUN pip install --no-cache-dir \
    python-casacore astropy astroplan regions astro-tigger-lsm \
    owlcat dask-ms scipy omegaconf bdsf msutils

# change this to master or release version when ready
RUN pip install --no-cache-dir git+https://github.com/caracal-pipeline/stimela@2.0rc10

RUN ln -s /usr/bin/python{VERSION} /usr/bin/python

CMD /usr/bin/python{VERSION}

