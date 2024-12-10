FROM {REGISTRY}/base-cult:{BUNDLE_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-add-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install apt-utils && \
    apt-get install -y casacore-data casacore-tools python{VERSION}-dev python{VERSION}-distutils \
    python3-pip python3-pytest python3-matplotlib curl\
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

RUN update-alternatives --install /usr/bin/python python /usr/bin/python{VERSION} 1

# # needed to upgrade pip properly -- sometimes it gets stuck and is unable to upgrade itself
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python{VERSION}

RUN python{VERSION} -m pip install --no-cache-dir -U setuptools wheel packaging

CMD /usr/bin/python{VERSION}

