import requests
from bs4 import BeautifulSoup

# The one public method

class UrlReading:
    def __init__(self, url: str):
        """
        Info
        ----------------
        This object stores all basic needs for a reader, such as the next page, previous page, etc.
        
        Parameters
        ----------------
        url: A string containing a url for the application to scrape from

        Class attributes
        ----------------
        website: defined when domain matches with a url,
        a lambda with the value webpage which will get a matching configuration
        for getting data from that webpage \n
        
        current: The Url of the current content displayed on the page \n
        content: The chapter content of whatever page i'm looking at \n
        title: The title of the page \n
        prev, next: The urls that allow going to the previous and next chapters
        """
        domain = url.split("/")[2].replace("www.", "")
        
        if domain == "kisslightnovels.info" or domain ==  "readwebnovels.net" or domain == "boxnovel.net":
            prev_lambda  = lambda tag: tag.get('class') == ['btn', 'prev_page']
            next_lambda  = lambda tag: tag.get('class') == ['btn', 'next_page']
            self.website = lambda webpage: generalWebsite(webpage, 'text-left', prev_lambda, next_lambda, titlespot = 4)

        elif domain == "readnovelfull.com":
            prev_lambda  = lambda tag: tag.get('id') == "prev_chap"
            next_lambda  = lambda tag: tag.get('id') == "next_chap"
            self.website = lambda webpage: generalWebsite(webpage, "chr-c", prev_lambda, next_lambda)
         
        elif domain == "royalroad.com":
            prev_lambda  = lambda tag: "Previous Chapter" in tag.text and tag.name == 'a'
            next_lambda  = lambda tag: "Next Chapter" in tag.text and tag.name == 'a'
            self.website = lambda webpage: generalWebsite(webpage, "chapter-content", prev_lambda, next_lambda, titlespot = 5)
        
        elif domain == "scribblehub.com":
            prev_lambda  = lambda tag: "Previous" == tag.text
            next_lambda  = lambda tag: "Next" == tag.text
            self.website = lambda webpage: generalWebsite(webpage, 'chp_raw', prev_lambda, next_lambda, titlespot = 4)
        
        elif domain == "fanfiction.net"    : self.website = lambda webpage: ffnet(webpage)
        elif domain == "wattpad.com"       : self.website = lambda webpage: wattpad(webpage)
        elif domain == 'webnovel.com'      : self.website = lambda webpage: webnovel(webpage)
        elif domain == "readlightnovel.org": self.website = lambda webpage: rlnovels(webpage)
        
        self.website(url)
        self.current = url
    
    @ property
    def current(self):
        return self._current
    
    @ current.setter
    def current(self, value: str):
        """Setter method for current; Also will set the other values"""
        self.content, self.title, self.prev, self.next = self.website(value)
        self._current = value

# 
#             PRIVATE
#             METHODS
#
#

# Decorators / Support Functions
def completeUrls(function: callable) -> list:
    """Completes incomplete urls

    Args:
        function (callable): The function decorated by this decorator

    Returns:
        list: content, title, prev_url, next_url
    """
    def wrapper(url: str, *args, **kwargs):
        baseUrl = "/".join(url.split("/")[:3])
        content, title, prev_url, next_url = function(url, *args, **kwargs)
        
        if prev_url is not None:
            prev_url = baseUrl + prev_url if prev_url.startswith("/") else prev_url
        if next_url is not None:
            next_url = baseUrl + next_url if next_url.startswith("/") else next_url

        return content, title, prev_url, next_url
    return wrapper

from traceback import print_exc
def errorHandler(function: callable):
    def wrapper(url: str, *args, **kwargs):
        try:
            return function(url, *args, **kwargs)
        except IndexError as e:
            print("Invalid Url")
            print_exc()
        except LookupError as e:
            print("Most likely a nonexistent or forbidden url")
            print_exc()
    return wrapper    

# Use this session for getting data from URLs
# Its preset to bypass websites that ask for a valid user agent
SESSION = requests.Session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0"}
SESSION.headers = headers


