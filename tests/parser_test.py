from modules.parser import get_config_dict, get_config_path


def test_get_config_path():
    assert get_config_path().is_file()


def test_config_file():
    assert get_config_path().name == "dashify.toml"


def test_unreadable_config_is_ignored(tmp_path):
    invalid_toml = tmp_path / "invalid.toml"
    invalid_toml.write_text('[widgets\nkind = "HBox"')

    assert get_config_dict(invalid_toml) == {}
