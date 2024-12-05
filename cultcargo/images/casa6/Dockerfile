FROM {REGISTRY}/base-cult:{BUNDLE_VERSION}

RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN pip install --no-cache-dir casatools=={wheel_version} casatasks=={wheel_version} casaconfig

RUN mkdir -p /opt/casa/data

COPY casasiteconfig.py /opt/casa

RUN {python} -m casaconfig --measurespath /opt/casa/data --update-all

RUN {python} -m casaconfig --measurespath /opt/casa/data --current-data

CMD /usr/bin/{python}
