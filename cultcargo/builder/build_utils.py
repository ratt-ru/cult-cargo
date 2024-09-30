import os
from typing import Any
from omegaconf import OmegaConf, DictConfig


ENVVAR_SYNTAX = "ENV::"

def substitute_environment_variables(element: Any):
    """Find and replace occurences of environment varaibles in dict values."""
    if isinstance(element, (dict, DictConfig)):
        for k, v in element.items():
            element[k] = substitute_environment_variables(v)
    elif isinstance(element, str) and element.startswith(ENVVAR_SYNTAX):
        envvar = element.lstrip(ENVVAR_SYNTAX)
        if envvar not in os.environ:
            raise KeyError(f"Environment variable {envvar} is not set.")
        return os.environ[envvar]
    return element

def resolve_version_substitutions(config):
    """Resolve version substitutions using metadata and assign sections."""
    
    for image_name, image in config.images.items():

        lookup_dict = OmegaConf.merge(dict(**config.metadata), config.assign)
        lookup_dict.update(**(image.assign or {}))
    
        resolved_versions = {}  # Recreate to preserve ordering.
        for version_name, version in image.versions.items():
            try:
                resolved_name = version_name.format(**lookup_dict)
            except KeyError as e:
                msg = (
                    f"Unable to resolve substitution '{version_name}' in "
                    f"versions field of manifest for image '{image_name}'."
                )
                raise Exception(msg) from e
            resolved_versions[resolved_name] = version

        image.versions = resolved_versions

    return

