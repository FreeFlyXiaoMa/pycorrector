# -*- coding: utf-8 -*-
# Author: XuMing <xuming624@qq.com>
# Brief: corrector with spell and stroke
import codecs
import operator
import os
import time

from pypinyin import lazy_pinyin

from pycorrector import config
from pycorrector.detector import Detector, ErrorType
from pycorrector.utils.logger import logger
from pycorrector.utils.math_utils import edit_distance_word
from pycorrector.utils.text_utils import is_chinese_string


class Corrector(Detector):
    def __init__(self, common_char_path=config.common_char_path,
                 same_pinyin_path=config.same_pinyin_path,
                 same_stroke_path=config.same_stroke_path,
                 language_model_path=config.language_model_path,
                 word_freq_path=config.word_freq_path,
                 custom_word_freq_path=config.custom_word_freq_path,
                 custom_confusion_path=config.custom_confusion_path,
                 person_name_path=config.person_name_path,
                 place_name_path=config.place_name_path,
                 stopwords_path=config.stopwords_path):
        super(Corrector, self).__init__(language_model_path=language_model_path,
                                        word_freq_path=word_freq_path,
                                        custom_word_freq_path=custom_word_freq_path,
                                        custom_confusion_path=custom_confusion_path,
                                        person_name_path=person_name_path,
                                        place_name_path=place_name_path,
                                        stopwords_path=stopwords_path)
        self.name = 'corrector'
        self.common_char_path = common_char_path
        self.same_pinyin_text_path = same_pinyin_path
        self.same_stroke_text_path = same_stroke_path
        self.initialized_corrector = False
        self.cn_char_set = None
        self.same_pinyin = None
        self.same_stroke = None

    @staticmethod
    def load_char_set(path):
        words = set()
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for w in f:
                words.add(w.strip())
        return words

    @staticmethod
    def load_same_pinyin(path, sep='\t'):
        """
        加载同音字
        :param path:
        :param sep:
        :return:
        """
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists:" + path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 2:
                    key_char = parts[0]
                    same_pron_same_tone = set(list(parts[1]))
                    same_pron_diff_tone = set(list(parts[2]))
                    value = same_pron_same_tone.union(same_pron_diff_tone)
                    if len(key_char) > 1 or not value:
                        continue
                    result[key_char] = value
        return result

    @staticmethod
    def load_same_stroke(path, sep='\t'):
        """
        加载形似字
        :param path:
        :param sep:
        :return:
        """
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists:" + path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 1:
                    for i, c in enumerate(parts):
                        result[c] = set(list(parts[:i] + parts[i + 1:]))
        return result

    def initialize_corrector(self):
        t1 = time.time()
        # chinese common char dict
        self.cn_char_set = self.load_char_set(self.common_char_path)

        # same pinyin
        self.same_pinyin = self.load_same_pinyin(self.same_pinyin_text_path)
        t2 = time.time()
        logger.debug("Loaded same pinyin file: %s, spend: %.3f s." % (
            self.same_pinyin_text_path, t2 - t1))

        # same stroke
        self.same_stroke = self.load_same_stroke(self.same_stroke_text_path)
        logger.debug("Loaded same stroke file: %s, spend: %.3f s." % (
            self.same_stroke_text_path, time.time() - t2))
        self.initialized_corrector = True

    def check_corrector_initialized(self):
        if not self.initialized_corrector:
            self.initialize_corrector()

    def get_same_pinyin(self, char):
        """
        取同音字
        :param char:
        :return:
        """
        self.check_corrector_initialized()
        return self.same_pinyin.get(char, set())

    def get_same_stroke(self, char):
        """
        取形似字
        :param char:
        :return:
        """
        self.check_corrector_initialized()
        return self.same_stroke.get(char, set())

    def known(self, words):
        """
        取得词序列中属于常用词部分
        :param words:
        :return:
        """
        return set(word for word in words if word in self.word_freq)

    def _confusion_char_set(self, c):
        return self.get_same_pinyin(c).union(self.get_same_stroke(c))

    def _confusion_word_set(self, word):
        confusion_word_set = set()
        candidate_words = list(self.known(edit_distance_word(word, self.cn_char_set)))
        for candidate_word in candidate_words:
            if lazy_pinyin(candidate_word) == lazy_pinyin(word):
                # same pinyin
                confusion_word_set.add(candidate_word)
        return confusion_word_set

    def _confusion_custom_set(self, word):
        confusion_word_set = set()
        if word in self.custom_confusion:
            confusion_word_set = {self.custom_confusion[word]}
        return confusion_word_set

    # TODO: need more faster
    def generate_items(self, word, fraction=1):
        """
        生成纠错候选集
        :param word:
        :param fraction:
        :return:
        """
        candidates_1_order = []
        candidates_2_order = []
        candidates_3_order = []
        # same pinyin word
        candidates_1_order.extend(self._confusion_word_set(word))
        # custom confusion word
        candidates_1_order.extend(self._confusion_custom_set(word))
        # same pinyin char
        if len(word) == 1:
            # same one char pinyin
            confusion = [i for i in self._confusion_char_set(word[0]) if i]
            candidates_1_order.extend(confusion)
        if len(word) == 2:
            # same first char pinyin
            confusion = [i + word[1:] for i in self._confusion_char_set(word[0]) if i]
            candidates_2_order.extend(confusion)
            # same last char pinyin
            confusion = [word[:-1] + i for i in self._confusion_char_set(word[-1]) if i]
            candidates_2_order.extend(confusion)
        if len(word) > 2:
            # same mid char pinyin
            confusion = [word[0] + i + word[2:] for i in self._confusion_char_set(word[1])]
            candidates_3_order.extend(confusion)

            # same first word pinyin
            confusion_word = [i + word[-1] for i in self._confusion_word_set(word[:-1])]
            candidates_3_order.extend(confusion_word)

            # same last word pinyin
            confusion_word = [word[0] + i for i in self._confusion_word_set(word[1:])]
            candidates_3_order.extend(confusion_word)

        # add all confusion word list
        confusion_word_set = set(candidates_1_order + candidates_2_order + candidates_3_order)
        confusion_word_list = [item for item in confusion_word_set if is_chinese_string(item)]
        confusion_sorted = sorted(confusion_word_list, key=lambda k: self.word_frequency(k), reverse=True)
        return confusion_sorted[:len(confusion_word_list) // fraction + 1]

    def get_lm_correct_item(self, cur_item, candidates, before_sent, after_sent, n=5, threshold=50):
        """
        通过语言模型纠正字词错误
        """
        result = cur_item
        if cur_item not in candidates:
            candidates.append(cur_item)

        ppl_scores = {i: self.ppl_score(list(before_sent + i + after_sent)) for i in candidates}
        sorted_ppl_scores = sorted(ppl_scores.items(), key=lambda d: d[1])

        # 增加正确字词的修正范围，减少误纠
        top_items = []
        top_score = 0.0
        for i, v in enumerate(sorted_ppl_scores):
            v_word = v[0]
            v_score = v[1]
            if i == 0:
                top_score = v_score
                top_items.append(v_word)
            elif i < n and v_score < top_score + threshold:
                top_items.append(v_word)
            else:
                break
        if cur_item not in top_items:
            result = top_items[0]
        return result

    def correct(self, sentence):
        """
        句子改错
        :param sentence: 句子文本
        :return: 改正后的句子, list(wrong, right, begin_idx, end_idx)
        """
        detail = []
        self.check_corrector_initialized()
        maybe_errors = self.detect(sentence)
        # 顺序处理
        maybe_errors = sorted(maybe_errors, key=operator.itemgetter(2), reverse=False)
        for cur_item, begin_idx, end_idx, err_type in maybe_errors:
            # 纠错，逐个处理
            before_sent = sentence[:begin_idx]
            after_sent = sentence[end_idx:]

            # 困惑集中指定的词，直接取结果
            if err_type == ErrorType.confusion:
                corrected_item = self.custom_confusion[cur_item]
            else:
                # 对非中文的错字不做处理
                if not is_chinese_string(cur_item):
                    continue
                # 取得所有可能正确的词
                candidates = self.generate_items(cur_item)
                if not candidates:
                    continue
                corrected_item = self.get_lm_correct_item(cur_item, candidates, before_sent, after_sent,
                                                          n=5, threshold=50)
            # output
            if corrected_item != cur_item:
                sentence = before_sent + corrected_item + after_sent
                detail_word = [cur_item, corrected_item, begin_idx, end_idx]
                detail.append(detail_word)
        detail = sorted(detail, key=operator.itemgetter(2))
        return sentence, detail
