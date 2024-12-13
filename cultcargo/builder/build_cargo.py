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
try:
    from importlib import metadata
except ImportError: # for Python<3.8
    import importlib_metadata as metadata
from cultcargo.builder.build_utils import (
    substitute_environment_variables,
    resolve_version_substitutions
)



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
        print(f"[bold red]{command} failed with exit code {result.returncode}[/bold red]")
        sys.exit(1)
    return 0

console = Console(highlight=False)
print = console.print


@click.command()
@click.option('-m', '--manifest', type=click.Path(exists=True),
                default=DEFAULT_MANIFEST,
                help=f'Cargo manifest. Default is {DEFAULT_MANIFEST}.')
@click.option('-l', '--list', 'do_list', is_flag=True, help='List only, do not push or build. Returns error if images are missing.')
@click.option('-b', '--build', is_flag=True, help='Build only, do not push.')
@click.option('-p', '--push', is_flag=True, help='Push only, do not build.')
@click.option('-r', '--rebuild', is_flag=True, help='Ignore docker image caches (i.e. rebuild).')
@click.option('-a', '--all', is_flag=True, help='Build and/or push all images in manifest.')
@click.option('-E', '--experimental', is_flag=True, help='Enable experimental versions.')
@click.option('-v', '--verbose', is_flag=True, help='Be verbose.')
@click.option('--no-tests', is_flag=True, help='Skip image tests during the list or build.')
@click.option('--ignore-latest-tag', is_flag=True, help='Neither require nor apply latest tag.')
@click.option('--boring', is_flag=True, help='Be boring -- no progress bar.')
@click.argument('imagenames', type=str, nargs=-1)
def build_cargo(manifest: str, do_list=False, build=False, push=False, all=False, rebuild=False, boring=False,
                no_tests=False,
                experimental=False, ignore_latest_tag=False, verbose=False, imagenames: List[str] = []):
    if not (build or push or do_list):
        build = push = True

    with Progress(
            TimeElapsedColumn(),
            SpinnerColumn(),
            "{task.description}",
            console=console, disable=boring) as progress:
        print = progress.console.print

        progress_task = progress.add_task("loading manifest")

        print(Rule(f"Loading manifest {manifest}"))

        conf = OmegaConf.load(manifest)
        conf = OmegaConf.merge(OmegaConf.structured(Manifest), conf)

        # NOTE(JSKenyon): Replace environment varaibles with values. Currently,
        # this function does not traverse collections other than dictionaries.
        conf = substitute_environment_variables(conf)
        # NOTE(JSKenyon): Resolve versioning substitutions on images to make
        # manipulating the config more consistent between use-cases.
        resolve_version_substitutions(conf)

        # get package version
        if conf.metadata.PACKAGE_VERSION == "auto":
            conf.metadata.PACKAGE_VERSION = metadata.version(conf.metadata.PACKAGE)

        print(f"Package is {conf.metadata.PACKAGE}=={conf.metadata.PACKAGE_VERSION}")
        match = re.fullmatch("(.*)rc(\d+)", conf.metadata.PACKAGE_VERSION)
        if match:
            print("  (this is a release candidate)")
            candidate_base, candidate_release = match.groups()
        else:
            candidate_base = candidate_release = None

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
                    if candidate_release:
                        print("  [green]Working with a public release candidate, push allowed.[/green]")
                    else:
                        print("  [red]Working with a public release. Push restricted to new images only.[/red]")
                else:
                    print("  [green]Working with an unreleased version, push allowed.[/green]")
            else:
                print(f"  [red]Failed to fetch release info: {response.status_code}[/red]")
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
            sys.exit(1)

        unprefixed_image_version = conf.metadata.BUNDLE_VERSION[len(conf.metadata.BUNDLE_VERSION_PREFIX):]

        if '::' in conf.metadata.BASE_IMAGE_PATH:
            modname, path = conf.metadata.BASE_IMAGE_PATH.split('::', 1)
            pkg_path = os.path.dirname(importlib.import_module(modname).__file__)
            conf.metadata.BASE_IMAGE_PATH = os.path.join(pkg_path, path)

        print(f"Base image path is {conf.metadata.BASE_IMAGE_PATH}")

        print(f"Loaded {len(conf.images)} image entries")

        global_vars = OmegaConf.merge(dict(**conf.metadata), conf.assign)
        registry = global_vars.REGISTRY
        BUNDLE_VERSION = global_vars.BUNDLE_VERSION

        if all:
            imagenames = list(conf.images.keys())

        # Check latest versions in manifest for consistency
        # Each version's image is tagged VERSION-BUNDLE_VERSION (e.g. wsclean:3.0-cc0.1.2), and there also is an official
        # default/latest version tagged simlpy BUNDLE_VERSION. Three scenarios:
        # (a) The latest version can be defined explicitly, by calling it "latest".
        # (b) The image.latest field can be specified to tag a specific version as latest.
        # (c) The last version listed is tagged as latest.
        # In cases (b) and (c), an additional tag operation needs to be done, so the tag_latest
        # dict below is populated with the versions that need to be tagged.
        tag_latest = {}
        for image, image_info in conf.images.items():
            versions = list(image_info.versions.keys())
            if not versions:
                print(f"No versions defined for {image}")
                sys.exit(1)
            # figure out latest version - this will be tagged as BUNDLE_VERSION
            # explicitly specified?
            latest = image_info.latest
            if ignore_latest_tag:  # Skip latest tag logic.
                tag_latest[image] = None
            elif latest: # case (a)
                if "latest" in versions:
                    print(f"Image {image}: both 'latest' version and a latest tag defined, can't have both")
                    sys.exit(1)
                if latest not in versions:
                    print(f"Image {image}: latest tag refers to unknown version '{latest}'")
                    print(f"Known versions are: {versions}.")
                    sys.exit(1)
                tag_latest[image] = f"{latest}-{BUNDLE_VERSION}"  # case (b)
            elif "latest" not in versions:
                tag_latest[image] = f"{versions[-1]}-{BUNDLE_VERSION}"  # case (c)

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
                sys.exit(1)
            if version is not None and version not in conf.images[image].versions:
                print(f"Unknown image '{image}:{version}'")
                sys.exit(1)

        remote_images_exist = {}

        for i_image,image in enumerate(imagenames):
            progress.update(progress_task, description=f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]")

            print(Rule(f"Processing image {image}"))
            if ':' in image:
                image, version = image.split(":", 1)
                versions = [version]
            else:
                versions = conf.images[image].versions.keys()

            image_info = conf.images[image]
            image_vars = global_vars.copy()
            image_vars.update(IMAGE=image, **(image_info.assign or {}))
            image_vars.setdefault("CMD", f"{image} --help")

            path = os.path.join(global_vars.BASE_IMAGE_PATH, image).format(**image_vars)

            for i_version, version in enumerate(versions):
                progress.update(progress_task, description=
                    f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]: "
                    f"version [bold]{version}[/bold] [{i_version}/{len(versions)}]")

                if version == "latest":
                    image_version = BUNDLE_VERSION
                else:
                    image_version = f"{version}-{BUNDLE_VERSION}"

                version_info = image_info.versions[version]
                version_vars = image_vars.copy()
                version_vars.update(**version_info)
                version_vars["VERSION"] = version
                version_vars["IMAGE_VERSION"] = image_version

                is_exp = version_info.get('experimental')
                exp_deps = version_info.get('experimental_dependencies', [])

                if is_exp or exp_deps:
                    if not experimental:
                        print(f"[bold]{image}:{image_version}[/bold] is experimental and -E switch not given, skipping")
                        continue
                    # check dependencies
                    print(f"[bold]{image}:{image_version}[/bold] is experimental")
                    for dep in exp_deps:
                        if not os.path.exists(dep):
                            print(f"  [red]ERROR: dependency {dep} doesn't exist[/red]")
                            sys.exit(1)

                dockerfile = version_info.get('dockerfile') or image_info.dockerfile or 'Dockerfile'
                dockerfile = dockerfile.format(**version_vars)
                full_image = f"{registry}/{image}:{image_version}"
                remote_image_exists = True

                # find Dockerfile for this image
                dockerpath = os.path.join(path, dockerfile)
                print(f"[bold]{image}:{image_version}[/bold] defined by {dockerpath}")
                if not os.path.exists(dockerpath):
                    print(f"  {dockerpath} doesn't exist")
                    sys.exit(1)
                build_dir = os.path.dirname(dockerpath)

                # check if remote image exists
                if push or build or do_list:
                    print(f"Checking if registry already contains {full_image}")
                    cmd = ['docker', 'manifest', 'inspect', full_image]
                    try:
                        print(f"  [bold].$ {' '.join(cmd)}[/bold]", highlight=False)
                        # Execute the command
                        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                        print(f"  Manifest returned for {full_image}")
                    except subprocess.CalledProcessError as e:
                        output = e.stderr.strip()
                        if "no such manifest" in output or "was deleted" in output:
                            print(f"  {output}")
                            print(f"  [green]No manifest returned for {full_image}[/green]")
                            remote_image_exists = False
                        else:
                            print(f"  Error inspecting manifest: {e.stderr}")
                            sys.exit(1)
                    remote_images_exist.setdefault(image, {})[image_version] = remote_image_exists

                # go build
                if build:
                    if remote_image_exists and not no_cache:
                        print(f"Pulling {full_image} from registry")
                        run(f"docker pull {full_image}")
                    # substitute Dockerfile and build
                    content = open(dockerpath, "rt").read().format(**version_vars)
                    if verbose:
                        print(f"Dockerfile:", style="bold")
                        print(f"{content}", style="dim", highlight=True)
                    run(f"docker build {no_cache} -t {full_image} -f- {build_dir}", cwd=build_dir, input=content)
                    # is this the latest version that needs to be tagged
                    if image_version == tag_latest.get(image):
                        run(f"docker tag {registry}/{image}:{image_version} {registry}/{image}:{BUNDLE_VERSION}")
                
                # run the image tests
                if not no_tests:
                    print(f"Running sanity check of {full_image}")
                    run(f"docker run {full_image}", input="")

                # go push
                if push:
                    if remote_image_exists:
                        # version mismatch
                        if unprefixed_image_version != conf.metadata.PACKAGE_VERSION:
                            if unprefixed_image_version == candidate_base:
                                print(f"  Image exists but package is a release candidate for image version: ok to push.")
                            else:
                                print(f"  [red]Image exists and package version doesn't match image version: won't push.[/red]")
                                continue
                        elif current_release:
                            if not candidate_release:
                                print(f"  [red]Image exists and package released: won't push.[/red]")
                                continue
                            else:
                                print(f"  Image exists, but package is a release candidate: ok to push.")
                        else:
                            print(f"  Image exists, but package unreleased, ok to push.")
                    run(f"docker push {full_image}", cwd=path)
                    if image_version == tag_latest.get(image):
                        run(f"docker push {registry}/{image}:{BUNDLE_VERSION}")
            progress.update(progress_task, description=
                f"image [bold]{image}[/bold] [{i_image}/{len(imagenames)}]: tagging latest version")

            # # apply :latest tag to images
            # if all_versions and built_or_pushed_versions:
            #     if latest is None:
            #         latest = image_version  # use last version from loop above
            #         run(f"docker tag {registry}/{image}:{latest} {registry}/{image}:{BUNDLE_VERSION}", cwd=build_dir)
            #         if push:
            #             run(f"docker push {registry}/{image}:{BUNDLE_VERSION}", cwd=path)
            #     run(f"docker tag {registry}/{image}:{BUNDLE_VERSION} {registry}/{image}:latest", cwd=build_dir)
            #     if push:
            #         run(f"docker push {registry}/{image}:latest", cwd=path)

    if do_list:
        print(Rule(f"Image list follows"))
        any_not_found = False
        for image in imagenames:
            found = [version for version, exists in remote_images_exist[image].items() if exists]
            not_found = [version for version, exists in remote_images_exist[image].items() if not exists]
            messages = [f"[green]{' '.join(found)}[/green] found"] if found else []
            if not_found:
                messages.append(f"[red]{' '.join(not_found)}[/red] not found")
                any_not_found = True
            if not messages:
                print(f"[bold]{image}[/bold]: no versions defined")
            else:
                print(f"[bold]{image}[/bold]: {', '.join(messages)}")
        if any_not_found:
            print("One or more image versions not found", style="red")
            sys.exit(1)


    print("Success!", style="green")

def driver():
    return build_cargo()
