import os

PASSAGES_FILE_PATH = r"data\passages_multi_sentences.json"
INDEX_FILE_PATH = r"data\interval_index.pkl"
HANDLED_PASSAGES_FILE_PATH = r"data\handled_passages.pkl"
PASSAGES_CONFIG_PATH = r"data\passages_config.pkl"

QA_TRAIN_FILE_PATH = r"data\train.json"
QA_TRAIN_FEATURE_FILE_PATH = r"data\train_feature.dat"
QA_TRAIN_PREDICT_FILE_PATH = r"data\train_predict.dat"
QA_TRAIN_SELECTED_FILE_PATH = r"data\train_selected.dat"  # 中间结果 实际不使用

QA_TEST_FILE_PATH = r"data\new_test.json"
QA_TEST_FEATURE_FILE_PATH = r"data\test_feature.dat"
QA_TEST_PREDICT_FILE_PATH = r"data\test_predict.dat"
QA_TEST_SELECTED_FILE_PATH = r"data\test_selected.json"
QA_TEST_FINAL_FILE_PATH = r"data\test_answers.json"

QA_DEV_FEATURE_FILE_PATH = r"data\dev_feature.dat"
QA_DEV_PREDICT_FILE_PATH = r"data\dev_predict.dat"
QA_DEV_SELECTED_FILE_PATH = r"data\dev_selected.json"
QA_DEV_FINAL_FILE_PATH = r"data\dev_answers.json"

QUESTION_CLASSIFICATION_TRAIN_FILE_PATH = r"question_classification\trian_questions.txt"
QUESTION_CLASSIFICATION_TEST_FILE_PATH = r"question_classification\test_questions.txt"
QUESTION_CLASSIFICATION_TF_IDF_FILE_PATH = r"question_classification\tf_idf_vector.pkl"

SVM_MODEL_PATH = r"svm_rank\svm_model.dat"
SVM_RANK_TRAIN_PATH = r"svm_rank\svm_rank_learn.exe"
SVM_RANK_CLASSIFY_PATH = r"svm_rank\svm_rank_classify.exe"
LTP_MODEL_DIR_PATH = r"ltp_model"
LTP_CWS_MODEL_NAME = r"cws.model"
LTP_POS_MODEL_NAME = r"pos.model"
LTP_NER_MODEL_NAME = r"ner.model"

LTP_CWS_MODEL_PATH = os.path.join(LTP_MODEL_DIR_PATH, LTP_CWS_MODEL_NAME)
LTP_POS_MODEL_PATH = os.path.join(LTP_MODEL_DIR_PATH, LTP_POS_MODEL_NAME)
LTP_NER_MODEL_PATH = os.path.join(LTP_MODEL_DIR_PATH, LTP_NER_MODEL_NAME)
if not os.path.exists(LTP_MODEL_DIR_PATH):
    os.makedirs(LTP_MODEL_DIR_PATH)
    print("pleas put the ltp model to： " + LTP_CWS_MODEL_PATH)
STOP_WORDS_PATH = "stopwords.txt"
with open(STOP_WORDS_PATH, "r", encoding="utf-8") as stop_word_f:
    STOP_WORDS = stop_word_f.readlines()
    STOP_WORDS = set([stop_word.strip() for stop_word in STOP_WORDS])

BM_K1 = 0.005
BM_K3 = 1.5
BM_B = 0.2
BEST_LR_C = 200
SVM_C = 5
