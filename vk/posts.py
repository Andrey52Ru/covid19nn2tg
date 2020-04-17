import re
import requests
from bs4 import BeautifulSoup


def get_posts(url):
    posts = {}
    try:
        page = requests.get(url)
        if page.status_code != 200:
            return posts

        soap = BeautifulSoup(page.text, features="html.parser")

        for item in soap.find_all(name='div', attrs={'class': "wall_item"}):
            # skip pinned
            if item.find(name='div', attrs={'class': 'wi_explain'}).text == "запись закреплена":
                continue
            # msg = item.find(name='div', attrs={'class': "wi_body"})
            post_id = item.find(name='a', attrs={'class': ["post__anchor", "anchor"]})['name']
            dt = item.find(name='a', attrs={'class': "wi_date"}).text
            text = item.find(name='div', attrs={'class': "pi_text"})
            tag_more = text.find(name='a', attrs={'class': 'pi_text_more'})
            if tag_more:
                tag_more.decompose()
            media_url = [re.sub(r'\|.*', '', m['data-src_big']) for m in
                         item.find_all(name='div', attrs={'class': 'thumb_map_img_as_div'})]
            posts[post_id] = {'date': dt, "text": text.text, 'media_url': media_url}
    except NameError as e:
        print(e)

    return posts
