import os
import sys

print("Python:", sys.version)
print("CWD:", os.getcwd())
print("Files in CWD:", os.listdir("."))
print("Models dir exists:", os.path.exists("models"))
if os.path.exists("models"):
    print("Models files:", os.listdir("models"))

try:
    from app.score import score_trend
    print("Import OK")
except Exception as e:
    print("Import FAILED:", e)