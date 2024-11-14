import shutil
import PyInstaller.__main__
import os

dist_path = f"build"
title = "SchPy"
start_file = "window.py"
icon_name = "icon.ico"
no_console = True
run_exe = True
current_directory = os.path.dirname(os.path.abspath(__file__))

dirs = [

]

files = [
    "icon.ico",
    "schedule_maker.py",
    "best_of.py"
    "db.py",
    "MainWindow.css",
    "InputDataDialog.css",
    "ErrorDialog.css",
    "ScheduleGeneratorDialog.css",
]

command = [
    start_file,
    '--noconfirm',
    '--onefile',
    f'--icon={icon_name}',
    f'--name={title}',
    '--clean',
    f'--distpath={dist_path}',
]

if no_console:
    command.append('--noconsole')

for d in dirs:
    command.append(f'--add-data={d};{d}/')

for filename in files:
    filename = os.path.join(current_directory, filename)
    command.append(f'--add-data={filename};.')


def build():
    shutil.rmtree(dist_path, ignore_errors=True)
    os.makedirs(dist_path, exist_ok=True)

    PyInstaller.__main__.run(command)

    shutil.rmtree(f"{dist_path}/{title}")
    os.unlink(f"{title}.spec")


if __name__ == '__main__':
    build()

    if run_exe:
        os.startfile(f"{dist_path}\\{title}.exe")
