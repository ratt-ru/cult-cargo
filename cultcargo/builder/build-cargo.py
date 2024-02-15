#!/usr/bin/env python
import json
import sys
import click
import requests
import os.path
import re
import subprocess
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from omegaconf import OmegaConf
from rich.console import Console
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
import importlib
import importlib.metadata


DEFAULT_MANIFEST = os.path.join(os.path.dirname(__file__), "cargo-manifest.yml")


@dataclass
class ImageInfo(object):
    versions: Dict[str, Dict[str, Any]]              # mapping of versions
    assign: Optional[Dict[str, Any]] = None       # optional assignments
    latest: Optional[str] = None                  # latest version -- use last 'versions' entry if not given
    dockerfile: Optional[str] = None

@dataclass
class Manifest(object):
    @dataclass
    class Metadata(object):
        PACKAGE: str
        REGISTRY: str
        BUNDLE_VERSION: str
        BUNDLE_VERSION_PREFIX: str = ""
        BASE_IMAGE_PATH: str = "images"
        PACKAGE_VERSION: str = "auto"
        GITHUB_REPOSITORY: str = ""

    metadata: Metadata
    assign: Dict[str, Any] 
    images: Dict[str, ImageInfo]


def run(command, cwd=None, input=None):
    print(f"[bold]{cwd or '.'}$ {command}[/bold]")
    args = command.split()
    result = subprocess.run(args, cwd=cwd, input=input, text=True)
    if result.returncode:
        print(f"{command} failed with exit code {result.returncode}")
        sys.exit(1)
    return 0

console = Console(highlight=False)
print = console.print


@click.command()
@click.option('-m', '--manifest', type=click.Path(exists=True), 
                default=DEFAULT_MANIFEST, 
                help=f'Cargo manifest. Default is {DEFAULT_MANIFEST}.')
