import json

from pyltp import NamedEntityRecognizer
from pyltp import Postagger
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split

import config
import segment
from answer_sentence_selection import generate_feature, eval_model, get_selected_result
from metric import cal_bleu
from preprocessed import load_index_in_disk, read_train_dataset, read_test_dataset, get_related_result


def rules(questions, answer_sentences, gold_answers=None):
    question_classification_model = joblib.load("best_LR_rough.model")
    pos_tagger = Postagger()
    pos_tagger.load(config.LTP_POS_MODEL_PATH)
    recongnizer = NamedEntityRecognizer()
    recongnizer.load(config.LTP_NER_MODEL_PATH)
    tf_idf_vector = joblib.load(config.QUESTION_CLASSIFICATION_TF_IDF_FILE_PATH)
    bleu_average = 0.0
    final_answers = []
    for gold_answer_ind, (question, answer_sentence) in enumerate(zip(questions, answer_sentences)):
        query_text = question["question"]
        query_words = segment.wordSeg(query_text, delete_stop_word_flag=False)
        answer_words = segment.wordSeg(answer_sentence, delete_stop_word_flag=True)
        query_class_predict = question_classification_model.predict(tf_idf_vector.transform([" ".join(query_words)]))[0]
        answer_words_pos = list(pos_tagger.postag(answer_words))
        answer_words_ner = list(recongnizer.recognize(answer_words, answer_words_pos))
        final_answer = ""
        for answer_word, answer_word_ner, answer_word_pos in zip(answer_words, answer_words_ner, answer_words_pos):
            if query_class_predict == "HUM":
                if answer_word_ner.find("-Nh") != -1:
                    final_answer += answer_word
            elif query_class_predict == "LOC":
                if answer_word_ner.find("-Ns") != -1:
                    final_answer += answer_word
            elif query_class_predict == "NUM":
                if answer_word_pos == "m":
                    final_answer += answer_word
            elif query_class_predict == "TIME":
                if answer_word_pos == "nt":
                    final_answer += answer_word
            elif query_class_predict == "OBJ":
                if answer_word_pos.find("n") != -1 and answer_word_ner.find("-Nh") == -1 and answer_word_ner.find(
                        "-Ns") == -1:
                    final_answer += answer_word
            if answer_word_pos.find("ws") != -1:
                final_answer += answer_word
        if answer_sentence.count(":") == 1:
            final_answer = answer_sentence[answer_sentence.find(":") + 1:]

        # basic rules
        if len(final_answer) == 0:
            for answer_word, answer_word_ner, answer_word_pos in zip(answer_words, answer_words_ner, answer_words_pos):
                if answer_word_pos.find("n") != -1:
                    final_answer = final_answer + answer_word
        # special rule 1
        if len(final_answer) == 0:
            final_answer = answer_sentence
        # no solution ,just use the sentence
        if gold_answers is not None:
            now_bleu = cal_bleu(final_answer, gold_answers[gold_answer_ind])
            bleu_average = bleu_average + now_bleu
        final_answers.append(final_answer)

    if gold_answers is not None:
        print(bleu_average / len(questions))

    return final_answers


def write_final_submit(final_result_file_path, questions, related_passage_ids, final_answers):
    with open(final_result_file_path, "w", encoding="UTF-8") as final_result_file:
        for question, related_passage_id, final_answer in zip(questions, related_passage_ids,
                                                              final_answers):
            json_dict = {
                "qid": question["qid"],
                "question": question["question"],
                "answer_pid": related_passage_id,
                "answer": final_answer
            }
            final_result_file.write(json.dumps(json_dict, ensure_ascii=False) + "\n")


def main():
    handled_passages_dict, invert_index = load_index_in_disk(config.HANDLED_PASSAGES_FILE_PATH, config.INDEX_FILE_PATH,
                                                             config.PASSAGES_CONFIG_PATH)
    train_questions, train_answers = read_train_dataset(train_file_path=config.QA_TRAIN_FILE_PATH)
    train_questions, dev_questions, train_answers, dev_answers = train_test_split(train_questions, train_answers,
                                                                                  test_size=0.10, shuffle=False,
                                                                                  random_state=0)
    dev_gold_related_passages_ids = []
    dev_gold_final_answers = []
    dev_gold_answer_sentences = []
    for answer in dev_answers:
        dev_gold_related_passages_ids.append(answer["pid"])
        dev_gold_answer_sentences.append(answer["answer_sentence"][0])
        dev_gold_final_answers.append(answer["answer"])

    # use pipeline for eval
    # eval_model(config.QA_DEV_FEATURE_FILE_PATH, config.SVM_MODEL_PATH, config.QA_DEV_PREDICT_FILE_PATH)
    # dev_related_passages_ids = get_related_result(dev_questions, invert_index, handled_passages_dict)
    # dev_selected_results = get_selected_result(config.QA_DEV_PREDICT_FILE_PATH, dev_gold_related_passages_ids,
    #                                            dev_questions,
    #                                            handled_passages_dict)
    # dev_answer_sentences = []
    # for selected_result in dev_selected_results:
    #     dev_answer_sentences.append(selected_result["answer_sentence"])

    # # use gold pipeline for eval
    # dev_final_answers = rules(dev_questions, dev_gold_answer_sentences, dev_gold_final_answers)
    #
    # write_final_submit(config.QA_DEV_FINAL_FILE_PATH, dev_questions, dev_gold_related_passages_ids, dev_final_answers)

    test_questions = read_test_dataset(config.QA_TEST_FILE_PATH)
    test_related_passage_ids = get_related_result(test_questions, invert_index, handled_passages_dict)
    generate_feature(config.QA_TEST_FEATURE_FILE_PATH, handled_passages_dict, test_questions,
                     test_related_passage_ids, None)
    eval_model(config.QA_TEST_FEATURE_FILE_PATH, config.SVM_MODEL_PATH, config.QA_TEST_PREDICT_FILE_PATH)
    test_selected_results = get_selected_result(config.QA_TEST_PREDICT_FILE_PATH, test_related_passage_ids,
                                                test_questions,
                                                handled_passages_dict)
    test_answer_sentences = []
    for test_selected_result in test_selected_results:
        test_answer_sentences.append(test_selected_result["answer_sentence"])
    test_final_answers = rules(test_questions, test_answer_sentences, None)
    write_final_submit(config.QA_TEST_FINAL_FILE_PATH, test_questions, test_related_passage_ids, test_final_answers)


if __name__ == '__main__':
    main()
