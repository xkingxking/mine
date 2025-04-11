@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model doubao-1.5-pro-32k --questions app/data/general_questions.json --output app/out 