@echo off
chcp 65001 >nul
echo ============================================
echo   考编雷达 kaobian-radar - 打包脚本
echo ============================================
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --name kaobian-radar ^
  --add-data "app\static;static" --paths app app\main.py
echo.
echo 打包完成: dist\kaobian-radar.exe
pause
