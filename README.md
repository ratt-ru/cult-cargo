# cult-cargo
Curated Stimela2 cargo for popular radio astronomy software

## Regular userland install

PyPI package coming soon, then you can do

```
pip install cult-cargo
```

...to install both Stimela2 and cult-cargo.

## Poweruser install

To work off the repo versions:

```
# activate virtualenv
$ pip install poetry
$ gh repo clone caracal-pipeline/stimela
$ cd stimela
$ poetry install
$ cd ..
$ gh repo clone caracal-pipeline/cult-cargo
$ cd cult-cargo
$ poetry install
```

Sample recipe:

```yml
#!/usr/bin/env -S stimela run -l
_include: 
  - (cultcargo)wsclean.yml

dummy-recipe:
  info: a dummy recipe
  steps:
    image:
      cab: wsclean
```

## Cab developers install

```
$ poetry install --with builder
```

This makes the ``builder/build-cargo.py`` script available. The script is configured with ``builder/cargo-manifest.yml``, which describes the images that must be built.

``build-cargo.py -a`` will build and push all images, or specify an image name to build a particular one. Use ``-b`` to build but not push, or ``-p`` for push-only.

The ``cultcargo`` folder contains yml files with cab definitions.

If you would like to maintain your own image collection, write your own manifest and Dockerfiles following the cult-cargo example, then use the ``build-cargo.py`` script to build your images.
