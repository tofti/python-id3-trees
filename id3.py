import csv
import sys
import math


def load_csv_to_header_data(filename):
    fs = csv.reader(open(filename))
    all_row = []
    for r in fs:
        all_row.append(r)

    headers = all_row[0]
    idx_to_name, name_to_idx = get_header_name_to_idx_maps(headers)

    data = {
        'header': headers,
        'rows': all_row[1:],
        'name_to_idx': name_to_idx,
        'idx_to_name': idx_to_name
    }
    return data


def get_header_name_to_idx_maps(headers):
    name_to_idx = {}
    idx_to_name = {}
    for i in range(0, len(headers)):
        name_to_idx[headers[i]] = i
        idx_to_name[i] = headers[i]
    return idx_to_name, name_to_idx


def project_columns(data, columns_to_project):
    data_h = list(data['header'])
    data_r = list(data['rows'])

    all_cols = list(range(0, len(data_h)))

    columns_to_project_ix = [data['name_to_idx'][name] for name in columns_to_project]
    columns_to_remove = [cidx for cidx in all_cols if cidx not in columns_to_project_ix]

    for delc in sorted(columns_to_remove, reverse=True):
        del data_h[delc]
        for r in data_r:
            del r[delc]

    idx_to_name, name_to_idx = get_header_name_to_idx_maps(data_h)

    return {'header': data_h, 'rows': data_r,
            'name_to_idx': name_to_idx,
            'idx_to_name': idx_to_name}


def transform_data(data, col_name, functor):
    col_idx = data['name_to_idx'][col_name]
    data_rows = data['rows']
    for row in data_rows:
        row[col_idx] = functor(row[col_idx])


def val_mapper_creator(map):
    def val_mapper(x):
        if x in map:
            return map[x]
        else:
            return None

    return val_mapper


def val_mapper_with_default_creator(val_map, default):
    val_mapper = val_mapper_creator(val_map)

    def val_mapper_with_default(x):
        y = val_mapper(x)
        if y is None:
            return default
        return y

    return val_mapper_with_default


def get_class_labels(data, target_attribute):
    rows = data['rows']
    col_idx = data['name_to_idx'][target_attribute]
    labels = {}
    for r in rows:
        val = r[col_idx]
        if val in labels:
            labels[val] = labels[val] + 1
        else:
            labels[val] = 1
    return labels


def entropy(n, labels):
    ent = 0
    for label in labels.keys():
        p_x = labels[label] / n
        ent += - p_x * math.log(p_x, 2)
    return ent


def partition_data(data, group_att):
    partitions = {}
    data_rows = data['rows']
    group_att_idx = data['name_to_idx'][group_att]
    for row in data_rows:
        row_val = row[group_att_idx]
        if row_val not in partitions.keys():
            partitions[row_val] = {
                'name_to_idx': data['name_to_idx'],
                'idx_to_name': data['idx_to_name'],
                'rows': list()
            }
        partitions[row_val]['rows'].append(row)
    return partitions


def avg_entropy_w_partitions(data, splitting_att, target_attribute):
    # find uniq values of splitting att
    data_rows = data['rows']
    n = len(data_rows)
    partitions = partition_data(data, splitting_att)

    avg_ent = 0

    for partition_key in partitions.keys():
        partitioned_data = partitions[partition_key]
        partition_n = len(partitioned_data['rows'])
        partition_labels = get_class_labels(partitioned_data, target_attribute)
        partition_entropy = entropy(partition_n, partition_labels)
        avg_ent += partition_n / n * partition_entropy

    return avg_ent, partitions


def id3(data, remaining_atts, target_attribute):
    labels = get_class_labels(data, target_attribute)

    node = {}

    if len(labels.keys()) == 1:
        node['label'] = next(iter(labels.keys()))
        return node

    n = len(data['rows'])
    ent = entropy(n, labels)

    max_info_gain = None
    max_info_gain_att = None
    max_info_gain_partitions = None

    for remaining_att in remaining_atts:
        avg_ent, partitions = avg_entropy_w_partitions(data, remaining_att, target_attribute)
        info_gain = ent - avg_ent
        if max_info_gain is None or info_gain > max_info_gain:
            max_info_gain = info_gain
            max_info_gain_att = remaining_att
            max_info_gain_partitions = partitions

    node['attribute'] = max_info_gain_att
    node['nodes'] = {}

    remaining_atts_for_subtrees = set(remaining_atts)
    remaining_atts_for_subtrees.discard(max_info_gain_att)

    for att_value in max_info_gain_partitions.keys():
        partition = max_info_gain_partitions[att_value]
        partition_labels = get_class_labels(partition, target_attribute)
        if len(partition_labels.keys()) == 1:
            node['nodes'][att_value] = {'label': next(iter(partition_labels.keys()))}
        else:
            node['nodes'][att_value] = id3(partition, remaining_atts_for_subtrees, target_attribute)

    return node


def main():
    argv = sys.argv
    print("Command line args are {}: ".format(argv))

    data = load_csv_to_header_data(argv[1])
    data = project_columns(data, ['Outlook', 'Temperature', 'Humidity', 'Windy', 'PlayTennis'])

    mappers = []
    # [val_mapper_with_default_creator({'Current': 'Current', 'Fully Paid': 'Current'}, 'Not Current')]

    for mapper in mappers:
        transform_data(data, mapper)

    target_attribute = 'PlayTennis'
    remaining_attributes = set(data['header'])
    remaining_attributes.remove(target_attribute)

    root = id3(data, remaining_attributes, target_attribute)

    print(root)


if __name__ == "__main__": main()
