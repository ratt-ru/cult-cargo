FROM {CULT_REGISTRY}/python-astro:3.8-cc{CULT_VERSION}

RUN pip install -U pip setuptools wheel

{pre_install}

RUN pip install --no-cache-dir {package} {extra_deps}

{post_install}

CMD {CMD}
