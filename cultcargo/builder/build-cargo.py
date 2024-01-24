#!/usr/bin/env python

import sys
import click
import os.path
import subprocess
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from omegaconf import OmegaConf
from rich import print

DEFAULT_MANIFEST = os.path.join(os.path.dirname(__file__), "cargo-manifest.yml")

BASE_IMAGES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

@dataclass
class ImageInfo(object):
    versions: Dict[str, Dict[str, Any]]              # mapping of versions
    assign: Optional[Dict[str, Any]] = None       # optional assignments
    latest: Optional[str] = None                  # latest version -- use last 'versions' entry if not given
    dockerfile: Optional[str] = None

@dataclass
class Manifest(object):
    registry: str
    assign: Optional[Dict[str, Any]]
    images: Dict[str, ImageInfo]


def run(command, cwd=None, input=None):
    print(f"[bold]{cwd or '.'}$ {command}[/bold]")
    args = command.split()
    result = subprocess.run(args, cwd=cwd, input=input, text=True)
    if result.returncode:
        print(f"{command} failed with exit code {result.returncode}")
        sys.exit(1)
    return 0


@click.command()
@click.option('-m', '--manifest', type=click.Path(exists=True), 
                default=DEFAULT_MANIFEST, 
                help=f'Cargo manifest. Default is {DEFAULT_MANIFEST}.')
@click.option('-b', '--build', is_flag=True, help='Build only, do not push.')
@click.option('-p', '--push', is_flag=True, help='Push only, do not build.')
@click.option('-r', '--rebuild', is_flag=True, help='Ignore docker image caches (i.e. rebuild).')
@click.option('-a', '--all', is_flag=True, help='Build and/or push all images in manifest.')
@click.argument('imagenames', type=str, nargs=-1)
def build_cargo(manifest: str, build=False, push=False, all=False, rebuild=False, imagenames: List[str] = []):
    if not (build or push):
        build = push = True

    print(f"Loading manifest {manifest}")

    conf = OmegaConf.load(manifest)
    conf = OmegaConf.merge(OmegaConf.structured(Manifest), conf)

    print(f"Loaded {len(conf.images)} image entries")

    if all:
        imagenames = list(conf.images.keys())

    no_cache = "--no-cache" if rebuild else ""

    if not imagenames:
        print(f"Nothing to be done. Please specify some image names, or run with -a/-all.")
        return 0
    
    for image in imagenames:
        version = None
        if ':' in image:
            image, version = image.split(":", 1)
        if image not in conf.images:
            print(f"Unknown image '{image}'")
            return 1
        if version is not None and version not in conf.images[image].versions:
            print(f"Unknown image '{image}:{version}'")
            return 1
        
    global_vars = conf.assign or {}
    registry = global_vars.get('CULT_REGISTRY', 'quay.io/stimela2')
    CULT_VERSION = global_vars.get('CULT_VERSION')

    for image in imagenames:
        if ':' in image:
            image, version = image.split(":", 1)
            versions = [version]
            all_versions = False
        else:
            versions = conf.images[image].versions.keys()
            all_versions = True

        image_info = conf.images[image]
        image_vars = global_vars.copy()
        image_vars.update(IMAGE=image, **(image_info.assign or {}))
        image_vars.setdefault("CMD", image)

        path = os.path.join(BASE_IMAGES, image).format(**image_vars)
        latest = None

        for version in versions:
            version = version.format(**image_vars)
            version_info = image_info.versions[version]
            version_info.setdefault('VERSION', version)

            version_vars = image_vars.copy()
            version_vars.update(**version_info)
            
            dockerfile = version_info.get('dockerfile') or image_info.dockerfile or 'Dockerfile'
            dockerfile = dockerfile.format(**version_vars)
            image_version = version_info.VERSION.format(**version_vars)
            if image_version == "latest":
                latest = image_version = f"cc{CULT_VERSION}"
            else:
                image_version += f"-cc{CULT_VERSION}"

            dockerpath = os.path.join(path, dockerfile)
            print(f"[bold green]{image}:{image_version}[/bold green] defined by {dockerpath}")
            if not os.path.exists(dockerpath):
                print(f"  {dockerpath} doesn't exist")
                return 1
            # go build
            build_dir = os.path.dirname(dockerpath)
            full_image = f"{registry}/{image}:{image_version}"
            if build:
                content = open(dockerpath, "rt").read().format(**version_vars)
                run(f"docker build {no_cache} -t {full_image} -", cwd=build_dir, input=content)
            if push:
                run(f"docker push {full_image}", cwd=path)

        if all_versions and versions:
            if latest is None:
                latest = image_version  # use last version from loop above
                run(f"docker tag {registry}/{image}:{latest} {registry}/{image}:cc{CULT_VERSION}", cwd=build_dir)
                if push:
                    run(f"docker push {registry}/{image}:cc{CULT_VERSION}", cwd=path)
            run(f"docker tag {registry}/{image}:cc{CULT_VERSION} {registry}/{image}:latest", cwd=build_dir)
            if push:
                run(f"docker push {registry}/{image}:latest", cwd=path)



if __name__ == '__main__':
    build_cargo()