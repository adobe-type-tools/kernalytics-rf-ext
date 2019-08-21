import re
import sys

weight_names = [
    'hair',
    'thin',
    'extralight',
    'light',
    'regular',
    'book',
    'medium',
    'semibold',
    'bold',
    'extrabold',
    'black',
    'ultra',
    'fat',
]

width_names = [
    'xcondensed',
    'narrow',
    'condensed',
    'cnd',
    'semicondensed',
    'semicond',
    'normal',
    'extended',
    'wide',
    'xwide',
    'expanded',
]

opsz_names = [
    'caption',
    'text',
    'normal',
    'subhead',
    'display',
    'large',
    'poster',
]


def find_longest_match(name_list, match_indices):
    found_names = [
        (len(name), name) for (name_index, name) in enumerate(name_list) if
        name_index in match_indices
    ]
    _, longest_name = sorted(found_names)[-1]
    longest_name_index = name_list.index(longest_name)
    return longest_name_index


def sort_fonts(all_fonts):
    '''
    Sort fonts by a hard-coded list of style names
    '''
    matches = {}
    for f in all_fonts:

        opsz_matches = []
        width_matches = []
        weight_matches = []

        for opsz_index, opsz_name in enumerate(opsz_names):
            opsz_expression = re.compile(
                rf'(.+?)?({opsz_name})(.+?)?', re.IGNORECASE)
            if re.match(opsz_expression, f.info.styleName):
                opsz_matches.append(opsz_index)
        if opsz_matches:
            opsz_score = find_longest_match(opsz_names, opsz_matches)
        else:
            normal_index = opsz_names.index('normal')
            opsz_score = normal_index

        for width_index, width_name in enumerate(width_names):
            width_expression = re.compile(
                rf'(.+?)?( )?({width_name})( )?(.+?)?', re.IGNORECASE)
            if re.match(width_expression, f.info.styleName):
                width_matches.append(width_index)
                # width_score = f'{width_index:03d}'
        if width_matches:
            width_score = find_longest_match(width_names, width_matches)
        else:
            normal_index = width_names.index('normal')
            width_score = normal_index

        for weight_index, weight_name in enumerate(weight_names):
            weight_expression = re.compile(
                rf'(.+?)?({weight_name})(.+?)?', re.IGNORECASE)
            if re.match(weight_expression, f.info.styleName):
                weight_matches.append(weight_index)
                # weight_score = f'{weight_index:03d}'
            if weight_matches:
                weight_score = find_longest_match(weight_names, weight_matches)
            else:
                normal_index = weight_names.index('regular')
                weight_score = normal_index

        if re.match(r'.*(it)(alic)?.*', f.info.styleName, re.IGNORECASE):
            weight_score += 100

        style_hash = f'{opsz_score:03d}{width_score:03d}{weight_score:03d}'
        matches.setdefault(f, []).append(int(style_hash))

    score_dict = {min(score_list): f for f, score_list in matches.items()}
    sorted_fonts = [f for _, f in sorted(score_dict.items())]
    unsorted = set(all_fonts) - set(sorted_fonts)

    if unsorted:
        for font_obj in sorted(unsorted):  # LOL
            print('could not sort', font_obj.info.styleName)
        sorted_fonts.append(font_obj)
    return(sorted_fonts)


if __name__ == '__main__':
    import argparse
    import os
    import defcon

    parser = argparse.ArgumentParser(
        description='Font Sorting Test')

    parser.add_argument(
        'd',
        action='store',
        metavar='DIRECTORY',
        help='directory which contains UFOs')

    args = parser.parse_args()
    arg_directory = args.d

    if args.d:
        font_paths = []
        if os.path.isdir(args.d):
            for root, folders, files in os.walk(args.d):
                for folder in folders:
                    if folder.endswith('.ufo'):
                        font_paths.append(os.path.join(root, folder))

    font_list = [defcon.Font(f_path) for f_path in font_paths]
    print()
    for font_obj in font_list:
        print(font_obj.info.styleName)
    print()
    for font_obj in sort_fonts(font_list):
        print(font_obj.info.styleName)
