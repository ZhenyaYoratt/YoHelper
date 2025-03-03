import os
print('Installing requirements...')
os.system('pip install -r requirements.txt --upgrade')
print('Upgrading python tools...')
os.system('python -m ensurepip --upgrade')
os.system('python -m pip install --upgrade setuptools')
print('Starting building...')
os.system('pyinstaller .\\modules\\tts.py --onefile --windowed')
os.system('pyinstaller main.py --onefile -n YoHelper --windowed --uac-admin --optimize 2 --upx-dir "C:\\upx-4.2.4-win64" --icon=icon.ico --splash=splash.png --hidden-import psutil --hidden-import PyQt5.sip --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets')
#os.system('pyinstaller installer.py --onefile --add-data dist:YoHelper.exe --windowed')

print("""
    Done!
""")