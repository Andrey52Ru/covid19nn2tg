import re
import requests
from bs4 import BeautifulSoup


def get_posts(url):
    page = requests.get(url)
    if page.status_code != 200:
        return {}

    soap = BeautifulSoup(page.text, features="html.parser")

    posts = {}
    for item in soap.find_all(name='div', attrs={'class': "wall_item"}):
        # msg = item.find(name='div', attrs={'class': "wi_body"})
        post_id = item.find(name='a', attrs={'class': ["post__anchor", "anchor"]})['name']
        dt = item.find(name='a', attrs={'class': "wi_date"}).text
        text = item.find(name='div', attrs={'class': "pi_text"})
        text_more = text.find(name='a', attrs={'class': 'pi_text_more'})
        if text_more:
            text_more.decompose()
        media_url = [re.sub(r'\|.*', '', m['data-src_big']) for m in
                     item.find_all(name='div', attrs={'class': 'thumb_map_img_as_div'})]
        posts[post_id] = {'date': dt, "text": text.text, 'media_url': media_url}
    return posts
