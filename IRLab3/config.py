import os

PAGE_JSON_FILE_PATH = "data/page.json"
PREPROCESSED_PAGE_JSON_FILE_PATH = "data/preprocessed_page.json"
DOC_DIR_PATH = r"data\documents"
INDEX_FILE_PATH = r"data\interval_index.pkl"
HANDLED_PASSAGES_FILE_PATH = r"data\handled_passages.pkl"
PASSAGES_CONFIG_PATH = r"data\passages_config.pkl"

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