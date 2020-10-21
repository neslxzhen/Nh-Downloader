from models.book import Book
from util.session import Session
from util.project_util import *
from util.logger import logger

class Result:
    def __init__(self,url,start=1,end=None):
        self.url=url
        self.start=start
        self.end=end
        self.start_scrapy()

    def start_scrapy(self):
        session = Session()
        res = session.request("GET", self.url)
        if res is None:return
        html = res.content
        if self.end==None: self.end=get_last_page(html)
        for page in range(self.start, self.end):
            new_url =self.url+ '?page=' + str(page)
            res=session.request("GET", new_url)
            if res is None:return
            html = res.content
            logger.debug('page: ' + str(page) + " res.status:" + str(res))
            for book in BeautifulSoup(html, 'html.parser').select('div.gallery'):
                d=self.get_book_info(book)
                Book(d['info_page_url'],log_option={'result_page':page}).download()

    def get_book_info(self,soup):
        d={}
        a=soup.select_one('a.cover')
        d["info_page_url"]=HOST+a['href'][1:]
        d['title']=a.select_one('div.caption').text
        src=None
        try:
            src=a.select_one('img')['data-src']
        except KeyError:
            src='https:'+a.select_one('img')['src']
        d["token"]=src
        d["tumb_url"]=src
        d["id"] =  d['info_page_url'].replace(HOST+'g/',"").replace('/',"")
        d["token"] = re.sub(r"(https://t.nhentai.net/galleries/)*(/thumb.)*(jpg|png)*/*", "", d['tumb_url'])
        return d
