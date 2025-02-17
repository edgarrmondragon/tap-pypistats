# tap-pypistats

Singer tap for extracting data from the pypistats API.

See https://pypistats.org/api/.

## Installation

### Using [`pipx`](https://pipx.pypa.io/)

```bash
pipx install tap-pypistats
```

### Using [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv tool install tap-pypistats
```

#### Pinned dependencies

Install `tap-pypistats[pinned]` to get a more stable dependency tree.

## Usage

```
tap-pypistats -c config.json
```

* `-c, --config` - Config file. See below for details.

## Settings

| Name | Type | Description | Default |
| ---- | ---- | ----------- | ------- |
| packages | array | List of packages to get stats for | `[]` |

### Config example

```json
{
  "packages": ["requests"]
}
```

## Acknowledgements

* [Christopher Flynn](https://flynn.gg/), for creating [pypistats.org](https://pypistats.org).
