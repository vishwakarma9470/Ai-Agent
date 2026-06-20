@echo off
echo Running Industry Data Reasoning Agent...
python cli.py --data data/sample_sales.csv --query "top products by revenue"
pause
