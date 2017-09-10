@Echo Off

REM activate Python venv

CALL "D:\dev\venv\scrapynuts\Scripts\activate.bat"

CD /D "D:\dev\git\scrapynuts"

CALL "D:\dev\venv\scrapynuts\Scripts\python.exe" "D:\dev\venv\scrapynuts\Lib\site-packages\scrapy\cmdline.py" crawl whoscored

CALL "D:\dev\venv\scrapynuts\Scripts\python.exe" "D:\dev\venv\scrapynuts\Lib\site-packages\scrapy\cmdline.py" crawl lfp

CALL "D:\dev\venv\scrapynuts\Scripts\python.exe" "D:\dev\venv\scrapynuts\Lib\site-packages\scrapy\cmdline.py" crawl sportsfr

CALL "D:\dev\venv\scrapynuts\Scripts\python.exe" "D:\dev\venv\scrapynuts\Lib\site-packages\scrapy\cmdline.py" crawl orangesports

deactivate