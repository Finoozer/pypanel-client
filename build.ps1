.\venv\Scripts\activate
pyinstaller script.py -F `
--name "PyPanel" `
--add-data "data\*;data" `
--version-file "VERSION" `
--add-data "data\*.txt;data" `
--clean