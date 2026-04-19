@echo off
echo 🚀 Making AdGenie Public with Ngrok...
echo.

REM Check if ngrok auth token is provided
if "%1"=="" (
    echo 💡 For better experience, get a free ngrok token from: https://dashboard.ngrok.com/get-started/your-authtoken
    echo Then run: make_public.bat YOUR_TOKEN_HERE
    echo.
    echo Continuing without auth token...
)

REM Set auth token if provided
if not "%1"=="" (
    echo 🔑 Setting ngrok auth token...
    ngrok config add-authtoken %1
)

echo 🔄 Starting ngrok tunnel...
start /B ngrok http 8501

timeout /t 3 /nobreak > nul

echo 🚀 Starting AdGenie...
streamlit run app.py --server.headless true --server.port 8501

echo 🛑 Shutting down...
ngrok disconnect http://localhost:8501
pause