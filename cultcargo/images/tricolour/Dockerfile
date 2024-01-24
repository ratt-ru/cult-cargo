FROM {CULT_REGISTRY}/base-cult:base-cc{CULT_VERSION}

RUN pip install -U pip setuptools wheel

{pre_install}

RUN pip install --no-cache-dir {package} {extra_deps}

{post_install}

CMD {CMD}
