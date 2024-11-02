import shutil
import PyInstaller.__main__

title = "SchPy"
start_file = "window.py"

dirs = [

]

files = [
    'icon.png',
    'schedule_maker.py',
    'db.py',
    'MainWindow.css',
    'InputDataDialog.css',
    'ErrorDialog.css'
]

command = [
    start_file,
    '--noconfirm',
    '--onefile',
    '--windowed',
    '--icon=icon.png',
    f'--name={title}',
    '--clean',
    '--distpath=build'
]

for d in dirs:
    command.append(f'--add-data={d};{d}/')

for filename in files:
    command.append(f'--add-data={filename};.')

PyInstaller.__main__.run(command)

shutil.rmtree(f"build/{title}")
