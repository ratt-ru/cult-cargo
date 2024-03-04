FROM {REGISTRY}/base-cult:base-{BUNDLE_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install apt-utils && \
    apt-get install -y casacore-data casacore-tools python{VERSION}-dev \
    python3-pip python3-pytest python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN update-alternatives --install /usr/bin/python python /usr/bin/python{VERSION} 1

# upgrade pip
RUN python{VERSION} -mpip install --no-cache-dir -U pip setuptools wheel 

# add useful astro stuff
RUN python{VERSION} -mpip install --no-cache-dir \
    python-casacore astropy astroplan regions astro-tigger-lsm \
    owlcat dask-ms scipy omegaconf bdsf msutils

# add stimela -- useful for scabha.schema_utils
RUN python{VERSION} -mpip install --no-cache-dir git+https://github.com/caracal-pipeline/stimela@2.0rc12

CMD /usr/bin/python{VERSION}

