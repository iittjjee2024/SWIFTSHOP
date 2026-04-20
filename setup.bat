@echo off
echo 🚀 Setting up SwiftShop Backend...

python -m venv venv
call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

if not exist .env (
  copy .env.example .env
  echo ⚠️  .env file created from .env.example — please fill in your secrets!
)

echo.
echo ✅ Setup complete! Run the server with:
echo    venv\Scripts\activate
echo    python run.py
echo.
echo 📚 API Docs: http://127.0.0.1:8000/docs
pause
