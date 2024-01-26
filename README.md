# tap-pypistats

Singer tap for extracting data from the pypistats API.

See https://pypistats.org/api/.

## Usage

```
tap-pypistats -c config.json
```

* `-c, --config` - Config file. See below for details.

## Settings

| Name | Type | Description | Default |
| ---- | ---- | ----------- | ------- |
| packages | array | List of packages to get stats for | `[]` |

### Example

```json
{
  "packages": ["requests"]
}
```
