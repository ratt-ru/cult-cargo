FROM {REGISTRY}/ddfacet:{BUNDLE_VERSION}

{pre_install}

RUN {python} -mpip install --use-pep517 --no-cache-dir {package} {extra_deps}

{post_install}

CMD ["kMS.py"]
