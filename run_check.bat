@echo off
.venv\Scripts\python.exe -u -c "import ultralytics; f=open('C:/Users/jerem/Documents/Jugend Forscht/MIRA-AI/res.txt','w'); f.write(ultralytics.__version__); f.close()" 2> C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\err.txt
echo DONE: %ERRORLEVEL%