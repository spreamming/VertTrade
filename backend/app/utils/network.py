import os
from contextlib import contextmanager

import requests


@contextmanager
def without_system_proxy():
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
        "NO_PROXY",
        "no_proxy",
    )
    saved = {name: os.environ.pop(name, None) for name in proxy_vars}
    original_merge_environment_settings = (
        requests.sessions.Session.merge_environment_settings
    )

    def merge_without_proxy(self, url, proxies, stream, verify, cert):
        settings = original_merge_environment_settings(
            self, url, proxies, stream, verify, cert
        )
        settings["proxies"] = {}
        return settings

    try:
        requests.sessions.Session.merge_environment_settings = merge_without_proxy
        os.environ["NO_PROXY"] = "*"
        yield
    finally:
        requests.sessions.Session.merge_environment_settings = (
            original_merge_environment_settings
        )
        os.environ.pop("NO_PROXY", None)
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value
