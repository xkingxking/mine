@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model qwen-max --questions app/data/5_questions.json --output app/out 