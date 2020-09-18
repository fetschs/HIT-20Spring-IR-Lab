import json
import math
import pickle

from sklearn.model_selection import train_test_split
from tqdm import tqdm

import config
import segment


class Passage:
    average_len = 0
    sum_len = 0
    passage_num = 0
    df_dict = {}

    def __init__(self, passage_id, passage_text, passage_len, passage_tf_dict):
        self.id = passage_id
        self.text = passage_text
        self.len = passage_len
        self.tf_dict = passage_tf_dict
        Passage.passage_num += 1
        Passage.sum_len += self.len
        Passage.average_len = Passage.sum_len / Passage.passage_num
        for word in self.tf_dict.keys():
            Passage.df_dict.setdefault(word, 0)
            Passage.df_dict[word] += 1


def read_passages_from_file(file_path):
    """
    read passages from text file.
    Args:
        file_path: text file path.

    Returns: passages_dict,key is passage_id,value is passage_text

    """
    with open(file_path, "r", encoding="UTF-8") as passage_file:
        passage_jsons = passage_file.readlines()
        passages_dict = {}
        for passage_json in passage_jsons:
            passage_dict = json.loads(passage_json)
            passage_id = passage_dict["pid"]
            passage_text = passage_dict["document"]
            passages_dict[passage_id] = passage_text
        return passages_dict


def handle_passages(passages_dict):
    """
    use word seg handle passages,and cal TF value for each word in each passage.
    Args:
        passages_dict: passages_dict,key is passage_id,value is passage_text

    Returns: Passage Class dict,key is passage_id,value is Passage Class

    """
    handled_passages_dict = {}
    for passage_id, passage_text in tqdm(passages_dict.items()):
        tf_dict = {}
        passage_len = 0
        for sentences in passage_text:
            word_list = segment.wordSeg(sentences, delete_stop_word_flag=False)
            for word in word_list:
                tf_dict.setdefault(word, 0)
                tf_dict[word] += 1
            passage_len += len(word_list)
        for word in tf_dict.keys():
            tf_dict[word] /= passage_len
        handled_passages_dict[passage_id] = Passage(passage_id, passage_text, passage_len, tf_dict)

    return handled_passages_dict


class Index:

    def __init__(self, word, df_val, passage_id_list, tf_val_list):
        self.word = word
        self.df_val = df_val
        self.passage_id_list = passage_id_list
        self.tf_val_list = tf_val_list
        assert (len(self.passage_id_list) == len(self.tf_val_list))

    def __str__(self):
        return Index.index_to_dict(self).__str__()


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
                invert_index[word] = Index(word, Passage.df_dict[word], [], [])
            invert_index[word].passage_id_list.append(passage_id)
            invert_index[word].tf_val_list.append(passage.tf_dict[word])
    return invert_index


# def read_index_from_file(index_file_path):
#     with open(index_file_path, "r", encoding="UTF-8") as index_file:
#         invert_index = json.load(index_file)
#         for key, value in invert_index.items():
#             invert_index[key] = Index.dict_to_index(value)
#         return invert_index


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
    bim_score = math.log10(Passage.passage_num / df_value)
    word_in_passage_score = ((1 + k1) * tf_passage_value) / (
            k1 * ((1 - b) + b * (len_passage / Passage.average_len)) + tf_passage_value)
    word_in_query_score = ((1 + k3) * tf_query_value) / (k3 + tf_query_value)
    return bim_score * word_in_passage_score * word_in_query_score


def find_passages_for_query(query, invert_index, handled_passages_dict, return_num=1):
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
    return result[0:return_num]


