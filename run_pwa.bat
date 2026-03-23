@echo off
echo ========================================
echo   学生成绩分析系统 - PWA 版本启动
echo ========================================
echo.

REM 在后台启动 PWA 静态文件服务器
echo [1/2] 启动 PWA 静态文件服务器...
start /B python pwa_server.py
timeout /t 2 /nobreak > nul

REM 启动 Streamlit 应用
echo [2/2] 启动 Streamlit 应用...
echo.
echo ========================================
echo   访问地址:
echo   - 主应用：http://localhost:8501
echo   - PWA 文件：http://localhost:8502
echo   - 手机访问：使用局域网 IP 访问
echo ========================================
echo.

streamlit run app.py --server.headless=true --server.address=0.0.0.0 --server.port=8501
