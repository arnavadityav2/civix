import winreg
import sys

key_path = r"SYSTEM\CurrentControlSet\Services\postgresql-x64-17"
target_image_path = '"C:\\Program Files\\PostgreSQL\\17\\bin\\pg_ctl.exe" runservice -N "postgresql-x64-17" -D "D:\\PostgreSQL\\17\\data" -w'

print("Target ImagePath:", target_image_path)

try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
    winreg.SetValueEx(key, "ImagePath", 0, winreg.REG_EXPAND_SZ, target_image_path)
    winreg.CloseKey(key)
    print("SUCCESS: Registry ImagePath updated!")
except Exception as e:
    print("Direct Registry Error:", e)
    sys.exit(1)
