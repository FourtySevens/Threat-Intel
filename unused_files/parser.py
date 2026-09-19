from bs4 import BeautifulSoup

def extract_text(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup
