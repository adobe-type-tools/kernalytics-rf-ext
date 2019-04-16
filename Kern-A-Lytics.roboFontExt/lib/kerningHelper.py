import itertools
import collections
import heapq
import random


def _sort_kern_dict(input_dict):
    '''
    Returns sorted kerning as an OrderedDict
    '''
    sorted_dict = collections.OrderedDict(
        sorted(input_dict.items(), key=lambda t: t[0]))
    return sorted_dict


def _gamut(value_list):
    '''
    Returns the maximum value distance in a list of values
    '''
    difference = 0
    n_list = [i for i in value_list if i]
    if any(n_list):
        difference = (max(n_list) - min(n_list))

    return difference


def _average(value_list, conscious=True):
    '''
    Average distance, not average value
    '''
    if conscious:
        n_list = [i for i in value_list if i]
    else:
        n_list = numeric_value_list(value_list)

    # not sure this is necessary
    abs_list = [abs(v) for v in n_list]
    average_value = 0
    if len(abs_list) > 0:
        average_value = sum(abs_list) / len(abs_list)

    return average_value


def _outlier(value_list, factor=4, test=False):
    '''
    Finds value lists in which one or more values are much larger
    (defined by *factor*) than the average
    '''
    n_list = numeric_value_list(value_list, absolute=True)
    if len(set(n_list)) == 1:
        # if all values are zero, no thanks
        return

    average_value = sum(n_list) / len(n_list)
    exceeding_values = [abs(v) >= average_value * factor for v in n_list]
    if test:
        print('average:', average_value)
    if any(exceeding_values):
        if test:
            print(exceeding_values)
        return True
    return


def numeric_value_list(value_list, absolute=False):
    '''
    Convert a list (which may contain Nones) to integers.
    '''
    if absolute:
        return [0 if i is None else abs(i) for i in value_list]
    else:
        return [0 if i is None else i for i in value_list]


def random_value_list(length=None):
    '''
    Just for testing.
    Can be deleted.
    '''
    if length is not None:
        l_length = length
    else:
        l_length = random.randint(2, 20)
    r_list = [random.randint(-1000, 1000) for i in range(l_length)]
    return r_list


def get_repr_pair(font, def_pair):
    '''
    Returns representative glyphs for a given kerning pair
    (which may involve groups). At this point, the method is
    not smart enough to filter out exceptions.
    '''
    left_item, right_item = def_pair
    font_glyph_order = font.lib['public.glyphOrder']
    font_groups = list(font.groups.keys())
    group_dict = {}
    group_dict.update(font.groups)
    # workaround for new get() method in build 1805210915
    # (returns tuple instead of list)
    if set(def_pair) <= set(font_glyph_order + font_groups):
        left_glyphs = list(group_dict.get(def_pair[0], [left_item]))
        right_glyphs = list(group_dict.get(def_pair[1], [right_item]))
        left_glyphs.sort(key=lambda x: font_glyph_order.index(x))
        right_glyphs.sort(key=lambda x: font_glyph_order.index(x))
        return left_glyphs[0], right_glyphs[0]
    return


def get_combined_kern_dict(fonts):
    '''
    Returns a sorted, combined kerning dictionary for a
    number of fonts. If a specific pair is not kerned,
    kerning value is None.
    '''
    combined_pairs = set(itertools.chain.from_iterable(
        font.kerning.keys() for font in fonts))

    c_kerning = {}
    for font in fonts:
        for pair in combined_pairs:
            value = font.kerning.find(pair, None)
            c_kerning.setdefault(pair, []).append(value)

    # make the dict an ordered dict, so we do not have
    # to sort it downstream
    return _sort_kern_dict(c_kerning)


def same_value_dict(cmb_kerning):
    '''
    Pairs in which all items are kerned by the same value
    '''
    output = {}
    for pair, values in cmb_kerning.items():
        if len(set(values)) == 1:
            output[pair] = values
    return _sort_kern_dict(output)


def zero_value_dict(cmb_kerning):
    '''
    Pairs in which all items are unkerned, or kerned by 0
    '''
    output = {}
    for pair, values in cmb_kerning.items():
        if not any([v for v in values]):
            output[pair] = values
    return _sort_kern_dict(output)


