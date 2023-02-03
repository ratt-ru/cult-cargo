# cult-cargo
Curated Stimela2 cargo for popular radio astronomy software

## Regular install

PyPI package coming soon, then you can do

```
pip install cult-cargo
```

...to install both Stimela2 and cult-cargo.

## Dev-mode install

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
