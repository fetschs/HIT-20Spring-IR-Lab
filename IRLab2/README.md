# HIT-2020-IRLAB2

## 环境配置

pip install requirement.txt

pyltp的安装很可能遇到各种奇怪的问题，可以联系我解决。

LTP模型需要自行下载配置。需要cws ner pos三种model

## 功能

一个简答的问答系统实现。

首先运行preprocessed.py,生成索引文件。

之后运行question_classification.py可以训练所需要的问题分类模型。

之后可以运行answer_sentnece_selection.py测试SVMRank的答案句排序效果。

也可以直接运行answer_span_selection.py，完成对测试集答案的抽取。

stopwords.txt存放停用词

处理后的json保存于data/test_answer.json中。