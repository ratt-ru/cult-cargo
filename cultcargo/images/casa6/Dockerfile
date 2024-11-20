FROM {REGISTRY}/base-cult:{BUNDLE_VERSION}

RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN pip install --no-cache-dir casatools=={wheel_version} casatasks=={wheel_version} casadata

CMD /usr/bin/python3.8

