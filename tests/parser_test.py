from modules.parser import _default_config_path, get_config_dict, get_config_path


def test_get_config_path():
    assert get_config_path().is_file()


def test_config_file():
    assert get_config_path().name == "dashify.toml"


def test_unreadable_config_is_ignored(tmp_path):
    invalid_toml = tmp_path / "invalid.toml"
    invalid_toml.write_text('[widgets\nkind = "HBox"')

    assert get_config_dict(invalid_toml) == {}


def test_packaged_default_is_found_beside_installed_modules(tmp_path):
    module_path = tmp_path / "site-packages" / "modules" / "parser.py"
    default_path = tmp_path / "site-packages" / "defaults" / "dashify.toml"
    default_path.parent.mkdir(parents=True)
    default_path.write_text('[widgets]\nkind = "Clock"\n')

    assert _default_config_path(module_path) == default_path
