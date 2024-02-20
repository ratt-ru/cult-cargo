FROM {REGISTRY}/{base_python_image}-{BUNDLE_VERSION}

RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir {package}

CMD {CMD}
