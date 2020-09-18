import json
import math
import os
import pickle
import docx
from win32com import client as wc
from sklearn.model_selection import train_test_split
from tqdm import tqdm

import config
import segment
import pdfplumber


class Page:
    average_len = 0
    sum_len = 0
    page_num = 0
    df_dict = {}

    def __init__(self, page_id, page_content, page_len, page_tf_dict):
        self.id = page_id
        self.text = page_content
        self.len = page_len
        self.tf_dict = page_tf_dict
        Page.page_num += 1
        Page.sum_len += self.len
        Page.average_len = Page.sum_len / Page.page_num
        for word in self.tf_dict.keys():
            Page.df_dict.setdefault(word, 0)
            Page.df_dict[word] += 1


def read_pages_from_file(page_file_path):
    """
    read passages from text file.
    Args:
        page_file_path: text file path.

    Returns: page_dict,key is page_id,value is page_content

    """
    with open(page_file_path, "r", encoding="UTF-8") as passage_file:
        page_json_lines = passage_file.readlines()
        page_dict = {}
        for page_json in page_json_lines:
            temp_page_dict = json.loads(page_json)
            page_id = temp_page_dict["page_id"]
            page_content = temp_page_dict["content"]
            if len(page_content) != 0:
                page_dict[page_id] = page_content
        return page_dict


def read_doc_from_dir(doc_root_dir, start_id):
    doc_dirs_name = os.listdir(doc_root_dir)
    document_id = start_id
    document_dict = {}
    for doc_dir_name in tqdm(doc_dirs_name):
        doc_dir_path = os.path.join(doc_root_dir, doc_dir_name)
        doc_files_name = os.listdir(doc_dir_path)
        for doc_file_name in doc_files_name:
            doc_file_path = os.path.join(doc_dir_path, doc_file_name)
            doc_file_path = os.path.abspath(doc_file_path)
            if doc_file_name.find(".pdf") != -1:
                document_id += 1
                with pdfplumber.open(doc_file_path) as pdf_file:
                    pages_text_list = []
                    for page in pdf_file.pages:
                        if page.extract_text() is not None:
                            pages_text_list.append(page.extract_text())
                document_dict[document_id] = segment.get_sentences("".join(pages_text_list))
            elif doc_file_name.find(".docx") != -1:
                document_id += 1
                doc = docx.Document(doc_file_path)
                paragraphs_text_list = []
                for paragraph in doc.paragraphs:
                    if paragraph.text is not None:
                        paragraphs_text_list.append(paragraph.text)
                document_dict[document_id] = segment.get_sentences("".join(paragraphs_text_list))
    return document_dict


def handle_pages(content_dict):
    """
    use word seg handle passages,and cal TF value for each word in each passage.
    Args:
        content_dict: content_dict,key is id,value is content

    Returns: Passage Class dict,key is id,value is Passage Class

    """
    handled_pages_dict = {}
    for page_id, page_content in tqdm(content_dict.items()):
        tf_dict = {}
        page_len = 0
        for sentences in page_content:
            word_list = segment.wordSeg(sentences, delete_stop_word_flag=True)
            for word in word_list:
                tf_dict.setdefault(word, 0)
                tf_dict[word] += 1
            page_len += len(word_list)
        for word in tf_dict.keys():
            tf_dict[word] /= page_len
        handled_pages_dict[page_id] = Page(page_id, page_content, page_len, tf_dict)

    return handled_pages_dict


class Index:

    def __init__(self, word, df_val, passage_id_list, tf_val_list):
        self.word = word
        self.df_val = df_val
        self.passage_id_list = passage_id_list
        self.tf_val_list = tf_val_list
        assert (len(self.passage_id_list) == len(self.tf_val_list))


def build_invert_index(passages_dict):
    """
    build invert index,save tf value and passage_id.
    Args:
        passages_dict: dict,key is passage_id, value is Passage class.

    Returns:
        invert_index:dict,key is word,then next key is Invert class.
    """
    invert_index = {}
    for passage_item in tqdm(passages_dict.items()):
        passage_id = passage_item[0]
        passage = passage_item[1]
        passage_words = passage.tf_dict.keys()
        for word in passage_words:
            if word not in invert_index:
                invert_index[word] = Index(word, Page.df_dict[word], [], [])
            invert_index[word].passage_id_list.append(passage_id)
            invert_index[word].tf_val_list.append(passage.tf_dict[word])
    return invert_index


