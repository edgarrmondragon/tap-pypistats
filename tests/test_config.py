from tap_pypistats.tap import Config, TapNamespace


def test_tap_namespace_to_config(tmp_path):
    """It should convert a namespace to a config."""
    config = tmp_path / "config.json"
    config.write_text('{"packages": ["foo", "bar"]}')

    namespace = TapNamespace(config=config)

    assert namespace.to_config() == Config(packages=["foo", "bar"])
