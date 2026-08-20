from modules.parser import get_config_path


def test_get_config_path():
    assert get_config_path().is_file()


def test_config_file():
    assert get_config_path().name == "dashify.toml"