def get_rsv_by_BM25(df_value, tf_passage_value, tf_query_value, len_passage, k1=config.BM_K1, k3=config.BM_K3,
                    b=config.BM_B):
    """
    cal rsv(score for passage) use BM25 model,for a query word in a passage.
    Args:
        df_value: the DF value of this word in passages.
        tf_passage_value: the TF value of this word in this passage text.
        tf_query_value: the TF value of this word in this query text.
        len_passage: the len of passage.
        k1: experienced parameter
        k3: experienced parameter
        b: experienced parameter

    Returns:
        rsv_value
    """
    bim_score = math.log10(Page.page_num / df_value)
    word_in_passage_score = ((1 + k1) * tf_passage_value) / (
            k1 * ((1 - b) + b * (len_passage / Page.average_len)) + tf_passage_value)
    word_in_query_score = ((1 + k3) * tf_query_value) / (k3 + tf_query_value)
    return bim_score * word_in_passage_score * word_in_query_score


def find_passages_for_query(query, invert_index, handled_passages_dict):
    query_words = segment.wordSeg(query, delete_stop_word_flag=False)
    rsv_passages = {}
    for query_word in query_words:
        if query_word in invert_index.keys():
            now_index = invert_index[query_word]
            tf_query_value = query_words.count(query_word) / len(query_words)
            for passage_id, tf_val in zip(now_index.passage_id_list, now_index.tf_val_list):
                rsv_passages.setdefault(passage_id, 0)
                rsv_passages[passage_id] += get_rsv_by_BM25(df_value=now_index.df_val, tf_passage_value=tf_val,
                                                            tf_query_value=tf_query_value,
                                                            len_passage=handled_passages_dict[passage_id].len,
                                                            )

    result = sorted(rsv_passages.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    return result


def preprocess_index_to_disk():
    """
    preprocess dataset, then dump index to disk
    Returns:

    """
    page_dict = read_pages_from_file(config.PREPROCESSED_PAGE_JSON_FILE_PATH)
    document_dict = read_doc_from_dir(config.DOC_DIR_PATH, len(page_dict) + 1)
    page_dict.update(document_dict)
    handled_passages_dict = handle_pages(page_dict)
    with open(config.HANDLED_PASSAGES_FILE_PATH, "wb") as handled_passages_dict_file:
        pickle.dump(handled_passages_dict, handled_passages_dict_file)
    with open(config.PASSAGES_CONFIG_PATH, "wb") as passage_config_file:
        pickle.dump(
            {"df_dict": Page.df_dict, "page_num": Page.page_num, "average_len": Page.average_len},
            passage_config_file)
    print("Handled Passages OK!")
    invert_index = build_invert_index(handled_passages_dict)
    with open(config.INDEX_FILE_PATH, "wb") as index_file:
        pickle.dump(invert_index, index_file)
    print("Build Index OK!")


def load_index_in_disk(passage_file_path, index_file_path, passages_config_path):
    with open(passage_file_path, "rb") as handled_passages_dict_file:
        handled_passages_dict = pickle.load(handled_passages_dict_file, encoding="UTF-8")
    with open(index_file_path, "rb") as index_file:
        invert_index = pickle.load(index_file, encoding="UTF-8")
    with open(passages_config_path, "rb") as passage_config_file:
        config_dict = pickle.load(passage_config_file)
        Page.df_dict = config_dict["df_dict"]
        Page.page_num = config_dict["page_num"]
        Page.average_len = config_dict["average_len"]
    return handled_passages_dict, invert_index


def main():
    """
    main function
    Returns:

    """
    preprocess_index_to_disk()
    # handled_passages_dict, invert_index = load_index_in_disk(config.HANDLED_PASSAGES_FILE_PATH, config.INDEX_FILE_PATH,
    #                                                          config.PASSAGES_CONFIG_PATH)


if __name__ == '__main__':
    main()
