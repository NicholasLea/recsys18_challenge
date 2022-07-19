import argparse
import csv
import random
from os import path

random.seed(1)

parser = argparse.ArgumentParser(description="Split MPD")

# #原版
parser.add_argument('--path', default=None, required=True)
parser.add_argument('--input_playlists', default=None, required=True)
parser.add_argument('--input_items', default=None, required=True)
parser.add_argument('--output_playlists', default=None, required=True)
parser.add_argument('--output_items', default=None, required=True)
parser.add_argument('--output_playlists_split', default=None, required=True)
parser.add_argument('--output_playlists_split_pid', default=None, required=True)
parser.add_argument('--output_items_split', default=None, required=True)
parser.add_argument('--output_items_split_x', default=None, required=True)
parser.add_argument('--output_items_split_y', default=None, required=True)
parser.add_argument('--scale', type=int, required=True)

#Lk方便运行版
# 第一次拆分
# parser.add_argument('--path', default='D:/Dataset/spotify_million_playlist_dataset', required=False, type=str)
# parser.add_argument('--input_playlists', default='playlists.csv', required=False, type=str)
# parser.add_argument('--input_items', default='items.csv', required=False, type=str)
# parser.add_argument('--output_playlists', default='playlists_training_validation.csv', required=False, type=str)
# parser.add_argument('--output_items', default='items_training_validation.csv', required=False, type=str)
# parser.add_argument('--output_playlists_split', default='playlists_test.csv', required=False, type=str)
# parser.add_argument('--output_playlists_split_pid', default='playlists_test_pid.csv', required=False, type=str)
# parser.add_argument('--output_items_split', default='items_test.csv', required=False, type=str)
# parser.add_argument('--output_items_split_x', default='items_test_x.csv', required=False, type=str)
# parser.add_argument('--output_items_split_y', default='items_test_y.csv', required=False, type=str)
# parser.add_argument('--scale', type=int, required=False)

args = parser.parse_args()

items = {} #key:pid, value:所以此pid下的[pid, track在本列表中的jdx，track_uri]
tracks = {} #key:trackid, value:出现次数
playlists = {} #key:pid, value:pid完整信息
playlists_pid = [] #pid列表

print("Reading the playlists")
with open(path.join(args.path, args.input_playlists), 'r', newline='', encoding='utf8') as playlists_file:
    playlists_reader = csv.reader(playlists_file)

    for playlist in playlists_reader:
        pid = playlist[0]
        playlists[pid] = playlist
        playlists_pid.append(pid)

print("Reading the items")
# # 这个表里存了3个列，[pid, track在本列表中的jdx，track_uri]
with open(path.join(args.path, args.input_items), 'r', newline='', encoding='utf8') as items_file:
    items_reader = csv.reader(items_file)

    for idx, item in enumerate(items_reader):
        #方便观察进度
        if idx % 10000 == 0:
            print('idx:', idx)
        pid = item[0]
        track_uri = item[2]

        if track_uri in tracks:
            tracks[track_uri] += 1
        else:
            tracks[track_uri] = 1

        if pid in items:
            items[pid].append(item)
        else:
            items[pid] = [item]

print("Selecting split playlists randomly")
split_playlists = []
candidate_pid_list = list(playlists_pid)
random.shuffle(candidate_pid_list)

for candidate_pid in candidate_pid_list:
    candidate_tracks = tracks.copy()

    # Check that pid is not already in the split set
    if candidate_pid in split_playlists:
        continue

    # Load the candidate items
    candidate_items = items[candidate_pid]

    # Innocent until proven guilty
    good_candidate = True

    #！！！在colab上仔细测试了半天，我发现这段代码好像有问题。根据论文的含义，需要挑选各1%（10000个）给test和validation，并且由下面的代码
    #可以知道划分是在playlist级别上的，也就是整个playlist要么整个划分给train/val/test之一，不会分开。那么下面代码分为2部分，首先判断本次看的
    #playlist有没有哪个track是最后一次出现，如果是，则这个playslist就不被分到val/test里。比如track='beat it'在3个playlist出现过，但是本
    #次扫描的这个playlist里的beat it是第三个即最后一个。一旦出现一个这样的track，整个playlist就留在train里。我觉得这个设定没啥意义，有点太刻意
    #了。刻意让train里包含尽可能全的信息，不知道这样好不好....
    # 更大的问题再后面，作者设置每个if分支里的good_candidate为false，那么就是只有这10种同时不满足才可能被分出去，那么good_candidate应该
    # 是true才行。我在colab里验证了他是错的。其实我觉得他们弄的有点复杂了，不如直接选1000个好了。而且no title的好像是不存在的吧！所有的
    # playlists都有title啊！

    #！！！更新，他的代码好像没有问题！在训练集里是没有10个类别之分的，这里全部都有playlist title，也全部都有至少5个tracks。但是在challange
    #上有10个类别，所以需要在训练集模拟10个类别出来分别放到val\test里。那么做这个操作的前提就是这个列表的长度必须是足够长的，比如要模拟challange
    #里给出5个的那个类，必须类的长度要大于5。另外因为测试集里所有的track都在训练集里出现过，所以确保track都进入过train也是有意义的。
    # Check that pid does not contain unique tracks
    for item in candidate_items:
        track_uri = item[2]
        if candidate_tracks[track_uri] > 1:
            candidate_tracks[track_uri] -= 1
        else:
            good_candidate = False
            break

    # Challenge category
    validation_index = len(split_playlists)

    # Check the length of the playlist
    if validation_index < 1 * args.scale:
        # Only title
        if len(candidate_items) < 1:
            good_candidate = False
    elif validation_index < 2 * args.scale:
        # Title and first one
        if len(candidate_items) <= 1:
            good_candidate = False
    elif validation_index < 3 * args.scale:
        # Title and first five
        if len(candidate_items) <= 5:
            good_candidate = False
    elif validation_index < 4 * args.scale:
        # No title and first five
        if len(candidate_items) <= 5:
            good_candidate = False
    elif validation_index < 5 * args.scale:
        # Title and first ten
        if len(candidate_items) <= 10:
            good_candidate = False
    elif validation_index < 6 * args.scale:
        # No title and first ten
        if len(candidate_items) <= 10:
            good_candidate = False
    elif validation_index < 7 * args.scale:
        # Title and first twenty-five
        if len(candidate_items) <= 25:
            good_candidate = False
    elif validation_index < 8 * args.scale:
        # Title and random twenty-five
        if len(candidate_items) <= 25:
            good_candidate = False
    elif validation_index < 9 * args.scale:
        # Title and first a hundred
        if len(candidate_items) <= 100:
            good_candidate = False
    else:
        # Title and random a hundred
        if len(candidate_items) <= 100:
            good_candidate = False

    # Commit the changes
    if good_candidate is True:
        tracks = candidate_tracks
        split_playlists.append(candidate_pid)
        print("\tSplit set size is", len(split_playlists))

        # Check if we are done
        if len(split_playlists) >= args.scale * 10:
            break

