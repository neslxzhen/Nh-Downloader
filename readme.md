### 功能
 - N站備份機: 
 輸入N站的搜尋結果網址，會自動備份其所有畫廊至`自訂的資料夾位置`
 - 單個本子備份:
 輸入本子的連結，備份整本本子至`自訂的資料夾位置`
 - 雲端模式:
如果您的備份位置是雲端，則常因速度太慢而無法檢查「是否已經下載過本子」。此時您應該在`config.py`中將`CLOUD_MODE`設為`True`，並在初次啟動專案時選擇`c> 生產目錄清單`
 - 存檔模式:
可以將`DOWNLOAD_DIR_PATH`中的本子們存檔成zip，並且不壓縮畫質。請在`config.py`中設定`ZIP=True`及`ZIP_DIR_PATH`
 
### 前置作業
- 自訂的資料夾位置
    - 在`config.py`的`DOWNLOAD_DIR_PATH`欄位輸入資料夾位置
    - (可選)在`config.py`的`ZIP_DIR_PATH`欄位輸入資料夾位置

### TL;DR
 - install python 3.8
 - run directly from source code:

        pip install bs4
        pip install requests
        git clone https://github.com/neslxzhen/Nh-Downloader.git
        cd Nh-Downloader
        python main.py
