"""
Training example.
"""
import argparse
import os

import numpy as np
from gensim.models.keyedvectors import KeyedVectors
from sklearn.model_selection import train_test_split

from namaco.utils import load_data_and_labels
from namaco.trainer import Trainer
from namaco.models import CharModel
from namaco.preprocess import StaticPreprocessor, DynamicPreprocessor


def filter_embeddings(embeddings, vocab, dim):
    """Loads word vectors in numpy array.

    Args:
        embeddings (dict): a dictionary of numpy array.
        vocab (dict): word_index lookup table.

    Returns:
        numpy array: an array of word embeddings.
    """
    _embeddings = np.zeros([len(vocab), dim])
    for word in vocab:
        if word in embeddings:
            word_idx = vocab[word]
            _embeddings[word_idx] = embeddings[word]

    return _embeddings


def main(args):
    print('Loading datasets...')
    X, y = load_data_and_labels(args.data_path)
    x_train, x_valid, y_train, y_valid = train_test_split(X, y, test_size=0.1, random_state=42)
    embeddings = KeyedVectors.load(args.embedding_path).wv

    print('Transforming datasets...')
    p = StaticPreprocessor()
    p.fit(X, y)
    x_train, y_train = p.transform(x_train, y_train)
    x_valid, y_valid = p.transform(x_valid, y_valid)
    dp = DynamicPreprocessor(n_labels=len(p.label_dic))
    embeddings = filter_embeddings(embeddings, p.word_dic, embeddings.vector_size)

    print('Building a model...')
    model = CharModel(char_vocab_size=len(p.char_dic),
                      word_vocab_size=len(p.word_dic),
                      pos_vocab_size=len(p.pos_dic),
                      ntags=len(p.label_dic),
                      embeddings=embeddings)
    model.build()

    print('Training the model...')
    trainer = Trainer(model, preprocessor=dp, inverse_transform=p.inverse_transform,
                      log_dir=args.log_dir, checkpoint_path=args.save_dir)
    trainer.train(x_train, y_train, x_valid, y_valid)

    print('Saving the model...')
    model.save(args.weights_file, args.params_file)
    p.save(args.preprocessor_file)


if __name__ == '__main__':
    DATA_DIR = os.path.join(os.path.dirname(__file__), '../tests/data')
    SAVE_DIR = os.path.join(os.path.dirname(__file__), 'models')
    parser = argparse.ArgumentParser(description='Training a model')
    parser.add_argument('--data_path', default=os.path.join(DATA_DIR, 'datasets.tsv'))
    parser.add_argument('--embedding_path', default=os.path.join(DATA_DIR, 'jawiki-embeddings-neologd/wiki.ja.neologd.word2vec.model'))
    parser.add_argument('--log_dir', default=os.path.join(os.path.dirname(__file__), 'logs'))
    parser.add_argument('--save_dir', default=SAVE_DIR)
    parser.add_argument('--weights_file', default=os.path.join(SAVE_DIR, 'model_weights.h5'))
    parser.add_argument('--params_file', default=os.path.join(SAVE_DIR, 'params.json'))
    parser.add_argument('--preprocessor_file', default=os.path.join(SAVE_DIR, 'preprocessor.json'))
    args = parser.parse_args()
    main(args)
