import asyncio
import functools
import shutil
from zipfile import ZipFile, BadZipFile

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

        self.download_path=None

        self.init_from_net()

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
        self.download_path=os.path.join(DOWNLOAD_DIR_PATH,check_dir_name(self.title))

        # sub_file_name
        self.sub_file_name = get_sub_pic_name(self.tumb_url)

        # max_page
        self.max_page = int(self.soup.select_one("div#info section#tags a[class='tag'] span.name").text)

    def download(self):
        if ZIP:
            if not (self.checkZipTemp() if ZIP_DIR_IN_CLOUD else self.checkZip()):
                def make(s):
                    return re.sub(r'([^\w\s]|\s)','',s)[:-3].lower()
                if not make(check_dir_name(self.title)) in [make(x) for x in os.listdir(ZIP_DIR_PATH)]:
                    self.download_book()
                    shutil.make_archive(os.path.join(ZIP_DIR_PATH,check_dir_name(self.title)), 'zip',os.path.join(self.download_path))
            if ZIP_DIR_IN_CLOUD:
                open(ZIP_LIST_TEMP_NAME, 'a', encoding='utf-8').write(
                    getZipList(check_dir_name(self.title)) + "\n")
            logger.info("ZIP內容完整({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
        else:
            self.download_book()

    def checkZip(self) ->bool:
        path=os.path.join(ZIP_DIR_PATH,check_dir_name(self.title)+".zip")
        if os.path.isfile(path):
            try:
                if len(set(file.filename for file in ZipFile(path,'r').infolist())) >= self.max_page:
                    return True
            except BadZipFile as e:
                logger.info(f"{e}, {path}")
            return False

    def checkZipTemp(self) ->bool:
        if not os.path.isfile(ZIP_LIST_TEMP_NAME):
            raise BaseException('nesl error: zip_temp.txt not exist.')
        for l in open(ZIP_LIST_TEMP_NAME, 'r', encoding='utf-8'):
            l = json.loads(l)
            if l["title"] == check_dir_name(self.title) and len(set(int(i) for i in l["pics_list"])) >= self.max_page:
                logger.info("在清單之中， 頁數正確({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
                return True
        return False

    def checkDir(self)->bool:
        if os.path.isdir(self.download_path):
            if len(set(name for name in os.listdir(self.download_path) if os.path.isfile(os.path.join(self.download_path, name)) and getNo(name) is not None)) >= self.max_page:
                logger.info("頁數完整({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
                return True
        return False

    def checkDirTemp(self)->bool:
        if not os.path.isfile(DIR_LIST_TEMP_NAME):
            raise BaseException('nesl error: DIR_LIST_TEMP.TXT not exist.')
        for l in open(DIR_LIST_TEMP_NAME, 'r', encoding='utf-8'):
            l = json.loads(l)
            if l["title"] == check_dir_name(self.title) and len(set(int(i) for i in l["pics_list"])) >= self.max_page:
                logger.info("在清單之中， 頁數正確({}):[{}]{}".format(self.max_page, self.log_option['result_page'], self.title))
                return True
        return False

    def downloaded_book(self, checkTemp=DOWNLOAD_DIR_IN_CLOUD):
        return self.checkDirTemp() if checkTemp else self.checkDir()

    def download_book(self):
        async def job():
            logger.info("[{}](pages:{}){}".format(self.log_option['result_page'], self.max_page, self.title))
            mkdir(self.download_path)
            def downloaded_img(img_title):
                if os.path.isfile(os.path.join(self.download_path,img_title)):
                    return True
                return False

            async def fetch(page):
                url='{}/galleries/{}/{}.{}'.format(GALLERY_PATH,self.gid,str(page),self.sub_file_name)
                title = get_pic_name(url)
                if downloaded_img(title): return

                res=await asyncio.get_event_loop().run_in_executor(None,functools.partial(
                    Session().request,
                    method="GET",
                    url=url,
                    title=self.title
                ))
                if res is None:
                    pass
                else:
                    open(os.path.join(self.download_path,title) , 'wb').write(res.content)
                    logger.info("got:{},({})".format(url, self.max_page))

            await asyncio.gather(
                *[fetch(page) for page in range(1, self.max_page+1)]
            )

            if not self.downloaded_book(checkTemp=False):
                book_logger(self.title, "圖片數量有缺")
            elif DOWNLOAD_DIR_IN_CLOUD:
                open(DIR_LIST_TEMP_NAME, 'a', encoding='utf-8').write(
                    getDirList(check_dir_name(self.title)) + "\n")
                
        if not self.downloaded_book():
            asyncio.run(job())
