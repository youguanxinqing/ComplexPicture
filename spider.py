import os
import re
import json
import requests
from urllib import parse
from hashlib import md5
from concurrent.futures import ThreadPoolExecutor

from CONFIG import *


def get_one_html(url, params, tries=3):
    """获取网页"""
    try:
        response = requests.get(url=url, headers=HEADERS, params=params)
    except requests.HTTPError:
        if tries > 0:
            get_one_html(url, parse, tries-1)
        else:
            return None
    else:
        return response.text


def extract_data(data):
    """提取key"""
    # 利用正则匹配pins = ...
    result = re.search(r'app.page\["pins"\] = (.+?);', data)
    # 如果存在
    if result:
        # 字符串的列表（"['z', 't', 'y']"）-> 列表（['z', 't', 'y']）
        pins = json.loads(result.group(1))
        for pin in pins:
            # 取出key值
            key = pin["file"]["key"]

            yield parse.urljoin(IMG_URL, key)  # 拼接url


def get_img(url, tries=3):
    """请求图片"""
    try:
        response = requests.get(url, headers=HEADERS)
    except requests.HTTPError:
        if tries > 0:
            get_img(url, tries-1)
        else:
            return None, None
    else:
        return response.content, response.url


def save_img(imgStream, url):
    """保存图片"""
    # MD5加密，构建图片名
    m = md5()
    m.update(url.encode("utf-8"))
    filename = m.hexdigest()
    # print(filename)
    with open("imgs/{}.png".format(filename), "wb") as file:
        file.write(imgStream)
    print("{filename}.png保存成功".format(filename=filename))


def init():
    """初始化，动态创建imgs目录"""
    dirname = "{}/imgs".format(os.path.abspath(os.path.dirname(__file__)))
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def main(page):
    PARAMS = {
        "jn8pvql9": "",
        "page": page,
        "per_page": 20,
        "wfl": 1,
    }
    html = get_one_html(URL, PARAMS)
    if html:
        for url in extract_data(html):
            imgStream, url = get_img(url)
            if all([imgStream, url]):
                save_img(imgStream, url)

def threading_main():
    print("正在准备从花瓣网下载图片源...")
    init()

    with ThreadPoolExecutor() as pool:
        pool.map(main, range(1, 200))

if __name__ == "__main__":
    threading_main()