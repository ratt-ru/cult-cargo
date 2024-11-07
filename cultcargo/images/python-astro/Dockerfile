FROM {REGISTRY}/base-cult:base-{BUNDLE_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-add-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install apt-utils && \
    apt-get install -y casacore-data casacore-tools python{VERSION}-dev python{VERSION}-distutils \
    python3-pip python3-pytest python3-matplotlib curl\
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN update-alternatives --install /usr/bin/python python /usr/bin/python{VERSION} 1

# needed to upgrade pip properly -- sometimes it gets stuck and is unable to upgrade itself
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python{VERSION}

RUN python{VERSION} -mpip install --no-cache-dir -U pip setuptools wheel 

# add useful astro stuff
RUN python{VERSION} -mpip install --no-cache-dir \
    python-casacore astropy astroplan regions astro-tigger-lsm \
    owlcat dask-ms scipy omegaconf bdsf msutils

# add stimela -- useful for scabha.schema_utils
RUN python{VERSION} -mpip install --no-cache-dir "stimela>=2.0rc17"

CMD /usr/bin/python{VERSION}

