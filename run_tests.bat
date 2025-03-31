@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model deepseek --questions app/data/questions/test_questions.json --output app/out 