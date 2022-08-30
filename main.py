import os
import sys
import time
import json
from typing import Optional, Tuple, Union
from urllib import request, parse
from http.client import HTTPResponse, IncompleteRead


def http_request(method, url, params=None, headers=None, data: Optional[Union[dict, list, bytes]] = None, timeout=None, logger=None) -> Tuple[HTTPResponse, str]:
    if params:
        url = f'{url}?{parse.urlencode(params)}'
    if not headers:
        headers = {}
    if data and isinstance(data, (dict, list)):
        data = json.dumps(data, ensure_ascii=False).encode()
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json; charset=utf-8'
    if logger:
        logger.info(f'request: {method} {url}')
    req = request.Request(url, method=method, headers=headers, data=data)
    res = request.urlopen(req, timeout=timeout)  # raises: (HTTPException, URLError)
    try:
        body: str = res.read().decode()
    except IncompleteRead as e:
        body: str = e.partial.decode()
    if logger:
        logger.debug(f'response: {res.status}, {body}')
    return res, body


class HTTPError(Exception):
    def __init__(self, status, body) -> None:
        self.status = status
        self.body = body

    def __str__(self):
        return f'HTTPError: {self.status}, {self.body}'


def yield_posts(base_url, page, limit=12):
    """
    {
        "posts": []
    }
    """
    url = f'{base_url}/api/posts?page={page}&limit={limit}'
    print(f'get posts of page {page}')
    res, body = http_request('GET', url)
    if res.status != 200:
        raise HTTPError(res.status, body)
    data = json.loads(body)
    for i in data['posts']:
        yield i


def get_all_posts(base_url):
    posts = []
    page = 1
    while page:
        if page > 1:
            time.sleep(1)
        next_posts = list(yield_posts(base_url, page))
        if not next_posts:
            break
        posts.extend(next_posts)
        page += 1
    return posts


xml_item_tmpl = """<item>
  <title>{title}</title>
  <description>{summary}</description>
  <link>{url}</link>
  <guid isPermaLink="true">{url}</guid>
  <dc:creator>{author}</dc:creator>
  <pubDate>{published_at}</pubDate>
</item>
"""

def post_to_xml(base_url, post):
    """
    {
        title
        brief (desc)
        author
            name
        slug
        dateAdded
    }
    """
    d = dict(
        title=post['title'],
        summary=post['brief'],
        author=post['author']['name'],
        url=f'{base_url}/{post["slug"]}',
        published_at=post['dateAdded'],
    )
    return xml_item_tmpl.format(**d)


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def main():
    base_url = os.environ['BASE_URL']

    #file_start, file_end = read_file(sys.argv[1]), read_file(sys.argv[2])
    posts = get_all_posts(base_url)
    print(f'posts: len={len(posts)}')
    print(f'post: {posts[0]}')


if __name__ == '__main__':
    main()
