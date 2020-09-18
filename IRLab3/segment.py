import json

from pyltp import Segmentor
from pyltp import SentenceSplitter

import config

segment_or = Segmentor()
segment_or.load(config.LTP_CWS_MODEL_PATH)


def get_sentences(target_string):
    """
    remove some space char, split sentences.
    :param target_string: string will be split to sentences.
    :return: sentences.
    """
    target_string = target_string.replace("\t", "")
    target_string = target_string.replace("\n", "")
    target_string = target_string.replace("\r", "")
    target_string = " ".join(target_string.split())
    target_string = SentenceSplitter.split(target_string)
    return list(target_string)


def delete_stop_word(target_words):
    """
    delete stop words in the result of segment.
    :param target_words: the result of segment.
    :return: result of segment without stop words.
    """
    ret_words = []
    for target_word in target_words:
        if target_word not in config.STOP_WORDS:
            ret_words.append(target_word)
    return ret_words


def wordSeg(target_sentence, delete_stop_word_flag=False):
    """
    get tokens from word,by segment words from sentence.
    Args:
        target_sentence: target sentence will be handle.
        delete_stop_word_flag: whether delete punctuations.

    Returns:
        
    """
    words = segment_or.segment(target_sentence)
    if delete_stop_word_flag:
        words = delete_stop_word(words)
    return list(words)


def main():
    with open(config.PREPROCESSED_PAGE_JSON_FILE_PATH, "w", encoding="utf-8") as preprocess_f:
        with open(config.LTP_CWS_MODEL_PATH, "r", encoding="utf-8") as data_f:
            page_json_lines = data_f.readlines()
            for page_ind, page_json_line in enumerate(page_json_lines):
                result = json.loads(page_json_line)
                result.pop("url")
                result.pop("title")
                result.pop("file_name")
                sentences = get_sentences(result["paragraphs"])
                result.pop("paragraphs")
                result["page_id"] = page_ind
                result["content"] = []
                for sentence in sentences:
                    result["content"].extend(wordSeg(sentence))
                preprocess_f.write(json.dumps(result, ensure_ascii=False) + "\n")
    segment_or.release()


if __name__ == '__main__':
    main()
