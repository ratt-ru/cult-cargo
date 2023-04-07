FROM {CULT_REGISTRY}/casa:_base

RUN wget -nv {url}/{tarball} && tar zxf {tarball} && rm {tarball}

CMD {entrypoint}