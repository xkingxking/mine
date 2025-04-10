@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model deepseek-v3 --questions app/data/5_questions.json --output app/out 