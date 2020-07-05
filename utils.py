#!/usr/bin/env python3
from urlextract import URLExtract


def extract_urls(body):
    urlset = set()
    extractor = URLExtract()
    excluded = ['.id', '.you', '.lol', '.like', '.now', '.my', '.love', '.phone', '.how', '.post', '.me', '.got',
                '.hot', '.im', '.best']
    try:
        generatedUrls = extractor.gen_urls(body)
        for url in generatedUrls:
            if len(url) < 5 or '.' not in url:
                continue
            if url.count('http') == 1:
                try:
                    url = url.split('http')[1]
                url = 'http{}'.format(url)
            if '(' in url:
                try:
                    rurl = url.split('(')
                if extractor.has_urls(rurl[1]):
                    url = rurl[1]
                elif extractor.has_urls(rurl[0]):
                    url = rurl[0]
                else:
                    continue
            if ')' in url:
                try:
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
            if '[IMG]' in url:
                try:
                    url = url.split('[IMG]')[1]
                except IndexError:
                    pass
            if '[/IMG]' in url:
                try:
                    url = url.split('[/IMG]')[0]
                except IndexError:
                    pass
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
    except IndexError as e:
        raise e
        print("While generating urls, an AttributeError (specifically {e}) was raised. Moving on without extracting urls for now. This is likely an error with the python library URLExtract (https://github.com/lipoja/URLExtract). The issue has been fixed (see issue fix here: https://github.com/lipoja/URLExtract/commit/aa51f52e77b104932c49fb14882c632f12b6e940) but is has not included in the most recent release. Please install the version from GitHub to fix this issue (eg. pip3 install git+https://github.com/lipoja/URLExtract.git".format(e=e))
    finally:
        return urlset # which is empty