@ errorHandler
@ completeUrls
def generalWebsite(URL: str, storyClass: str, prevLambda: bool, nextLambda: bool, titlespot = 3) -> list:
    """General Purpose webscraper for these types of websites

    Args:
        url (str): The url of the target website
        storyClass (str): The class that contains the text or the div with text inside of it
        prevLambda (callable): Lambda for filtering for a tag
        nextLambda (callable): Same as prevLambda, except target a tag should be the next page
        titlespot (int, optional): Spot in url (split with /) where the title of the novel is. Defaults to 3.

    Raises:
        LookupError: 404 Error; File not found
        LookupError: 403 Error; Forbidden url

    Returns:
        list: Contains [content, title, url for previous page, url for next page] in that order
    """
    try: title = URL.split("/")[titlespot].replace("-", " ").title() 
    except: title = "Error"
    # Get text
    DATA = SESSION.get(URL)
    # Error handling
    if   DATA.status_code == 404: raise LookupError("No Page", "No page accessable by that url; or website not allowing access")
    elif DATA.status_code == 403: raise LookupError("Forbidden", "Scraper not allowed access by ddos protection (probably)")
    
    SOUP = BeautifulSoup(DATA.text, 'html.parser')
    # Checks if there are multiple separate p tags, which seems to be pretty common
    # for these types of websites
    storyTag = SOUP.find(class_ = storyClass)
    if not storyTag.name == 'div': content = storyTag.text
    else:
        #text = storyTag.find_all(text = True)
        content = "\n".join([element.text for element in storyTag.find_all(whitespace = False)])
    #Buttons for next and previous chapters
    prevInfo = SOUP.find(prevLambda)
    if prevInfo != None: 
        prev_url = prevInfo['href'] if prevInfo.get('href') != None and prevInfo['href'] != '#' else None
    else: prev_url = None
    
    nextInfo = SOUP.find(nextLambda)
    if nextInfo != None: 
        next_url = nextInfo['href'] if nextInfo.get('href') != None and nextInfo['href'] != '#' else None
    else: next_url = None
    return content, title, prev_url, next_url


@ errorHandler
@ completeUrls
def ffnet(url: str) -> list:
    """Function to allow access to fanfiction.net content with a chapter url 

    Args:
        url (str): The url of the target chapter of the story

    Raises:
        LookupError: 404 error; File not found

    Returns:
        list: a list containing 'content' of the story, 'title' of the story, 'prev_url' Url for previous chapter, 'next_url' Url for next chapter
    """
    title = url.split("/")[6].replace("-", " ").title()
    # Get text
    data = SESSION.get(url)
    if data.status_code == 404: raise LookupError("No Page", "No page accessable by that url")
    
    soup = BeautifulSoup(data.text, 'html.parser')
    div = soup.findChildren('div', id = "storytext")
    finalString = "".join([f"\n\n{str(element)}" for element in div[0].contents])
    content = BeautifulSoup(finalString.encode(), 'lxml').text

    #Buttons for next and previous chapters
    prev_url = soup.find('button', text = "< Prev")
    next_url = soup.find('button', text = "Next >")

    prev_url = prev_url['onclick'][14:]  if prev_url != None else None
    next_url = next_url["onclick"][14:]  if next_url != None else None
    
    return content, title, prev_url, next_url

# Already has built in error handling with generalWebsite
def rlnovels(URL: str):
    """Function for trimming fat of readlightnovel body

    Args:
        URL (str): Url of readlightnovel.com

    Returns:
        list: content, title, prev_url, next_url
    """
    
    prev_lambda = lambda tag: tag.get('class') == ["prev", "prev-link"]
    next_lambda = lambda tag: tag.get('class') == ["next", "next-link"]
    
    content, title, prev_url, next_url = generalWebsite(URL, "desc", prev_lambda, next_lambda)
    
    SOUP = BeautifulSoup(content, 'html.parser')
    content = "\n".join([f"{element.text}" for element in SOUP.findAll("p", whitespace = False)])
    
    return content, title, prev_url, next_url


import re
import json

