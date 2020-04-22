#!/usr/bin/python
# coding:utf-8

"""
@author: Mingxiang Tuo
@contact: tuomx@qq.com
@file: demo.py
@time: 2019/4/28 11:01
实验一的整个程序逻辑框架的简单示例（也可以按自己的逻辑写），同学们只需要指定urls集合以及完成爬虫工具提取网页内容及附件的逻辑即可
"""

import json

def get_urls():
    '''
    指定urls集合(总共1000个)，例如从某些新闻网站上，通过查看所有新闻的页面，可以获取大量url
    :return:
    '''
    # TODO: 获取urls集合并返回
    urls = ['' for i in range(10)]
    return urls

def craw(url):
    '''
    提取网页内容及附件，返回一个字典对象
    :return:
    '''

    # TODO: 使用爬虫工具提取网页内容及附件，返回一个字典对象, 这里只是个简单的示例
    result = {
        "url": "http://today.hit.edu.cn/article/2019/03/25/65084",
        "title": "计算机学院召开第3次科创俱乐部主席联席会",
        "paragraphs": "3月16日中午召开了计算机学院2019年春季学期第3次科创俱乐部主席联席会，...",
        "file_name": ['picture1.jpg', 'picture2.jpg']
    }

    return result


if __name__ == '__main__':
    # url集合示例
    urls = get_urls()
    results = []
    for url in urls:
        # 这个是用爬虫爬取并处理后得到的一个字典对象
        results.append(craw(url))

    # 保存成json文件的示例
    with open('data.json', 'w', encoding='utf-8') as fout:
        for sample in results:
            # 注意一定要加上换行符
            fout.write(json.dumps(sample, ensure_ascii=False)+'\n')

    # 从json文件中读取数据的示例
    read_results = []
    with open('data.json', encoding='utf-8') as fin:
        read_results = [json.loads(line.strip()) for line in fin.readlines()]

    print(read_results)