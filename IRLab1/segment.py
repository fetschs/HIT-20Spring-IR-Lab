import json
import os

from pyltp import Segmentor
from pyltp import SentenceSplitter

LTP_MODEL_DIR_PATH = r"ltp_model"
MODEL_NAME = r"cws.model"
MODEL_PATH = os.path.join(LTP_MODEL_DIR_PATH, MODEL_NAME)
if not os.path.exists(LTP_MODEL_DIR_PATH):
    os.makedirs(LTP_MODEL_DIR_PATH)
    print("请将对应模型放置在对应路径： " + MODEL_PATH)

segment_or = Segmentor()
segment_or.load(MODEL_PATH)


def get_sentences(target_string):
    target_string = target_string.replace("\t", "")
    target_string = target_string.replace("\n", "")
    target_string = target_string.replace("\r", "")
    target_string = " ".join(target_string.split())
    target_string = SentenceSplitter.split(target_string)
    return list(target_string)


def delete_stop_word(target_words):
    ret_words = []
    for target_word in target_words:
        if target_word not in stop_words:
            ret_words.append(target_word)
    return ret_words


def wordSeg(target_sentence):
    words = segment_or.segment(target_sentence)
    words = delete_stop_word(words)
    return words


if __name__ == '__main__':
    with open("stopwords.txt", "r", encoding="utf-8") as stop_word_f:
        stop_words = stop_word_f.readlines()
        stop_words = set([stop_word.strip() for stop_word in stop_words])
    print(stop_words)
    with open("preprocessed.json", "w", encoding="utf-8") as preprocess_f:
        with open("data.json", "r", encoding="utf-8") as data_f:
            page_jsons = data_f.readlines()
            for ind in range(len(page_jsons)):
                result = json.loads(page_jsons[ind])
                titles = get_sentences(result["title"])
                result.pop("title")
                result["segmented_title"] = []
                for title in titles:
                    result["segmented_title"].extend(wordSeg(title))
                sentences = get_sentences(result["paragraphs"])
                result.pop("paragraphs")
                result["segmented_paragraphs"] = []
                for sentence in sentences:
                    result["segmented_paragraphs"].extend(wordSeg(sentence))
                temp_file_name = result["file_name"]
                result.pop("file_name")
                result["file_name"] = temp_file_name
                # only preprocess 10 pages
                if ind <= 9:
                    preprocess_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                else:
                    exit()
    segment_or.release()