@click.option('--list', 'do_list', is_flag=True, help='Build only, do not push.')
@click.option('-b', '--build', is_flag=True, help='Build only, do not push.')
@click.option('-p', '--push', is_flag=True, help='Push only, do not build.')
@click.option('-r', '--rebuild', is_flag=True, help='Ignore docker image caches (i.e. rebuild).')
@click.option('-a', '--all', is_flag=True, help='Build and/or push all images in manifest.')
@click.option('-v', '--verbose', is_flag=True, help='Be verbose.')
@click.argument('imagenames', type=str, nargs=-1)
def build_cargo(manifest: str, do_list=False, build=False, push=False, all=False, rebuild=False, verbose=False, imagenames: List[str] = []):
    if not (build or push):
        build = push = True

    with Progress(
            TimeElapsedColumn(),
            SpinnerColumn(),
            "{task.description}",
            console=console) as progress:
        print = progress.console.print

        progress_task = progress.add_task("loading manifest")

        print(Rule(f"Loading manifest {manifest}"))

        conf = OmegaConf.load(manifest)
        conf = OmegaConf.merge(OmegaConf.structured(Manifest), conf)

        # get package version
        if conf.metadata.PACKAGE_VERSION == "auto":
            conf.metadata.PACKAGE_VERSION = importlib.metadata.version(conf.metadata.PACKAGE)

        print(f"Package is {conf.metadata.PACKAGE}=={conf.metadata.PACKAGE_VERSION}")
        is_candidate_release = re.match(".*rc(\d+)", conf.metadata.PACKAGE_VERSION)
        if is_candidate_release:
            print("  (this is a release candidate)")

        package_releases = {}
        current_release = None

        # check release version
        if not conf.metadata.GITHUB_REPOSITORY:
            print("[yellow]GITHUB_REPOSITORY not set in manifest -- disabling release version checks[/yellow]")
        else:
            print(f"Checking github releases for {conf.metadata.GITHUB_REPOSITORY}")
            url = f'https://api.github.com/repos/{conf.metadata.GITHUB_REPOSITORY}/releases'
            # Make the GET request
            response = requests.get(url)
            # Check if the request was successful
            if response.status_code == 200:
                releases = response.json()  # Parse the JSON response
                for release in releases:
                    package_releases[release['tag_name']] = release
                print(f"  Available releases: {' '.join(sorted(package_releases.keys()))}")
                current_release = package_releases.get(conf.metadata.PACKAGE_VERSION)
                if current_release:
                    if is_candidate_release:
                        print("  [green]Working with a public release candidate, build/push allowed.[/green]")
                    else:
                        print("  [red]Working with a public release. Build/push restricted to new images only.[/red]")
                else:
                    print("  [green]Working with an unreleased version, build/push allowed.[/green]")
            else:
                print("  [yellow]Failed to fetch release info: {response.status_code}[/yellow]")
                sys.exit(1)


        # get registry
        def resolve_config_reference(value):
            comps =  value.split("::")
            if len(comps) == 3:
                module = importlib.import_module(comps[0])
                container = OmegaConf.load(f"{os.path.dirname(module.__file__)}/{comps[1]}")
                try:
                    for key in comps[2].split('.'):
                        container = container[key]
                except:
                    raise KeyError(f"{comps[2]} not found in {comps[1]}")
                return container
            return value
                
        conf.metadata.REGISTRY = resolve_config_reference(conf.metadata.REGISTRY)
        conf.metadata.BUNDLE_VERSION = resolve_config_reference(conf.metadata.BUNDLE_VERSION)
        print(f"Registry is {conf.metadata.REGISTRY}, bundle is '{conf.metadata.BUNDLE_VERSION}', prefix '{conf.metadata.BUNDLE_VERSION_PREFIX}'")
        if not conf.metadata.BUNDLE_VERSION.startswith(conf.metadata.BUNDLE_VERSION_PREFIX):
            print("Inconsistent manifest metadata: BUNDLE_VERSION must start with BUNDLE_VERSION_PREFIX")
            return 1
        
        unprefixed_image_version = conf.metadata.BUNDLE_VERSION[len(conf.metadata.BUNDLE_VERSION_PREFIX):]
        
        if '::' in conf.metadata.BASE_IMAGE_PATH:
            modname, path = conf.metadata.BASE_IMAGE_PATH.split('::', 1)
            pkg_path = os.path.dirname(importlib.import_module(modname).__file__)
            conf.metadata.BASE_IMAGE_PATH = os.path.join(pkg_path, path)

        print(f"Base image path is {conf.metadata.BASE_IMAGE_PATH}")

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
            
        global_vars = OmegaConf.merge(dict(**conf.metadata), conf.assign)
        registry = global_vars.REGISTRY
        BUNDLE_VERSION = global_vars.BUNDLE_VERSION

        for i_image,image in enumerate(imagenames):
            progress.update(progress_task, description=f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]")

            print(Rule(f"Processing image {image}"))
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

            path = os.path.join(global_vars.BASE_IMAGE_PATH, image).format(**image_vars)
            latest = None
            built_or_pushed_versions = set()

            for i_version, version in enumerate(versions):
                progress.update(progress_task, description=
                    f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]: "
                    f"version [bold]{version}[/bold] [{i_version}/{len(versions)}]")

                version = version.format(**image_vars)
                version_info = image_info.versions[version]
                version_info.setdefault('VERSION', version)

                version_vars = image_vars.copy()
                version_vars.update(**version_info)
                
                dockerfile = version_info.get('dockerfile') or image_info.dockerfile or 'Dockerfile'
                dockerfile = dockerfile.format(**version_vars)
                image_version = version_info.VERSION.format(**version_vars)
                if image_version == "latest":
                    latest = image_version = f"{BUNDLE_VERSION}"
                else:
                    image_version += f"-{BUNDLE_VERSION}"
                full_image = f"{registry}/{image}:{image_version}"
                remote_image_exists = True

                # find Dockerfile for this image
                dockerpath = os.path.join(path, dockerfile)
                print(f"[bold]{image}:{image_version}[/bold] defined by {dockerpath}")
                if not os.path.exists(dockerpath):
                    print(f"  {dockerpath} doesn't exist")
                    return 1
                build_dir = os.path.dirname(dockerpath)

                # check if remote image exists
                if push or build:
                    print(f"Checking if registry already contains {full_image}")
                    cmd = ['docker', 'manifest', 'inspect', full_image]
                    try:
                        print(f"  [bold]$ {' '.join(cmd)}[/bold]", highlight=False)
                        # Execute the command
                        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                        print(f"  Manifest returned for {full_image}")
                    except subprocess.CalledProcessError as e:
                        output = e.stderr.strip() 
                        if "no such manifest" in output or "was deleted" in output:
                            print(f"  {output}")
                            print(f"  [green]No manifest returned for {full_image}, ok to build/push[/green]")
                            remote_image_exists = False
                        else:
                            print(f"  Error inspecting manifest: {e.stderr}")
                            sys.exit(1)

                    # check for build protection
                    if remote_image_exists:
                        if unprefixed_image_version != conf.metadata.PACKAGE_VERSION:
                            print(f"  [red]Package version doesn't match image version, and image already exists. Refusing to rebuild/push this image.[/red]")
                            continue
                        if current_release:
                            if not is_candidate_release:
                                print(f"  [red]Package released, and image already exists. Refusing to rebuild/push this image.[/red]")
                                continue
                            else:
                                print(f"  Package is a release candidate, ok to rebuild/push image")
                        else:
                            print(f"  Package unreleased, ok to rebuild/push image")

                        cmd = ['docker', 'pull', full_image]
                        try:
                            print(f"  [bold]$ {' '.join(cmd)}[/bold]")
                            # Execute the command
                            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, check=True)
                        except subprocess.CalledProcessError as e:
                            print(f"  Error pulling image: {e.stderr}")
                            sys.exit(1)
                
                # go build
                if build:
                    content = open(dockerpath, "rt").read().format(**version_vars)
                    if verbose:
                        print(f"Dockerfile:", style="bold")
                        print(f"{content}", style="dim", highlight=True)
                    run(f"docker build {no_cache} -t {full_image} -", cwd=build_dir, input=content)
                    built_or_pushed_versions.add(version)
                if push:
                    run(f"docker push {full_image}", cwd=path)
                    built_or_pushed_versions.add(version)
                    
            progress.update(progress_task, description=
                f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]: tagging latest version")

            # apply :latest tag to images
            if all_versions and built_or_pushed_versions:
                if latest is None:
                    latest = image_version  # use last version from loop above
                    run(f"docker tag {registry}/{image}:{latest} {registry}/{image}:{BUNDLE_VERSION}", cwd=build_dir)
                    if push:
                        run(f"docker push {registry}/{image}:{BUNDLE_VERSION}", cwd=path)
                run(f"docker tag {registry}/{image}:{BUNDLE_VERSION} {registry}/{image}:latest", cwd=build_dir)
                if push:
                    run(f"docker push {registry}/{image}:latest", cwd=path)

    print("Success!", style="green")


if __name__ == '__main__':
    build_cargo()