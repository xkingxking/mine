@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
pytest tests/test_api_keys.py -v 