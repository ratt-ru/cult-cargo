FROM {REGISTRY}/python-base:{VERSION}-{BUNDLE_VERSION}

# add useful astro stuff
RUN python{VERSION} -m pip install --no-cache-dir \
    python-casacore astropy astroplan regions astro-tigger-lsm \
    owlcat dask-ms scipy omegaconf bdsf msutils \
    stimela

CMD python{VERSION}

