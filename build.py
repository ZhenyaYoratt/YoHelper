import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import PyInstaller.__main__

#print('Installing requirements...')
#os.system('pip install -r requirements.txt --upgrade')
#print('Upgrading python tools...')
#os.system('python -m ensurepip --upgrade')
#os.system('python -m pip install --upgrade setuptools')


print('Starting building...')


datas = [('./.venv/Lib/site-packages/psutil/_pswindows.py', 'psutil'), ('./.venv/Lib/site-packages/psutil/_psutil_windows.pyd', 'psutil')]
hiddenimports = collect_submodules('psutil')
hiddenimports += collect_submodules('PyQt5.QtCore')
hiddenimports += collect_submodules('PyQt5.QtGui')
hiddenimports += collect_submodules('PyQt5.QtWidgets')
print('hiddenimports:', hiddenimports)

#PyInstaller.__main__.run([
#    '.\\modules\\tts.py',
#    '--onefile',
#    '--windowed'
#])

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--name=YoHelper',
    '--uac-admin',
    '--optimize=2',
    '--upx-dir="C:\\upx-4.2.4-win64"',
    '--icon=icon.ico',
    '--splash=splash.png',
    '--hidden-import=' + ' '.join(hiddenimports)
])
#os.system('pyinstaller installer.py --onefile --add-data dist:YoHelper.exe --windowed')

print("""
    Done!
""")