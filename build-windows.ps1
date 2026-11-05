# أنشئ ملف EXE مستقل بعد تثبيت متطلبات المشروع وPyInstaller.
python -m PyInstaller --noconfirm --clean --windowed --name YTDISK `
  --hidden-import reedsolo `
  --hidden-import cryptography `
  --collect-submodules cryptography `
  ytdisk_gui.py
