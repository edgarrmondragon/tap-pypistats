from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import pathlib
import sys
import typing as t

import requests
import requests_cache

BASE_URL = "https://pypistats.org/api"


@dataclasses.dataclass
class Config:
    """Configuration for the package."""

    packages: list[str]


class TapNamespace(argparse.Namespace):
    """A namespace for the tap command."""

    config: pathlib.Path

    def to_config(self: TapNamespace) -> Config:
        """Convert the namespace to a configuration."""
        with self.config.open(encoding="utf-8") as file:
            data = json.load(file)

            return Config(
                packages=data["packages"],
            )


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "downloads": {"type": "integer"},
    },
    "required": ["category", "date", "downloads"],
    "additionalProperties": False,
}


def write_message(message: dict[str, t.Any], *, stream: t.IO[str] = sys.stdout) -> None:
    """Write a message to a stream.

    :param dict message: The message to write.
    :param IO[str] stream: The stream to write to.
    """
    stream.write(json.dumps(message, default=str, separators=(",", ":")) + "\n")
    stream.flush()


def iter_python_minor(package_name: str) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a package."""
    url = f"{BASE_URL}/packages/{package_name}/python_minor"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    yield from data["data"]


def iter_system(package_name: str) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a package."""
    url = f"{BASE_URL}/packages/{package_name}/system"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    yield from data["data"]


def iter_packages(
    packages: t.Iterable[str],
) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a list of packages.

    :param Iterable[str] packages: The names of the packages.
    :rtype: Iterator[dict]
    """
    yield {
        "type": "SCHEMA",
        "stream": "python_minor",
        "schema": SCHEMA,
        "key_properties": ["category", "date"],
    }
    for package in packages:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for record in iter_python_minor(package):
            yield {
                "type": "RECORD",
                "stream": "python_minor",
                "record": record,
                "time_extracted": now,
            }

    yield {
        "type": "SCHEMA",
        "stream": "system",
        "schema": SCHEMA,
        "key_properties": ["category", "date"],
    }
    for package in packages:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for record in iter_system(package):
            yield {
                "type": "RECORD",
                "stream": "system",
                "record": record,
                "time_extracted": now,
            }


def sync_packages(
    packages: t.Iterable[str],
    *,
    cache_name: str = "pypistats",
) -> t.Generator[dict[str, t.Any], None, None]:
    """Sync data for a list of packages.

    :param Iterable[str] packages: The names of the packages.
    :param str cache_name: The name of the cache.
    :rtype: Iterator[dict]
    """
    requests_cache.install_cache(cache_name)
    for message in iter_packages(packages):
        write_message(message)


def main() -> None:
    """Run the main program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="The path to the configuration file.",
        required=True,
        type=pathlib.Path,
    )
    args = parser.parse_args(namespace=TapNamespace())
    config = args.to_config()

    sync_packages(config.packages)


if __name__ == "__main__":
    main()
