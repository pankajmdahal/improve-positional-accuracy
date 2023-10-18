from bs4 import BeautifulSoup as bs

url = "https://domino.bnsf.com/website/stcc.nsf/SearchResults?readform&STCC=1&Commodity=&Contact="

html = requests.get(url)


soup = bs(html.text, "html.parser")
tds = soup.find_all(text=True)





from urllib2 import Request, urlopen, URLError
from TableParser import TableParser
url_addr ="https://domino.bnsf.com/website/stcc.nsf/SearchResults?readform&STCC=1&Commodity=&Contact="
req = Request(url_addr)
url = urlopen(req)
tp = TableParser()
tp.feed(url.read())












html = etree.HTML(s)