def read_train_dataset(train_file_path):
    """
    read train dataset from file.
    Args:
        train_file_path: train dataset file path.

    Returns:
        train_questions: train questions set.
        train_answers: train labels set.
    """
    with open(train_file_path, "r", encoding="UTF-8") as train_file:
        train_questions = []
        train_answers = []
        json_lines = train_file.readlines()
        train_data_dicts = []
        for json_line in json_lines:
            train_data_dicts.append(json.loads(json_line))
        train_data_dicts = sorted(train_data_dicts, key=lambda x: x["qid"])
        for train_data_dict in train_data_dicts:
            train_questions.append({"qid": train_data_dict.pop("qid"),
                                    "question": train_data_dict.pop("question")})
            train_answers.append(train_data_dict)
    return train_questions, train_answers


def read_test_dataset(test_file_path):
    """
    read test dataset from file.
    Args:
        test_file_path: test dataset path

    Returns:
        test_questions: test questions.
    """
    with open(test_file_path, "r", encoding="UTF-8") as train_file:
        test_questions = []
        json_lines = train_file.readlines()
        test_data_dicts = []
        for json_line in json_lines:
            test_data_dict = json.loads(json_line)
            test_data_dicts.append(test_data_dict)
        test_data_dicts = sorted(test_data_dicts, key=lambda x: x["qid"])
        for test_data_dict in test_data_dicts:
            test_questions.append({"qid": test_data_dict.pop("qid"),
                                   "question": test_data_dict.pop("question")})
    return test_questions


def eval_BM25(questions, gold_answers, invert_index, handled_passages_dict):
    """
    eval BM25 model,use acc.
    Args:
        questions: query will be use for find related document.
        gold_answers: gold related document for query.
        invert_index: invert index,which should get by build_invert_index() function.
        handled_passages_dict: passage dict,which should get by handle_passages.

    Returns:

    """
    pred_passages_ids = get_related_result(questions, invert_index, handled_passages_dict)
    correct_pid = 0

    for ind, gold_answer in enumerate(gold_answers):
        temp_pid = gold_answer["pid"]
        if temp_pid in pred_passages_ids[ind]:
            correct_pid += 1
    print("Top 1 ACC:" + str(correct_pid / len(gold_answers)))


def preprocess_index_to_disk():
    """
    preprocess dataset, then dump index to disk
    Returns:

    """
    passages_dict = read_passages_from_file(config.PAGE_FILE_PATH)
    handled_passages_dict = handle_passages(passages_dict)
    with open(config.HANDLED_PASSAGES_FILE_PATH, "wb") as handled_passages_dict_file:
        pickle.dump(handled_passages_dict, handled_passages_dict_file)
    with open(config.PASSAGES_CONFIG_PATH, "wb") as passage_config_file:
        pickle.dump(
            {"df_dict": Passage.df_dict, "passage_num": Passage.passage_num, "average_len": Passage.average_len},
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
        Passage.df_dict = config_dict["df_dict"]
        Passage.passage_num = config_dict["passage_num"]
        Passage.average_len = config_dict["average_len"]
    return handled_passages_dict, invert_index


def get_related_result(questions, invert_index,
                       handled_passages_dict):
    pred_passages_ids = []
    for question in tqdm(questions):
        results = find_passages_for_query(question["question"], invert_index,
                                          handled_passages_dict)
        pred_passages_ids.append([])
        for result in results:
            result_id = result[0]
            pred_passages_ids[-1].append(result_id)
    return pred_passages_ids


def main():
    """
    main function
    Returns:

    """
    handled_passages_dict, invert_index = load_index_in_disk(config.HANDLED_PASSAGES_FILE_PATH, config.INDEX_FILE_PATH,
                                                             config.PASSAGES_CONFIG_PATH)
    train_questions, train_answers = read_train_dataset(train_file_path=config.QA_TRAIN_FILE_PATH)
    train_questions, dev_questions, train_answers, dev_answers = train_test_split(train_questions, train_answers,
                                                                                  test_size=0.10, random_state=0)
    print("START EVAL BM25...")
    eval_BM25(dev_questions, dev_answers, invert_index, handled_passages_dict)
    print("EVAL BM25 OK！")


if __name__ == '__main__':
    preprocess_index_to_disk()
    main()
