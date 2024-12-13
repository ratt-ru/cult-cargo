FROM {REGISTRY}/casa:_base-{BUNDLE_VERSION}

RUN wget -nv {url}/{tarball} && tar zxf {tarball} && rm {tarball}

RUN ln -s {entrypoint} /usr/local/bin

ENV LC_ALL=C

CMD {entrypoint} --help