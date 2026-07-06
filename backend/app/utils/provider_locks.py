from threading import Lock


# AKShare's Tonghuashun helpers use py_mini_racer internally, which can crash
# the Python process when initialized concurrently. Keep THS provider calls
# serialized until we replace those adapters with safer direct requests.
THS_PROVIDER_LOCK = Lock()
