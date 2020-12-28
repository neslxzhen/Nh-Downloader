import asyncio
import sys
from models.book import Book
from models.result import Result
from util.project_util import dir_list_file_generator, zip_list_file_generator

if len(sys.argv)>1:
    Result('https://nhentai.net/language/chinese/',start=int(sys.argv[1]),end=int(sys.argv[2]))

else:
    d={
        'a':"下載搜尋結果",
        'b':"下載本子",
        'c':"生產目錄清單",
        'd':"生產ZIP清單",
        'input':''
    }
    inp = input("\n".join([key+"> "+d[key] for key in d]))

    if inp == 'a':
        inp = input("輸入搜尋結果的連結: ")
        if inp == "#":
            Result('https://nhentai.net/language/chinese/',start=1)
        else:
            Result(inp.strip())

    elif inp == 'b':
        inp = input("輸入本子的連結: ")
        if inp == "#":
            Book('https://nhentai.net/g/299246/',log_option={'result_page':'test'}).download()
        else:
            Book(inp.strip())

    elif inp == 'c':
        dir_list_file_generator()

    elif inp == 'd':
        zip_list_file_generator()

