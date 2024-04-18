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
# activate your virtualenv
$ pip install -U pip
$ gh repo clone caracal-pipeline/stimela
$ gh repo clone caracal-pipeline/cult-cargo
$ pip install -e stimela
$ pip install -e cult-cargo
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

## Using cult-cargo as a standalone image repository

You don't even need to run stimela (or indeed install anything) to take advantage of the images packaged with cult-cargo. Take a look at the image repository on https://quay.io/organization/stimela2 to see what's available.

For example, if you want to run a wsclean image, just do:

```
$ singularity build wsclean-3.3.sif docker:quay.io/stimela2/wsclean:3.3-cc0.1.2
$ singularity exec wsclean-3.3.sif wsclean 
```
