from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from tqdm import tqdm

import config
import segment


def read_question_dataset_from_file(data_file_path, label_type):
    with open(data_file_path, "r", encoding="UTF-8") as data_file:
        seg_questions = []
        labels = []
        for question_line in tqdm(data_file.readlines()):
            question_tuple = question_line.strip().split("\t")
            question_label = question_tuple[0]
            question_word_list = segment.wordSeg(question_tuple[1], delete_stop_word_flag=False)
            seg_questions.append(" ".join(question_word_list))
            temp_label = question_label[0:question_label.find("_")] if label_type == "rough" else question_label
            labels.append(temp_label)
        return seg_questions, labels


def get_question_dataset(train_file_path, test_file_path, label_type):
    train_questions, train_labels = read_question_dataset_from_file(data_file_path=train_file_path,
                                                                    label_type=label_type)
    test_questions, test_labels = read_question_dataset_from_file(data_file_path=test_file_path,
                                                                  label_type=label_type)
    return train_questions, train_labels, test_questions, test_labels


def classification_by_LR(train_inputs, train_labels, test_inputs, test_labels, label_type):
    parameters = [
        {
            "C": range(200, 220, 20)
        }]
    lr_classifier = LogisticRegression(solver="newton-cg", multi_class="multinomial", n_jobs=-1, max_iter=500)
    grid_search_result = GridSearchCV(lr_classifier, parameters, scoring="accuracy", cv=10, n_jobs=-1)
    grid_search_result.fit(train_inputs, train_labels)
    best_classifier = grid_search_result.best_estimator_
    print("%f  with:   %r" % (grid_search_result.best_score_, grid_search_result.best_params_))
    print("test dataset acc: {}".format(best_classifier.score(test_inputs, test_labels)))
    joblib.dump(best_classifier, "best_LR_" + label_type + ".model")


def load_best_model(label_type):
    train_questions, train_labels, test_questions, test_labels = get_question_dataset(
        train_file_path=config.QUESTION_CLASSIFICATION_TRAIN_FILE_PATH,
        test_file_path=config.QUESTION_CLASSIFICATION_TEST_FILE_PATH, label_type=label_type)
    tf_idf_vector = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    train_tf_idf_features = tf_idf_vector.fit_transform(train_questions)
    return train_tf_idf_features, joblib.load("best_LR_" + label_type + ".model")


def main():
    # label_type = "fine"
    # train_questions, train_labels, test_questions, test_labels = get_question_dataset(
    #     train_file_path=config.QUESTION_CLASSIFICATION_TRAIN_FILE_PATH,
    #     test_file_path=config.QUESTION_CLASSIFICATION_TEST_FILE_PATH, label_type=label_type)
    # tf_idf_vector = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    # tf_idf_vector.fit(train_questions)
    # joblib.dump(tf_idf_vector, config.QUESTION_CLASSIFICATION_TF_IDF_FILE_PATH)
    # train_tf_idf_features = tf_idf_vector.transform(train_questions)
    # test_tf_idf_features = tf_idf_vector.transform(test_questions)
    # classification_by_LR(train_tf_idf_features, train_labels, test_tf_idf_features, test_labels, label_type=label_type)

    label_type = "rough"
    train_questions, train_labels, test_questions, test_labels = get_question_dataset(
        train_file_path=config.QUESTION_CLASSIFICATION_TRAIN_FILE_PATH,
        test_file_path=config.QUESTION_CLASSIFICATION_TEST_FILE_PATH, label_type=label_type)
    tf_idf_vector = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    tf_idf_vector.fit(train_questions)
    joblib.dump(tf_idf_vector, config.QUESTION_CLASSIFICATION_TF_IDF_FILE_PATH)
    train_tf_idf_features = tf_idf_vector.transform(train_questions)
    test_tf_idf_features = tf_idf_vector.transform(test_questions)
    classification_by_LR(train_tf_idf_features, train_labels, test_tf_idf_features, test_labels, label_type=label_type)


if __name__ == '__main__':
    main()
