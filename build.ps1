.\venv\Scripts\activate
pyinstaller script.py -F `
--name "pypanel-os-windows" `
--add-data "data\*;data" `
--clean