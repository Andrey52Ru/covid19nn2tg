import re
import requests
from urllib.parse import unquote
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(r"vk_parser")
logger.setLevel(logging.ERROR)


def get_posts(url):
    posts = {}
    try:
        page = requests.get(url)
        if page.status_code != 200:
            return posts
        soap = BeautifulSoup(page.text, features="html.parser")
        page.close()

        for item in soap.find_all(name='div', attrs={'class': "wall_item"}):
            # skip pinned
            if item.find(name='div', attrs={'class': 'wi_explain'}):
                if item.find(name='div', attrs={'class': 'wi_explain'}).text == "запись закреплена" \
                        or item.find(name='div', attrs={'class': 'wi_explain'}).text == "pinned post":
                    continue

            # msg = item.find(name='div', attrs={'class': "wi_body"})
            # print(f'\n\n{msg.prettify()}')

            post_id = item.find(name='a', attrs={'class': ["post__anchor", "anchor"]})['name']
            dt = item.find(name='a', attrs={'class': "wi_date"}).text
            text = item.find(name='div', attrs={'class': "pi_text"})
            tag_more = text.find(name='a', attrs={'class': 'pi_text_more'})
            if tag_more:
                tag_more.decompose()
            media_url = []
            # for m in item.find_all(name='a', attrs={'class': ['thumb_map', 'thumb_map_wide', 'thumb_map_l']}):
            #     if m.has_attr('href'):
            #         media_url.append('https://vk.com' + m['href'])
            # posts[post_id] = {'date': dt, "text": text.text, 'media_url': media_url}
            for m in item.find_all(name='div', attrs={'class': 'pi_medias'}):
                a = m.find(name='a')
                if a:
                    if a.has_attr('href'):
                        if re.match(r'^\/away\.php\?.*', a['href']):
                            media_url.append(unquote(re.search(r'^\/away.php\?to=(.*)\&+.*&', a['href']).group(1)))
                        else:
                            media_url.append('https://vk.com' + a['href'])
            posts[post_id] = {'date': dt, "text": text.text, 'media_url': media_url}

    except NameError as e:
        print(e)

    return posts


# Debug
if __name__ == '__main__':
    p = get_posts("https://vk.com/covid19nn")
    for i in p:
        print(i)
        print(p[i]["media_url"])