@ errorHandler
@ completeUrls
def wattpad(url: str) -> list:
    
    ID = re.findall('/(\d{5,})', url)[0]
    
    apiCallUrl = f"https://www.wattpad.com/apiv2/info?id={ID}"
    DATA = SESSION.get(apiCallUrl)
    
    if   DATA.status_code == 404: raise LookupError ("No Page", "No page accessable by that url; or website not allowing access")
    elif DATA.status_code == 403: raise LookupError ("Forbidden", "Scraper not allowed access by ddos protection (probably)"    )
    
    bookJson = DATA.json()

    chaps = bookJson["group"]

    currentChap, prevTitle, nextTitle = None, None, None
    currentId = None
    # When next and previous are being run, they are ran in increments of 3 instead of one
    for chapterId in range(len(chaps)):
        if chaps[chapterId]["TITLE"] == bookJson["title"]:
            # Get chapter ids from api
            currentChap = chaps[chapterId]
            if chapterId != 0:
                prevChap  = chaps[chapterId - 1]
                prevTitle = prevChap["TITLE"]
                prevId = prevChap["ID"]
            else: prevTitle = None
            
            if len(chaps) - 1 != chapterId:
                nextChap  = chaps[chapterId + 1]
                nextTitle = nextChap["TITLE"]
                nextId = nextChap["ID"]
            else: nextTitle = None
            
            currentId = currentChap["ID"]
            break


    base = re.findall("\d{5,}(.+)",bookJson["url"])[0] # <- Find the data after the id
    # Build a url using the actual title
    prev_url = f"https://www.wattpad.com/{prevId}{base}" if prevTitle != None else None
    next_url = f"https://www.wattpad.com/{nextId}{base}" if nextTitle != None else None

    content = SESSION.get(f"https://www.wattpad.com/apiv2/storytext?id={currentId}").text
    title = currentChap["TITLE"]
    
    SOUP = BeautifulSoup(content, "html.parser")
    content = "\n".join([f"{element.text}" for element in SOUP.findAll("p", whitespace = False)])
    
    return content, title, prev_url, next_url


@ errorHandler
def webnovel(url: str) -> list:
    """Gets data from webnovel.com chapters using undocumented API

    Args:
        url (str): The url of webnovel.com chapter

    Raises:
        LookupError: 404 Error; File not found
        LookupError: 403 Error; Forbidden
        
    Returns:
        list: content, title, prev_url, next_url
    """
    bookId, chapterId = re.findall('_(\d{5,})', url)
    apiCallUrl = f"https://www.webnovel.com/apiajax/chapter/GetContent?_csrfToken=94w9XBrUFO69c33tsjJ1rcElpIEJmkWqinj48dbH&bookId={bookId}&chapterId={chapterId}&_=1597089803712"
    DATA = SESSION.get(apiCallUrl)
    
    if DATA.status_code == 404: 
        raise LookupError("No Page", "No page accessable by that url; or website not allowing access")
    elif DATA.status_code == 403:
        raise LookupError("Forbidden",     "Scraper not allowed access by ddos protection (probably)")

    # Get the data in json format 
    SOUP = BeautifulSoup(DATA.text, 'lxml')
    body = SOUP.find('body')
    content = json.loads(body.text)
    
    title = content['data']['bookInfo']['bookName']
    bookTitle = title.lower().replace(" ", "-")

    chapterInfo = content['data']['chapterInfo']

    # IDs
    nextChapterId, prevChapterId = chapterInfo['nextChapterId'], chapterInfo['preChapterId' ]

    # Titles
    nextChapterTitle = chapterInfo['nextChapterName'].lower().replace(" ", "-") if nextChapterId != -1 else None
    prevChapterTitle = chapterInfo['preChapterName' ].lower().replace(" ", "-") if prevChapterId != -1 else None
    
    # Construct urls dynamically
    next_url = f"https://www.webnovel.com/book/{bookTitle}_{bookId}/{nextChapterTitle}_{nextChapterId}" if nextChapterTitle != None else None
    prev_url = f"https://www.webnovel.com/book/{bookTitle}_{bookId}/{prevChapterTitle}_{prevChapterId}" if prevChapterTitle != None else None

    content = [f"<p>{obj['content']}</p>" for obj in chapterInfo['contents']]
    content = "".join(content).replace("â¦", "...") # Reformmating data to be more readable and accessable
    
    SOUP = BeautifulSoup(content, "html.parser")
    content = "\n".join([f"{element.text}" for element in SOUP.findAll("p", whitespace = False)])
    
    return content, title, prev_url, next_url