import os
from contextlib import contextmanager


@contextmanager
def without_system_proxy():
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
    )
    saved = {name: os.environ.pop(name, None) for name in proxy_vars}
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value
