from tf_jev import __version__


def test_package_version_is_bootstrap_version() -> None:
    assert __version__ == "0.1.0.dev0"
