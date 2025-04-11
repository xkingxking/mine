@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model deepseek-v3 --questions app/data/general_questions.json --output app/out 