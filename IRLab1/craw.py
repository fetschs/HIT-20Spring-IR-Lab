#!/usr/bin/python
# coding:utf-8


import json
import re
import time
import os
import unicodedata
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from multiprocessing import Pool

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/80.0.3987.163 Safari/537.36 ",
    "Connection": "close"
}

URLS_FILE_PATH = "urls.txt"
IMG_DIR_PATH = r"attachment/img/"
DOC_DIR_PATH = r"attachment/doc/"
OTHER_DIR_PATH = r"attachment/other/"
JSON_DIR_PATH = r"jsons/"
DOC_FILE_TYPE_LIST = ["doc", "docx", "txt", "pdf"]


def get_http_status_code(target_url):
    """
    get status code, for get an url.
    :param target_url: url will be get
    :return: status code
    """
    try:
        request = requests.get(target_url, headers=HEADERS)
        http_status_code = request.status_code
        return http_status_code
    except requests.exceptions.HTTPError as e:
        return e


def check_url(target_url):
    """
    check if url is working, use 200 status code.
    :param target_url: url will be check
    :return: true or false.
    """
    try:
        if get_http_status_code(target_url) == 200:
            return True
        else:
            return False
    except Exception as e:
        print(e)


def get_urls():
    """
    get urls set from hitgs.hit.edu.cn
    :return: urls list(unique)
    """
    if os.path.exists(URLS_FILE_PATH):
        with open(URLS_FILE_PATH, "r") as url_f:
            return json.load(url_f)

    target_urls = []
    chrome_opt = Options()
    chrome_opt.add_argument('--headless')
    chrome_opt.add_argument('--window-size=1366,768')
    driver = webdriver.Chrome(options=chrome_opt)

    for start_num in range(1, 92):
        index_url = "http://hitgs.hit.edu.cn/tzgg_2340/list" + str(start_num) + ".htm"
        driver.get(index_url)
        title_labels = driver.find_elements_by_class_name("news_title")
        for title_label in title_labels:
            target_urls.append(title_label.find_element_by_tag_name('a').get_attribute("href"))
        time.sleep(0.1)
    driver.quit()
    target_urls = list(set(target_urls))
    ret_urls = []
    for target_url in target_urls:
        if "http://hitgs.hit.edu.cn/" not in target_url:
            continue
        if check_url(target_url):
            ret_urls.append(target_url)
    return ret_urls


def fix_invalid_name(name):
    """
    check and fix invalid file name to save in windows.
    :param name: the file name
    :return: the valid name ,new or orgin.
    """
    reg = re.compile(r'[\\/:*?"<>|\r\n]+')
    invalid_matches = reg.findall(name)
    if invalid_matches:
        for invalid_match in invalid_matches:
            name = name.replace(invalid_match, "_")
    return name


def make_sure_attach_path(attach_name, cur_id):
    """
    check whether doc or other attachment.
    :param attach_name:
    :param cur_id:
    :return:
    """
    if any(file_type in attach_name for file_type in DOC_FILE_TYPE_LIST):
        return os.path.join(DOC_DIR_PATH, cur_id), os.path.join(DOC_DIR_PATH, cur_id, attach_name)
    else:
        return os.path.join(OTHER_DIR_PATH, cur_id), os.path.join(OTHER_DIR_PATH, cur_id, attach_name)


def get_response(target_url):
    while True:
        try:
            response = requests.get(target_url, headers=HEADERS, timeout=100)
            print("Get Response!")
            return response
        except requests.exceptions.ConnectionError:
            print("Connection Error! Retry.")
            continue


