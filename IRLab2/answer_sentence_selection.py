import json
import os

import Levenshtein
import numpy as np
from gensim.summarization import bm25
from sklearn.model_selection import train_test_split
from tqdm import tqdm

import config
import segment
from preprocessed import read_train_dataset, load_index_in_disk, get_related_result


def cal_lcs_len(str_a, str_b):
    lena = len(str_a)
    lenb = len(str_b)
    c = [[0 for i in range(lenb + 1)] for j in range(lena + 1)]
    for i in range(lena):
        for j in range(lenb):
            if str_a[i] == str_b[j]:
                c[i + 1][j + 1] = c[i][j] + 1
            elif c[i + 1][j] > c[i][j + 1]:
                c[i + 1][j + 1] = c[i + 1][j]
            else:
                c[i + 1][j + 1] = c[i][j + 1]
    return c[lena][lenb]


def generate_feature(feature_path, handled_passages_dict, questions, related_passages_ids,
                     gold_answers=None):
    with open(feature_path, "w", encoding="UTF-8") as feature_file:
        gold_answer_sentence = None
        questions = sorted(questions, key=lambda x: x["qid"])
        for ind, (question, related_passage_id_tops) in tqdm(enumerate(zip(questions, related_passages_ids))):

            query_id = question["qid"]
            query_sentence = question["question"]
            answer_sentences = []
            for related_passages_id in related_passage_id_tops:
                passage = handled_passages_dict[related_passages_id]
                answer_sentences.extend(passage.text)
            feature_lines = []
            query_words = segment.wordSeg(query_sentence, delete_stop_word_flag=False)
            corpus = []
            for answer_sentence in answer_sentences:
                answer_sentence_words = segment.wordSeg(answer_sentence, delete_stop_word_flag=True)
                corpus.append(answer_sentence_words)
            # print(corpus)
            bm25_model = bm25.BM25(corpus)
            if gold_answers is not None:
                gold_answer_sentence = gold_answers[ind]["answer_sentence"][0]
            for sentence_ind, answer_sentence in enumerate(answer_sentences):
                feature_lines.append([])
                answer_sentence_words = segment.wordSeg(answer_sentence, delete_stop_word_flag=True)
                feature_lines[sentence_ind].append(len(answer_sentence))  # len of answer sentence
                feature_lines[sentence_ind].append(1 if answer_sentence.find(":") != -1 else 0)  # whether include :
                feature_lines[sentence_ind].append(
                    abs(len(answer_sentence_words) - len(query_words)))  # words len difference
                feature_lines[sentence_ind].append(
                    len(set(answer_sentence_words).intersection(set(query_words))))  # uni-gram co-occur
                feature_lines[sentence_ind].append(
                    len(set(answer_sentence).intersection(set(query_sentence))))  # char co-occur
                feature_lines[sentence_ind].append(cal_lcs_len(answer_sentence, query_sentence))  # LCS len
                feature_lines[sentence_ind].append(
                    Levenshtein.distance(answer_sentence, query_sentence))  # edit distance
                feature_lines[sentence_ind].append(bm25_model.get_score(query_words, sentence_ind))  # BM25 value
            for sentence_ind, feature_line in enumerate(feature_lines):
                if gold_answer_sentence is not None:
                    if answer_sentences[sentence_ind] == gold_answer_sentence:
                        feature_file.write("2")
                    else:
                        feature_file.write("1")
                else:
                    feature_file.write("0")
                feature_file.write(f" qid:{query_id}")
                for feature_id, feature in enumerate(feature_line):
                    feature_text = str(feature)
                    feature_file.write(f" {feature_id + 1}:{feature_text}")
                feature_file.write("\n")


def train_model(train_feature_file_path):
    command = config.SVM_RANK_TRAIN_PATH + " -c " + str(
        config.SVM_C) + " " + train_feature_file_path + " " + config.SVM_MODEL_PATH
    print(command)
    os.system(command)


def eval_model(feature_file_path, model_path, predict_file_path):
    command = config.SVM_RANK_CLASSIFY_PATH + " " + feature_file_path + " " + model_path + " " + \
              predict_file_path
    os.system(command)


def get_selected_result(predict_file_path, related_passages_ids, questions, handled_passages_dict):
    with open(predict_file_path, "r", encoding="UTF-8") as predict_file:
        answered_questions = []
        for related_passages_id_tops, question in zip(related_passages_ids, questions):
            answer_sentences = []
            for related_passages_id in related_passages_id_tops:
                passage = handled_passages_dict[related_passages_id]
                answer_sentences.extend(passage.text)
            score = []
            for answer_sentence in answer_sentences:
                score.append(float(predict_file.readline()))
            answered_questions.append(question)
            answered_questions[-1]["answer_sentence"] = answer_sentences[np.argmax(score)]
    return answered_questions


def write_selected_result(selected_result_path, predicted_result_file_path, related_passages_ids, questions,
                          handled_passages_dict):
    with open(selected_result_path, "w", encoding="UTF-8") as selected_file:
        result_dicts = get_selected_result(predicted_result_file_path, related_passages_ids,
                                           questions, handled_passages_dict)
        json_lines = []
        for result_dict in result_dicts:
            json_lines.append(json.dumps(result_dict, ensure_ascii=False) + "\n")
        selected_file.writelines(json_lines)


def main():
    handled_passages_dict, invert_index = load_index_in_disk(config.HANDLED_PASSAGES_FILE_PATH, config.INDEX_FILE_PATH,
                                                             config.PASSAGES_CONFIG_PATH)
    train_questions, train_answers = read_train_dataset(train_file_path=config.QA_TRAIN_FILE_PATH)
    train_questions, dev_questions, train_answers, dev_answers = train_test_split(train_questions, train_answers,
                                                                                  test_size=0.10, shuffle=False,
                                                                                  random_state=0)
    train_related_passages_ids = []
    for answer in train_answers:
        train_related_passages_ids.append([answer["pid"]])
    generate_feature(config.QA_TRAIN_FEATURE_FILE_PATH, handled_passages_dict, train_questions,
                     train_related_passages_ids,
                     train_answers)

    dev_related_passages_ids = []
    # for answer in dev_answers:
    #     dev_related_passages_ids.append([answer["pid"]])
    dev_related_passages_ids = get_related_result(dev_questions, invert_index, handled_passages_dict)

    generate_feature(config.QA_DEV_FEATURE_FILE_PATH, handled_passages_dict, dev_questions,
                     dev_related_passages_ids,
                     dev_answers)

    train_model(config.QA_TRAIN_FEATURE_FILE_PATH)
    eval_model(config.QA_DEV_FEATURE_FILE_PATH, config.SVM_MODEL_PATH, config.QA_DEV_PREDICT_FILE_PATH)


if __name__ == '__main__':
    main()
