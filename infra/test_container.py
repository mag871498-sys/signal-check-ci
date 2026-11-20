def test_application_file(host):
    assert host.file("/srv/signal/service.py").is_file
    assert host.file("/etc/os-release").is_file


def test_service_runs_as_pid_one(host):
    cmdline = host.check_output("tr '\\000' ' ' < /proc/1/cmdline")
    assert cmdline.split() == ["python", "-u", "/srv/signal/service.py"]


def test_tcp_port_listens(host):
    probe = (
        "import os, socket; "
        "socket.create_connection(('127.0.0.1', int(os.environ['SERVICE_PORT'])), 2).close()"
    )
    assert host.run("python -c %s", probe).rc == 0


def test_service_runs_without_root(host):
    uid_line = host.check_output("grep '^Uid:' /proc/1/status")
    assert uid_line.split()[1:] == ["10051"] * 4