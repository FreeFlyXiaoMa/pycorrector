# -*- coding: utf-8 -*-
"""
@author:XuMing（xuming624@qq.com)
@description: network configuration
"""
import os

pwd_path = os.path.abspath(os.path.dirname(__file__))

# Training data path.
# chinese corpus
raw_train_paths = [
    os.path.join(pwd_path, '../data/cn/CGED/CGED18_HSK_TrainingSet.xml'),
    os.path.join(pwd_path, '../data/cn/CGED/CGED17_HSK_TrainingSet.xml'),
    os.path.join(pwd_path, '../data/cn/CGED/CGED16_HSK_TrainingSet.xml'),
    # os.path.join(pwd_path, '../data/cn/CGED/sample_HSK_TrainingSet.xml'),
]

output_dir = os.path.join(pwd_path, 'output')

train_path = os.path.join(output_dir, 'train.txt')
# Validation data path.
test_path = os.path.join(output_dir, 'test.txt')

emb_path = os.path.join(output_dir, 'emb.vec')
model_path = os.path.join(output_dir, 'model')

# nets
word_embed_size = 200
hidden_size = 200
n_layers = 1
use_mlp = True
dropout = 0.0

# train
maxlen = 400
epochs = 30
batch_size = 128
min_freq = 10
ns_power = 0.75
learning_rate = 1e-3
gpu_id = 0

# evaluate with mscc data set
question_file = 'YOUR_DATASET_DIR/Holmes.machine_format.questions.txt'
answer_file = 'YOUR_DATASET_DIR/Holmes.machine_format.answers.txt'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
