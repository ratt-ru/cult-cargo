FROM {REGISTRY}/base-cult:base-{BUNDLE_VERSION}

RUN pip install -U pip setuptools wheel

{pre_install}

RUN pip install --no-cache-dir {package} {extra_deps}

{post_install}

CMD {CMD}
