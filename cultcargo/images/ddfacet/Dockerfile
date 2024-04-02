FROM {REGISTRY}/{base_python_image}-{BUNDLE_VERSION}

RUN apt-get update && \
    apt-get -y install \
        dpkg-dev \
        libc-dev \
        cmake \
        git \
        wget \
        subversion \
        rsync \
        python3-virtualenv \
        python3-pip \
        libfftw3-dev \
        python3-numpy \
        libfreetype6 \
        libfreetype6-dev \
        libpng-dev \
        pkg-config \
        python3-dev \
        libboost-all-dev \
        libcfitsio-dev \
        libhdf5-dev \
        wcslib-dev \
        libatlas-base-dev \
        liblapack-dev \
        python3-tk \
        libreadline6-dev \
        subversion \
        liblog4cplus-dev \
        libhdf5-dev \
        libncurses5-dev \
        flex \
        bison \
        libbison-dev \
        libqdbm-dev \
        libgsl-dev \
        make \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives 

{pre_install}

RUN {python} -mpip install --use-pep517 --no-cache-dir -U matplotlib dask-ms python-casacore casadata 
RUN {python} -mpip install --use-pep517 --no-cache-dir {package} {extra_deps}

{post_install}

CMD ["DDF.py"]
