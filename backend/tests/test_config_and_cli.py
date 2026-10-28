"""Address settings, the port scan, and the command line."""

import socket

import pytest

from turtlemaxxxing import config, ports
from turtlemaxxxing.__main__ import main


@pytest.mark.parametrize("name", ["localhost", "turtle.localhost", "i-like-turtles.localhost", "my.turtle.localhost"])
def test_valid_hostnames(name):
    assert config.valid_hostname(name)


@pytest.mark.parametrize("name", [
    "turtles", "I like turtles", "evil.com", "localhost.evil.com",
    "turtle.localhost.", "-turtle.localhost", "turtle_.localhost", "",
])
def test_rejected_hostnames_can_never_claim_a_real_internet_name(name):
    assert not config.valid_hostname(name)


def test_defaults():
    s = config.load_settings()
    assert (s.port, s.hostname) == (8765, "turtle.localhost")
    assert s.url == "http://turtle.localhost:8765"
    assert s.allowed_hosts == {"turtle.localhost", "localhost", "127.0.0.1"}


def test_settings_round_trip_and_env_override(monkeypatch):
    config.save_settings(config.Settings(port=8790, hostname="shell.localhost"))
    assert config.load_settings() == config.Settings(port=8790, hostname="shell.localhost")
    monkeypatch.setenv("TURTLE_PORT", "8791")
    assert config.load_settings().port == 8791


def test_bad_settings_fail_loudly():
    config.settings_path().write_text('{"hostname": "evil.com"}', encoding="utf-8")
    with pytest.raises(ValueError):
        config.load_settings()
    config.settings_path().write_text('{"port": 80}', encoding="utf-8")
    with pytest.raises(ValueError):
        config.load_settings()


def test_port_scan_skips_a_port_in_use():
    with socket.socket() as busy:
        busy.bind((config.HOST, 0))
        busy.listen()
        taken = busy.getsockname()[1]
        assert not ports.is_free(taken)
        assert ports.find_free([taken]) is None


def test_port_scan_skips_common_dev_ports():
    assert ports.find_free([5173]) is None


def test_cli_find_port_saves_settings(capsys):
    with pytest.raises(SystemExit) as done:
        main(["--find-port", "--hostname", "i-like-turtles.localhost"])
    assert done.value.code == 0
    saved = config.load_settings()
    assert saved.hostname == "i-like-turtles.localhost"
    assert ports.is_free(saved.port)
    assert "http://i-like-turtles.localhost:" in capsys.readouterr().out


def test_cli_rejects_bad_hostname():
    with pytest.raises(SystemExit) as done:
        main(["--hostname", "turtles.com"])
    assert done.value.code == 2
