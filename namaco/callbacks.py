"""
Custom callbacks.
"""
import os

import numpy as np
from keras.callbacks import Callback, TensorBoard, EarlyStopping, ModelCheckpoint
from seqeval.metrics import f1_score, classification_report


def get_callbacks(log_dir=None, valid=(), checkpoint_dir=None, early_stopping=True):
    """Get callbacks.
    Args:
        log_dir (str): the destination to save logs(for TensorBoard).
        valid (tuple): data for validation.
        checkpoint_dir (bool): Whether to use checkpoint.
        early_stopping (bool): whether to use early stopping.
    Returns:
        list: list of callbacks
    """
    callbacks = []

    if log_dir:
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
            print('Successfully made a directory: {}'.format(log_dir))
        callbacks.append(TensorBoard(log_dir))

    if valid:
        callbacks.append(F1score(*valid))

    if checkpoint_dir:
        if not os.path.exists(checkpoint_dir):
            os.mkdir(checkpoint_dir)
            print('Successfully made a directory: {}'.format(checkpoint_dir))

        file_name = '_'.join(['model_weights', '{epoch:02d}', '{f1:2.2f}']) + '.h5'
        save_callback = ModelCheckpoint(os.path.join(checkpoint_dir, file_name),
                                        monitor='f1', save_weights_only=True)
        callbacks.append(save_callback)

    if early_stopping:
        callbacks.append(EarlyStopping(monitor='f1', patience=3, mode='max'))

    return callbacks


class F1score(Callback):

    def __init__(self, valid_steps, valid_batches, preprocessor=None):
        super(F1score, self).__init__()
        self.valid_steps = valid_steps
        self.valid_batches = valid_batches
        self.p = preprocessor

    def on_epoch_end(self, epoch, logs={}):
        label_true = []
        label_pred = []
        for i in range(self.valid_steps):
            x_true, y_true = next(self.valid_batches)
            y_true = np.argmax(y_true, -1)
            sequence_lengths = x_true[-1]  # shape of (batch_size, 1)
            sequence_lengths = np.reshape(sequence_lengths, (-1,))
            y_pred = self.model.predict_on_batch(x_true)
            y_pred = np.argmax(y_pred, -1)

            y_true = self.p(y_true)
            y_pred = self.p(y_pred)

            label_true.extend(y_true)
            label_pred.extend(y_pred)

        score = f1_score(label_true, label_pred)
        print(' - f1: {:04.2f}'.format(score * 100))
        print(classification_report(label_true, label_pred))
        logs['f1'] = score