def outlier_dict(cmb_kerning, factor=4):
    '''
    Pairs in which one of the values is drastically different from others
    '''
    output = {}
    for pair, values in cmb_kerning.items():
        if _outlier(values, factor):
            output[pair] = values
    return _sort_kern_dict(output)


def high_gamut_dict(cmb_kerning, approx_amount=100):
    '''
    Pairs with the highest kerning gamut
    '''
    output = collections.OrderedDict({})
    gamut_dict = {}
    for pair, values in cmb_kerning.items():
        gamut = _gamut(values)
        gamut_dict.setdefault(gamut, []).append(pair)
    max_gamut_list = sorted(gamut_dict.keys(), reverse=True)
    pair_count = 0
    for gamut_value in max_gamut_list:
        pairs = gamut_dict.get(gamut_value)
        if pair_count < approx_amount:
            for pair in pairs:
                output[pair] = cmb_kerning.get(pair)
        pair_count += len(pairs)
    return output


def largest_value_dict(cmb_kerning, amount=200):
    '''
    Pairs kerned by the largest distance
    '''

    # dictionaries that contain the largest and smallest value per pair
    max_value_dict = {
        pair: max(numeric_value_list(v_list)) for
        (pair, v_list) in cmb_kerning.items()
    }
    min_value_dict = {
        pair: min(numeric_value_list(v_list)) for
        (pair, v_list) in cmb_kerning.items()
    }

    # sorting by value
    max_value_list = sorted(
        # Lambda function to sort the resulting pairs
        # based on the sum of all kerning values
        heapq.nlargest(amount // 2, max_value_dict, key=max_value_dict.get),
        key=lambda pair: sum(numeric_value_list(cmb_kerning.get(pair)))
    )
    min_value_list = sorted(
        # Lambda function to sort the resulting pairs
        # based on the sum of all kerning values
        heapq.nsmallest(amount // 2, min_value_dict, key=min_value_dict.get),
        key=lambda pair: sum(numeric_value_list(cmb_kerning.get(pair)))
    )

    # re-establishing the combined-value dict based on lists created above
    max_value_cmb_dict = {
        pair: cmb_kerning.get(pair) for pair in max_value_list}
    min_value_cmb_dict = {
        pair: cmb_kerning.get(pair) for pair in min_value_list}

    # sorting those dictionaries by the greatest value in the valuelist
    max_sorted_dict = collections.OrderedDict(
        sorted(
            max_value_cmb_dict.items(),
            key=lambda t: max_value_dict.get(t[0]),
            reverse=True))

    min_sorted_dict = collections.OrderedDict(
        sorted(
            min_value_cmb_dict.items(),
            key=lambda t: min_value_dict.get(t[0]),
            reverse=True))

    output = {}
    output.update(max_sorted_dict)
    output.update(min_sorted_dict)
    return output


def _make_grouped_dicts(groups):
    '''
    Creates two dictionaries to identify which group(s)
    a specific glyph belongs to.
    '''
    grouped_dict_left = {}
    grouped_dict_right = {}

    for groupName, glyphList in groups.items():
        if groupName.startswith('public.kern1.'):
            for gName in glyphList:
                grouped_dict_left.setdefault(gName, None)
                grouped_dict_left[gName] = '{}'.format(groupName)

        if groupName.startswith('public.kern2.'):
            for gName in glyphList:
                grouped_dict_right.setdefault(gName, None)
                grouped_dict_right[gName] = '{}'.format(groupName)

    return grouped_dict_left, grouped_dict_right


def single_exception_list(font):
    '''
    Creates a list of exceptions for a single font
    '''
    g_flag = 'public.kern'
    grouped_dict_l, grouped_dict_r = _make_grouped_dicts(font.groups)

    group_group_pairs = [
        pair for pair in font.kerning.keys() if
        all([g_flag in item for item in pair])]
    glyph_group_pairs = [
        pair for pair in font.kerning.keys() if
        g_flag not in pair[0] and g_flag in pair[1]]
    group_glyph_pairs = [
        pair for pair in font.kerning.keys() if
        g_flag in pair[0] and g_flag not in pair[1]]
    glyph_glyph_pairs = [
        pair for pair in font.kerning.keys() if not
        any([g_flag in item for item in pair])]

    pair_list = []
    covered_pairs = []
    for (left, right) in group_glyph_pairs:
        group_pair = (
            left, grouped_dict_r.get(right, right))
        if group_pair in group_group_pairs:
            pair_list.append((left, right))
            pair_list.append(group_pair)
            covered_pairs.append((left, right))

    for (left, right) in glyph_group_pairs:
        group_pair = (
            grouped_dict_l.get(left, left), right)
        if group_pair in group_group_pairs:
            pair_list.append((left, right))
            pair_list.append(group_pair)
            covered_pairs.append((left, right))

    for (left, right) in glyph_glyph_pairs:
        group_l_pair = (
            grouped_dict_l.get(left, left), right)
        group_r_pair = (
            left, grouped_dict_r.get(right, right))
        group_both_pair = (
            grouped_dict_l.get(left, left), grouped_dict_r.get(right, right))

        if (
            group_l_pair in group_glyph_pairs and
            group_l_pair not in covered_pairs
        ):
            pair_list.append((left, right))
            pair_list.append(group_l_pair)
            covered_pairs.append(group_l_pair)
        if (
            group_r_pair in glyph_group_pairs and
            group_r_pair not in covered_pairs
        ):
            pair_list.append((left, right))
            pair_list.append(group_r_pair)
            covered_pairs.append(group_r_pair)
        if (
            group_both_pair in group_group_pairs and
            group_both_pair not in covered_pairs
        ):
            pair_list.append((left, right))
            pair_list.append(group_both_pair)
            covered_pairs.append(group_both_pair)

    zip_list = sorted(zip(pair_list[::2], pair_list[1::2]))
    sorted_pair_list = []
    for exception, base_pair in zip_list:
        sorted_pair_list.append(exception)
        # sorted_pair_list.append(base_pair)
    return sorted_pair_list


def exception_dict(fonts, cmb_kerning):
    all_exceptions = []
    output = collections.OrderedDict({})
    for font in fonts:
        font_exceptions = single_exception_list(font)
        all_exceptions.extend(font_exceptions)
    for pair in all_exceptions:
        if pair not in output.keys():
            output[pair] = cmb_kerning.get(pair)
    return output


def small_average_dict(cmb_kerning, small_av_value=5):
    output = collections.OrderedDict({})
    for pair, values in cmb_kerning.items():
        if _average(values) in range(-small_av_value, small_av_value):
            output[pair] = cmb_kerning.get(pair)
    return output


def single_pair_dict(cmb_kerning):
    output = collections.OrderedDict({})
    for pair, values in cmb_kerning.items():
        if not any([side.startswith('public') for side in pair]):
            output[pair] = cmb_kerning.get(pair)
    return output


def filter_pair_list_by_items(font, pair_list, filter_item_left=None, filter_item_right=None):
    """
    filter a combined kerning dictionary by item featured in the pairs 
    filter_items can be either glyphs or groups
    a font object is necessary for group analysis
    """
    # sanitizing input (?)
    if len(filter_item_left.strip()) == 0:
        filter_item_left = None
    if len(filter_item_right.strip()) == 0:
        filter_item_right = None

    # no filtering needed here
    if not filter_item_left and not filter_item_right:
        return pair_list

    # XXXX maybe it is expensive to have that calculate each time the pair list is updated?
    # should this be cached somewhere?
    grouped_dict_1, grouped_dict_2 = _make_grouped_dicts(font.groups)

    # add groups to the filter items if relevant
    pertinent_items_1 = [filter_item_left]
    group_item_1 = grouped_dict_1.get(filter_item_left, None)
    if group_item_1:
        pertinent_items_1.append(group_item_1)
    pertinent_items_2 = [filter_item_right]
    group_item_2 = grouped_dict_2.get(filter_item_right, None)
    if group_item_2:
        pertinent_items_2.append(group_item_2)

    filtered_kerning = []
    for pair in pair_list:
        pair_item_1, pair_item_2 = pair
        if (filter_item_left == None or pair_item_1 in pertinent_items_1) and (filter_item_right == None or pair_item_2 in pertinent_items_2):
            filtered_kerning.append(pair)

    return filtered_kerning
