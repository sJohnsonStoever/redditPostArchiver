#!/usr/bin/env python3
from urlextract import URLExtract


def extract_urls(body):
    urlset = set()
    extractor = URLExtract()
    excluded = ['.id', '.you', '.lol', '.like', '.now', '.my', '.love', '.phone', '.how', '.post', '.me', '.got',
                '.hot', '.im', '.best']
    for url in extractor.gen_urls(body):
        if len(url) < 5 or '.' not in url:
            continue
        if url.count('http') == 1:
            url = url.split('http')[1]
            url = 'http{}'.format(url)
        if '(' in url:
            rurl = url.split('(')
            if extractor.has_urls(rurl[1]):
                url = rurl[1]
            elif extractor.has_urls(rurl[0]):
                url = rurl[0]
            else:
                continue
        if ')' in url:
            lurl = url.split(')')
            if extractor.has_urls(lurl[0]):
                url = lurl[0]
            elif extractor.has_urls(lurl[1]):
                url = lurl[1]
            else:
                continue
        sem = 0
        for suffix in excluded:
            if url.endswith(suffix):
                sem = 1
        if sem == 1:
            continue
        # """
        if 'http://[IMG]http://' in url:
            url = url.replace('http://[IMG]http://', '')
        if '[/IMG]' in url:
            url = url.replace('[/IMG]', '')
        if url.endswith('?fb'):
            url = url.replace('?fb', '')
        if url.endswith('?noredirect'):
            url = url.replace('?noredirect', '')
        elif url.endswith('_d.jpg?maxwidth=640&amp;shape=thumb&amp;fidelity=medium'):
            url = url.replace('_d.jpg?maxwidth=640&amp;shape=thumb&amp;fidelity=medium', '')
        elif url.endswith('?s=sms'):
            url = url.replace('?s=sms', '')
        if '//m.imgur.com' in url:
            url = url.replace('//m.imgur.com', '//imgur.com')
        if url.startswith('https://thumbs.gfycat.com/'):
            url = url.replace('https://thumbs.gfycat.com/', 'https://gfycat.com/')
        if url.endswith('-size_restricted.gif'):
            url = url.replace('-size_restricted.gif', '')
        # """
        urlset.add(url)
    return urlset
