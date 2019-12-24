# -*- coding: utf-8 -*-
# @Time     :2019/12/18 10:11
# @Author   :XiaoMa
# @File     :test.py
import pycorrector
corrected_sent,detail=pycorrector.correct('少先队员因该为老人让坐')
print(corrected_sent,detail)