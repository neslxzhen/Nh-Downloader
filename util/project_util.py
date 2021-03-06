import os
import re
import sys
import traceback
from zipfile import ZipFile

from bs4 import BeautifulSoup
import json
from util.logger import logger
from const import *

# Project
def like(s1, s2):
    return s1 == s2


def get_last_page(html):
    href = BeautifulSoup(html, 'html.parser').select_one('section.pagination a.last')['href']
    return int(re.search(r'\d*$', href).group(0))


def get_pic_name(url):
    arr = url.split('/')
    return arr[len(arr) - 1]


def get_sub_pic_name(url):
    a = get_pic_name(url).split('.')
    return a[len(a) - 1]


def check_dir_name(name):
    name = re.sub(r'[:!\\*"<>?/|	]*', "", name).strip()
    # if len(name)>96:name=name[:96]
    if len(name) > 95: name = name[:95]
    name = name.strip()
    return name


def error_logger(e, title=None):
    error_class = e.__class__.__name__  # 取得錯誤類型
    detail = e.args[0]  # 取得詳細內容
    cl, exc, tb = sys.exc_info()  # 取得Call Stack
    lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
    fileName = lastCallStack[0]  # 取得發生的檔案名稱
    lineNum = lastCallStack[1]  # 取得發生的行號
    funcName = lastCallStack[2]  # 取得發生的函數名稱
    errMsg = "TITLE \"{}\":File \"{}\", line {}, in {}: [{}] {}".format(title, fileName, lineNum, funcName, error_class,
                                                                        detail)
    if title: book_logger(title, errMsg)
    logger.error(errMsg)


def book_logger(title, msg):
    open(LOG_FILE_NAME + ".book.log", 'a', encoding='utf-8').write(title + "," + msg + "\n")
    logger.warning(title + "," + msg)


def mkdir(*paths):
    for path in paths:
        try:
            os.makedirs(path)
            return path
        except FileExistsError:
            return path
        except OSError:
            pass

def zip_list_file_generator():
    print("生產目錄清單中...")
    f = open(ZIP_LIST_TEMP_NAME, 'w' if os.path.isfile(ZIP_LIST_TEMP_NAME) else 'a', encoding='utf-8')
    for zip in os.listdir(ZIP_DIR_PATH):
        f.write(getZipList(zip) + "\n")
    print("生產完畢")

def getZipList(zip:str) -> str:
    file_list = [file.filename for file in ZipFile(ZIP_DIR_PATH+"/"+check_dir_name(zip),'r').infolist()]
    return json.dumps({
        "title": zip,
        "file_list": file_list,
        "pics_list": [int(getNo(name)) for name in file_list if getNo(name) is not None]
    }, ensure_ascii=False)

def dir_list_file_generator():
    print("生產目錄清單中...")
    f = open(DIR_LIST_TEMP_NAME, 'w' if os.path.isfile(DIR_LIST_TEMP_NAME) else 'a', encoding='utf-8')
    for dir in os.listdir(DOWNLOAD_DIR_PATH):
        f.write(getDirList(dir) + "\n")
    print("生產完畢")

def getDirList(dir):
    file_list = [name for name in os.listdir(DOWNLOAD_DIR_PATH + "/" + check_dir_name(dir))]
    return json.dumps({
        "title": dir,
        "file_list": file_list,
        "pics_list": [int(getNo(name)) for name in file_list if getNo(name) is not None]
    }, ensure_ascii=False)

def getNo(name):
    ld = re.sub(r'\D+\.*(jpg|png)*', '', name)
    return None if ld == '' else int(ld)
