import os
from keras import Sequential
from keras.models import Model
from keras.callbacks import ModelCheckpoint, TensorBoard
from keras.layers import LSTM, Embedding, Dense, TimeDistributed, GRU, concatenate, Input, RepeatVector
from preprocessor import load_data_with_title
from keras.utils import to_categorical

MODEL_FILE_NAME = 'model_title_based.h5'
CHECKPOINT_WEIGHTS_DIR = './2way_weights'
EPOCHS = 300
BATCH_SIZE = 8
DATA_SIZE = 100
RNN_CELL_TYPE = 'gru'
RNN_NETWORK_UNITS = 128
EMBEDDING_OUT_DIM = 10

(x_title, x_content, y_content), VOC = load_data_with_title(limit=DATA_SIZE)
VOC_SIZE = len(VOC)

print('training set information:')
print('vocabulary size:', VOC_SIZE)
print('X title shape:', x_title.shape)
print('X content shape:', x_content.shape)
print('Y content shape:', y_content.shape)
X_CONTENT_SHAPE = x_content.shape
X_TITLE_SHAPE = x_title.shape


def build_graph():
    rnn_cell_func = GRU
    if RNN_CELL_TYPE == 'lstm':
        rnn_cell_func = LSTM

    title_input = Input(name='title_input', dtype='int32', shape=(None,))
    content_input = Input(name='content_input', dtype='int32', shape=(None,))

    embedded_title = Embedding(VOC_SIZE, EMBEDDING_OUT_DIM)(title_input)
    dim_reduction_title = rnn_cell_func(EMBEDDING_OUT_DIM, return_sequences=False)(embedded_title)
    repeat_title = RepeatVector(X_CONTENT_SHAPE[1])(dim_reduction_title)

    embedded_content = Embedding(VOC_SIZE, EMBEDDING_OUT_DIM)(content_input)
    inputs = concatenate([repeat_title, embedded_content])

    output = rnn_cell_func(RNN_NETWORK_UNITS, return_sequences=True)(inputs)
    output = TimeDistributed(Dense(VOC_SIZE, activation='softmax'), name='td_output')(output)
    model = Model([title_input, content_input], [output])

    model.compile('rmsprop', 'categorical_crossentropy')
    return model


def train(model, x, y):
    # one-hot encode
    y = to_categorical(y, VOC_SIZE)

    try:
        if not os.path.exists(CHECKPOINT_WEIGHTS_DIR):
            os.mkdir(CHECKPOINT_WEIGHTS_DIR)

        # Keras callbacks
        checkpoint = ModelCheckpoint(CHECKPOINT_WEIGHTS_DIR + '/{epoch:d}.hdf5', save_weights_only=True, period=10)
        tensorboard = TensorBoard(batch_size=64)

        def fit_model(initial_epoch):
            nonlocal model

        epoch = 0
        try:
            print('try restoring ...')
            files = os.listdir(CHECKPOINT_WEIGHTS_DIR)
            if len(files) > 0:
                # latest check points
                latest_cp = max(map(lambda f: int(f.replace('.hdf5', '')), files))
                epoch = latest_cp
                print('from epoch:', epoch)
            model.load_weights(CHECKPOINT_WEIGHTS_DIR + '/{}.hdf5'.format(epoch))
        except OSError:
            print('weights not found, continuing start new training')
            pass

        model.fit(x, y, shuffle=True, batch_size=BATCH_SIZE, epochs=EPOCHS, initial_epoch=epoch,
                  callbacks=[checkpoint, tensorboard])

    except KeyboardInterrupt:
        print('')
        print('interrupted by user')
        pass


def run():
    model = build_graph()
    train(model, [x_title, x_content], y_content)
    model.save(MODEL_FILE_NAME)


if __name__ == '__main__':
    run()
