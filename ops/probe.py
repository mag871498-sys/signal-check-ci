import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def check(port, version):
    expected = {"/health": {"state": "ready"}, "/version": {"version": version}}
    passed = True
    for path, payload in expected.items():
        url = f"http://127.0.0.1:{port}{path}"
        try:
            with urlopen(url, timeout=4) as response:
                code, body = response.status, response.read().decode()
        except HTTPError as error:
            with error:
                code, body = error.code, error.read().decode()
        except (URLError, OSError) as error:
            print(f"{path} failed: {error}")
            passed = False
            continue

        print(f"{path} -> HTTP {code} {body}")
        try:
            if code != 200 or json.loads(body) != payload:
                passed = False
        except json.JSONDecodeError:
            passed = False

    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("version")
    args = parser.parse_args()
    raise SystemExit(0 if check(args.port, args.version) else 1)