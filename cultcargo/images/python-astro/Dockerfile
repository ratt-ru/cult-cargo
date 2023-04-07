FROM {CULT_REGISTRY}/base-cult:base-cc{CULT_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install apt-utils && \
    apt-get install -y casacore-data python{VERSION} python3-pip python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN pip install -U 'numpy<1.24'   # <1.24 for numba

RUN pip install --no-cache-dir python-casacore astropy astroplan astro-tigger-lsm owlcat dask-ms \
    dask-ms scipy omegaconf

CMD /usr/bin/python{VERSION}

