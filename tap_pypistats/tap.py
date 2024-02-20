"""Singer tap for PyPI Stats."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import logging
import pathlib
import sys
import typing as t

import requests
import requests_cache

BASE_URL = "https://pypistats.org/api"

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

logger = logging.getLogger(__name__)
logger.addHandler(handler)


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
        "package": {"type": "string"},
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


def iter_python_minor(
    base_url: str, package_name: str
) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a package."""
    url = f"{base_url}/packages/{package_name}/python_minor"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    yield from data["data"]


def iter_system(base_url: str, package_name: str) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a package."""
    url = f"{base_url}/packages/{package_name}/system"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    yield from data["data"]


def iter_packages(
    base_url: str,
    packages: t.Iterable[str],
) -> t.Generator[dict[str, t.Any], None, None]:
    """Iterate over the data for a list of packages.

    :param Iterable[str] packages: The names of the packages.
    :rtype: Iterator[dict]
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    yield {
        "type": "SCHEMA",
        "stream": "python_minor",
        "schema": SCHEMA,
        "key_properties": ["category", "date", "package"],
    }
    for package in packages:
        for record in iter_python_minor(base_url, package):
            yield {
                "type": "RECORD",
                "stream": "python_minor",
                "record": {
                    "package": package,
                    **record,
                },
                "time_extracted": now,
            }

    yield {
        "type": "SCHEMA",
        "stream": "system",
        "schema": SCHEMA,
        "key_properties": ["category", "date", "package"],
    }
    for package in packages:
        for record in iter_system(base_url, package):
            yield {
                "type": "RECORD",
                "stream": "system",
                "record": {
                    "package": package,
                    **record,
                },
                "time_extracted": now,
            }


def sync_packages(
    base_url: str,
    packages: t.Iterable[str],
    *,
    cache_name: str = "pypistats",
    stream: t.IO[str] = sys.stdout,
) -> t.Generator[dict[str, t.Any], None, None]:
    """Sync data for a list of packages.

    :param Iterable[str] packages: The names of the packages.
    :param str cache_name: The name of the cache.
    :rtype: Iterator[dict]
    """
    requests_cache.install_cache(cache_name)
    for message in iter_packages(base_url, packages):
        write_message(message, stream=stream)


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

    try:
        config = args.to_config()
    except json.JSONDecodeError as error:
        logger.error("Configuration file is not valid JSON: %s", error)
        sys.exit(1)
    except FileNotFoundError as error:
        logger.error("Configuration file not found: %s", error)
        sys.exit(1)
    except Exception as error:  # noqa: BLE001
        logger.error("Error reading configuration: %s", error)
        sys.exit(1)

    sync_packages(
        BASE_URL,
        config.packages,
        stream=sys.stdout,
    )


if __name__ == "__main__":
    main()
