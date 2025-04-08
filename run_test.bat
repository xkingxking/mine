@echo off
cd app\modules\question_generator
set PYTHONPATH=%PYTHONPATH%;%CD%\..\..\..
python generator_test.py --dimensions "医学,法学" --difficulties "easy,medium,hard" --distribution "balanced" --count 10 --output "test_questions.json"
pause 