def crawl_from_url(news_url, cur_id):
    """
    from a url , get url,title,paragraphs and filesName
    :return: the target dict
    """
    # time.sleep(1)

    print(news_url, cur_id)
    result = {"url": news_url}
    news_response = get_response(news_url)

    news_response.encoding = news_response.apparent_encoding
    soup = BeautifulSoup(news_response.text, 'html5lib')
    result["title"] = unicodedata.normalize('NFKC', soup.find("title").text)
    contents = soup.find("div", attrs={"class": "wp_articlecontent"})

    if contents is None:
        result["paragraphs"] = ""
        result["file_name"] = []
        with open(JSON_DIR_PATH + cur_id + ".json", "w", encoding="utf-8") as json_f:
            json.dump(result, json_f, ensure_ascii=False)
        return

    result["paragraphs"] = unicodedata.normalize('NFKC', contents.text)
    img_labels = contents.find_all("img")
    result["file_name"] = []

    for img_label in img_labels:
        img_url = "http://hitgs.hit.edu.cn" + img_label.get("src")
        if not check_url(img_url):
            continue
        if "_upload" not in img_url:
            continue

        print(img_url, cur_id)
        img_response = get_response(img_url)

        img_name = os.path.basename(img_url)
        img_name = fix_invalid_name(img_name)
        result["file_name"].append(img_name)
        result_dir_path = os.path.join(IMG_DIR_PATH, cur_id)
        img_file_path = os.path.join(result_dir_path, img_name)
        if not os.path.exists(result_dir_path):
            os.makedirs(result_dir_path)
        with open(img_file_path, "wb") as img_f:
            img_f.write(img_response.content)

    attach_labels = contents.select("a[href]")
    for attach_label in attach_labels:
        attach_url = "http://hitgs.hit.edu.cn" + attach_label.get('href')
        if "_upload" not in attach_url:
            continue
        if not check_url(attach_url):
            continue

        attach_name = os.path.basename(attach_url)
        attach_name = attach_name[attach_name.rfind('.'):]
        temp_name = attach_label.text.strip()
        if '.' in temp_name:
            temp_name = temp_name[:temp_name.rfind('.')]
        if len(temp_name) == 0:
            attach_name = os.path.basename(attach_url)
        attach_name = temp_name + attach_name
        result["file_name"].append(attach_name)
        attach_name = fix_invalid_name(attach_name)

        print(attach_url, cur_id)
        attach_response = get_response(attach_url)

        result_dir_path, file_path = make_sure_attach_path(attach_name, cur_id)
        if not os.path.exists(result_dir_path):
            os.makedirs(result_dir_path)
        with open(file_path, "wb") as attach_f:
            attach_f.write(attach_response.content)

    with open(JSON_DIR_PATH + cur_id + ".json", "w", encoding="utf-8") as json_f:
        json.dump(result, json_f, ensure_ascii=False)


if __name__ == '__main__':
    if not os.path.exists(IMG_DIR_PATH):
        os.makedirs(IMG_DIR_PATH)
    if not os.path.exists(DOC_DIR_PATH):
        os.makedirs(DOC_DIR_PATH)
    if not os.path.exists(OTHER_DIR_PATH):
        os.makedirs(OTHER_DIR_PATH)
    if not os.path.exists(JSON_DIR_PATH):
        os.makedirs(JSON_DIR_PATH)
    print("Finish create dir")
    urls = get_urls()
    with open(URLS_FILE_PATH, 'w') as f:
        json.dump(urls, f)

    # use multi processes for crawl

    urls_index = [str(i) for i in range(len(urls))]
    zip_args = list(zip(urls, urls_index))

    crawl_from_url(urls[1], str(1))
    # pool = Pool(4)
    # pool.starmap(crawl_from_url, zip_args)
    # pool.close()
    # pool.join()

    # transDict2Json
    # with open("data.json", "w", encoding="utf-8") as f_all:
    #     for ind in range(len(urls)):
    #         if not os.path.exists(JSON_DIR_PATH + str(ind) + ".json"):
    #             crawl_from_url(urls[ind], str(ind))
    #         with open(JSON_DIR_PATH + str(ind) + ".json", 'r', encoding="utf-8") as f:
    #             f_all.write(f.readline() + "\n")

    # show the result of json file
    # with open('data.json', encoding='utf-8') as fin:
    #     read_results = [json.loads(line.strip()) for line in fin.readlines()]
    # print(read_results)
