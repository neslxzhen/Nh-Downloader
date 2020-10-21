import asyncio
import functools
import math
import os
import threading
from queue import Queue
from util.scheduler import Scheduler
from util.project_util import *
from util.session import Session
from util.util import *
from util.logger import logger


class Book:
    def __init__(self, info_page_url,log_option=dict):
        self.info_page_url = info_page_url
        res = Session().request("GET", self.info_page_url)
        if res is None: return
        self.soup = BeautifulSoup(res.content, 'html.parser')

        self.title = None
        self.log_option = log_option
        self.sub_file_name = None
        self.gid = None
        self.token = None
        self.tumb_url = None
        self.max_page = 0

        self.init_from_net()

    def download(self):
        if not self.downloaded_book():
            asyncio.run(self.download_book())

    def init_from_net(self):
        # gid, tumb_url
        self.tumb_url = self.soup.select_one("div#cover img")['data-src']
        self.gid = remove_suffix(remove_prefix(self.tumb_url,".*/galleries/"),"/cover.jpg")
        self.token = None
        self.archiver_key = None

        # title
        self.title = self.soup.select_one("div#info h1").text
        if USE_JPN_TITLE:
            try:
                self.title = self.soup.select_one("div#info h2").text
            except AttributeError: pass
        self.title = check_dir_name(self.title)

        # sub_file_name
        self.sub_file_name = get_sub_pic_name(self.tumb_url)

        # max_page
        self.max_page = int(self.soup.select_one("div#info section#tags a[class='tag'] span.name").text)

    def downloaded_book(self,isTemp=CLOUD_MODE):
        def checkFromDir(title):
            path=os.path.join(DOWNLOAD_DIR_PATH,check_dir_name(title))
            if os.path.isdir(path):
                if len(set(name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name)) and getNo(name) is not None)) >= self.max_page:
                    logger.info("頁數完整({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
                    return True
            return False

        def checkFromTemp(title):
            for l in open(DIR_LIST_TEMP_NAME, 'r', encoding='utf-8'):
                l = json.loads(l)
                if l["title"] == title and len(set(int(i) for i in l["pics_list"])) >= self.max_page:
                    logger.info("在清單之中， 頁數正確({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
                    return True
            return False

        is_downloaded=False
        for dirTitle in [self.title, "[" + self.gid + "]"]:
            dirTitle = check_dir_name(dirTitle)
            if not is_downloaded:
                is_downloaded=checkFromTemp(dirTitle)if isTemp else checkFromDir(dirTitle)
        return is_downloaded

    async def download_book(self):
        logger.info("[{}](pages:{}){}".format(self.log_option['result_page'], self.max_page, self.title))
        path = DOWNLOAD_DIR_PATH + '/' + self.title

        def downloaded_img(img_title):
            if os.path.isfile(path + img_title):
                return True
            return False

        mkdir(path, DOWNLOAD_DIR_PATH + '/' + "[" + self.gid + "]")

        async def fetch(page):
            url='{}/galleries/{}/{}.{}'.format(GALLERY_PATH,self.gid,str(page),self.sub_file_name)
            title = get_pic_name(url)
            if downloaded_img(title): return

            # res = await Session().request("GET",url,title=self.title)
            res=await asyncio.get_event_loop().run_in_executor(None,functools.partial(
                Session().request,
                method="GET",
                url=url,
                title=self.title
            ))
            if res is None:
                pass
            else:
                open(path + "/" + title, 'wb').write(res.content)
                logger.info("got:{},({})".format(url, self.max_page))

        await asyncio.gather(
            *[fetch(page) for page in range(1, self.max_page+1)]
        )

        if self.downloaded_book(isTemp=False):
            if CLOUD_MODE:
                open(DIR_LIST_TEMP_NAME, 'a', encoding='utf-8').write(
                    getLine(self.title) + "\n")
        else:
            book_logger(self.title, "圖片數量有缺")
