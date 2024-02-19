# cult-cargo
Curated Stimela2 cargo for popular radio astronomy software.

## Regular userland install

```
pip install cult-cargo
```

This installs both cult-cargo and the required version of stimela.

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

## Sample recipe

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

This makes the ``build-cargo.py`` script available. The script is preconfigured to read ``cultcargo/builder/cargo-manifest.yml``, which describes the images that must be built.

``build-cargo.py -a`` will build and push all images, or specify an image name to build a particular one. Use ``-b`` to build but not push, or ``-p`` for push-only. Use ``-l`` to list available images.

The ``cultcargo`` folder contains YaML files with cab definitions.

If you would like to maintain your own image collection, write your own manifest and Dockerfiles following the cult-cargo example, and use the ``build-cargo.py`` script to build your images.
