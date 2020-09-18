import json

from pyltp import Segmentor
from pyltp import SentenceSplitter

import config
import segment


def get_page_id_and_content(target_page_file_path, source_page_file_path):
    with open(target_page_file_path, "w", encoding="utf-8") as preprocess_f:
        with open(source_page_file_path, "r", encoding="utf-8") as data_f:
            page_json_lines = data_f.readlines()
            for page_ind, page_json_line in enumerate(page_json_lines):
                result = json.loads(page_json_line)
                result.pop("url")
                result.pop("title")
                result.pop("file_name")
                sentences = segment.get_sentences(result["paragraphs"])
                result.pop("paragraphs")
                result["page_id"] = page_ind
                result["content"] = sentences
                preprocess_f.write(json.dumps(result, ensure_ascii=False) + "\n")


def main():
    get_page_id_and_content(target_page_file_path=config.PREPROCESSED_PAGE_JSON_FILE_PATH,
                            source_page_file_path=config.PAGE_JSON_FILE_PATH)


if __name__ == '__main__':
    main()