# Saving the results
with open(path.join(args.path, args.output_playlists_split_pid), 'w', newline='', encoding='utf8') as pid_file:
    pid_writer = csv.writer(pid_file)
    for pid in split_playlists:
        pid_writer.writerow([pid])

output_playlists_file = open(path.join(args.path, args.output_playlists), 'w', newline='', encoding='utf8')
output_items_file = open(path.join(args.path, args.output_items), 'w', newline='', encoding='utf8')
output_playlists_split_file = open(path.join(args.path, args.output_playlists_split), 'w', newline='', encoding='utf8')
output_items_split_file = open(path.join(args.path, args.output_items_split), 'w', newline='', encoding='utf8')
output_items_split_x_file = open(path.join(args.path, args.output_items_split_x), 'w', newline='', encoding='utf8')
output_items_split_y_file = open(path.join(args.path, args.output_items_split_y), 'w', newline='', encoding='utf8')

output_playlists_writer = csv.writer(output_playlists_file)
output_items_writer = csv.writer(output_items_file)
output_playlists_split_writer = csv.writer(output_playlists_split_file)
output_items_split_writer = csv.writer(output_items_split_file)
output_items_split_x_writer = csv.writer(output_items_split_x_file)
output_items_split_y_writer = csv.writer(output_items_split_y_file)

for playlist in playlists.values():
    pid = playlist[0]

    # Original playlist
    if pid not in split_playlists:
        output_playlists_writer.writerow(playlist)

        for item in items[pid]:
            output_items_writer.writerow(item)

    # Split playlist
    else:
        # Challenge category
        validation_index = split_playlists.index(pid)

        if validation_index < 1 * args.scale:
            # Only title
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = []
            items_y = items[pid][:]
        elif validation_index < 2 * args.scale:
            # Title and first one
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = items[pid][:1]
            items_y = items[pid][1:]
        elif validation_index < 3 * args.scale:
            # Title and first five
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = items[pid][:5]
            items_y = items[pid][5:]
        elif validation_index < 4 * args.scale:
            # No title and first five
            playlist_name = None
            items_xy = items[pid][:]
            items_x = items[pid][:5]
            items_y = items[pid][5:]
        elif validation_index < 5 * args.scale:
            # Title and first ten
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = items[pid][:10]
            items_y = items[pid][10:]
        elif validation_index < 6 * args.scale:
            # No title and first ten
            playlist_name = None
            items_xy = items[pid][:]
            items_x = items[pid][:10]
            items_y = items[pid][10:]
        elif validation_index < 7 * args.scale:
            # Title and first twenty-five
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = items[pid][:25]
            items_y = items[pid][25:]
        elif validation_index < 8 * args.scale:
            # Title and random twenty-five
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            random.shuffle(items[pid])
            items_x = items[pid][:25]
            items_y = items[pid][25:]
        elif validation_index < 9 * args.scale:
            # Title and first a hundred
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            items_x = items[pid][:100]
            items_y = items[pid][100:]
        else:
            # Title and random a hundred
            playlist_name = playlist[1]
            items_xy = items[pid][:]
            random.shuffle(items[pid])
            items_x = items[pid][:100]
            items_y = items[pid][100:]

        # Sort tracks by position
        # 这里是排序，但是我觉得这个很不必要。对于y和x都包含一部分乱序的数据，从而让数据更真实的反应最后的结果比较好。所以我注释掉了这部分。
        # 并且我已经验证了在item.csv里，一个playslist里的数据都是有序的。除了这里专门shuffle的以外，所有处理后的数据也是有序的。
        # print('items_xy bef:',items_xy)
        # items_xy = sorted(items_xy, key=lambda row: int(row[1]))
        # items_x = sorted(items_x, key=lambda row: int(row[1]))
        # items_y = sorted(items_y, key=lambda row: int(row[1]))
        # print('items_xy aft:',items_xy)

        output_playlists_split_writer.writerow([pid, playlist_name,
                                                len(items_x), len(items_y),
                                                len(items_x + items_y)])

        for item in items_xy:
            # 我忽然有觉得把playlist_name带进去不是一个好事，存储文件太大，不利于后面别人复现
            output_items_split_writer.writerow(item)
            # output_items_split_writer.writerow([*item, playlist_name])

        for item in items_x:
            output_items_split_x_writer.writerow(item)
            # output_items_split_x_writer.writerow([*item, playlist_name])

        for item in items_y:
            output_items_split_y_writer.writerow(item)
            # output_items_split_y_writer.writerow([*item, playlist_name])
