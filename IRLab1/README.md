# HIT-2020-IRLAB1
## 环境配置
pip install requirement.txt

pyltp的安装很可能遇到各种奇怪的问题，可以联系我解决。

selenium库所使用的chromedriver需要安装本地的chrome浏览器对应版本

或者直接使用爬取好的urls.txt
## 功能
爬取哈工大研究生院所有通知公告及其中附件并下载保存，对爬取到的网页正文和网页标题进行分词和去停用词处理。

部分通知公告页面内容为空，通知公告的URL列表保存在urls.json中。

结果保存在attachment文件夹和jsons文件夹中。

合并后用于提交的json保存于data.json中。

运行craw.py即可爬取对应内容。

运行segment.py即可完成分词和去停用词。

stopwords.txt存放停用词

处理后的json保存于preprocessed.json中。