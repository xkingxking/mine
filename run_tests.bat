@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model deepseek --questions app/data/questions/test_questions.json --output app/out --proxy http://127.0.0.1:8453 