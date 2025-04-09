@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python app/main.py --model llama --questions app/data/test_math_questions.json --output app/out 