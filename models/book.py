from queue import Queue
from util.scheduler import Scheduler
from util.project_util import *
from util.session import Session
from util.util import *
from util.logger import logger


class Book:
    def __init__(self, info_page_url,log_option=dict, download=True):
        self.info_page_url = info_page_url
        res = Session().request("GET", self.info_page_url)
        if res is None: return
        self.soup = BeautifulSoup(res.content, 'html.parser')
        self.title = None
        self.log_option = log_option
        self.sub_file_name = None

        self.gid = None
        self.token = None
        self.archiver_key = None
        self.jpn_title=None
        self.en_title=None
        self.category=None
        self.tumb_url = None
        self.uploader = None
        self.posted = None
        self.max_page = 0
        self.filesize = None
        self.expunged = None
        self.rating = None
        self.torrentcount = None
        self.torrents = None
        self.tags = None

        self.init_from_net()
        if download and not self.downloaded_book(): self.download_book()

    def init_from_net(self):
        # gid, tumb_url
        self.tumb_url = self.soup.select_one("div#cover img")['data-src']
        self.gid = remove_suffix(remove_prefix(self.tumb_url,".*/galleries/"),"/cover.jpg")
        self.token = None
        self.archiver_key = None

        # title
        self.title = self.soup.select_one("div#info h1").text
        self.en_title=self.title
        if USE_JPN_TITLE:
            try:
                self.title = self.soup.select_one("div#info h2").text
                self.jpn_title=self.title
            except AttributeError: pass
        self.title = check_dir_name(self.title)

        # sub_file_name, max_page
        self.sub_file_name = get_sub_pic_name(self.tumb_url)
        self.max_page = int(self.soup.select_one("div#info section#tags a[class='tag'] span.name").text)

        self.category=None
        self.uploader = None
        self.posted = None
        self.filesize = None
        self.expunged = None
        self.rating = None
        self.torrentcount = None
        self.torrents = None
        self.tags = None

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

    def download_book(self):
        logger.info("[{}](pages:{}){}".format(self.log_option['result_page'], self.max_page, self.title))
        path = DOWNLOAD_DIR_PATH + '/' + self.title

        def writeJson():
            json.dump({
                'gid':self.gid,
                "token": self.token,
                "archiver_key":self.archiver_key,
                "title": self.en_title,
                "title_jpn": self.jpn_title,
                "category": self.category,
                "thumb": self.tumb_url,
                "uploader": self.uploader,
                "posted": self.posted,
                "filecount": self.max_page,
                "filesize": self.filesize,
                "expunged": self.expunged,
                "rating": self.rating,
                "torrentcount": self.torrentcount,
                "torrents": self.torrents,
                "tags":self.tags
            },open(path+"/_meta.json",'w',encoding='utf-8'), ensure_ascii=False)

        def downloaded_img(img_title):
            if os.path.isfile(path + img_title):
                return True
            return False

        mkdir(path, DOWNLOAD_DIR_PATH + '/' + "[" + self.gid + "]")
        writeJson()

        que = Queue()
        def job(start, end):
            for page in range(start, end):
                url='{}/galleries/{}/{}.{}'.format(GALLERY_PATH,self.gid,str(page),self.sub_file_name)
                title = get_pic_name(url)
                if downloaded_img(title): continue
                res = Session().request("GET", url, title=self.title)
                if res is None:
                    pass
                else:
                    open(path + "/" + title, 'wb').write(res.content)
                    logger.info("got:{},({})".format(url, self.max_page))

        Scheduler(1,self.max_page,THREAD_CNT,que,job,WAIT_OTHER_THREAD)

        if self.downloaded_book(isTemp=False):
            if CLOUD_MODE:
                open(DIR_LIST_TEMP_NAME, 'a', encoding='utf-8').write(
                    getLine(self.title) + "\n")
        else:
            book_logger(self.title, "圖片數量有缺")
