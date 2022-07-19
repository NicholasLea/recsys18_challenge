from utils import sentence
from utils.dataset import Dataset

train_playlists = 'playlists_training_validation.csv'
train_items = 'items_training_validation.csv'
test_playlists = 'playlists_test.csv'
test_items = 'items_test_x.csv'

dataset = Dataset('/Users/nicholas/Documents/Dataset/spotify_million_playlist_dataset')
# sentences = sentence.Iterator(dataset, train_playlists, train_items, sentence.Mode.ITEM)
# print('sentences', list(sentences))

for playlist in dataset.reader(train_playlists, train_items):
    print('playlist', playlist) #从这里可以看出，这里其实是对itemId用word2vec进行了学习
    # Convert IDs to strings
    # sentences = list(map(lambda x: str(x), playlist[sentence.Mode.ITEM.value]))
    # print('sentences', list(sentences))