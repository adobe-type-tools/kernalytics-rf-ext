import os
import plistlib
import re

from fontTools import ttLib

weight_names = [
    'hair',
    'ultralight',
    'thin',
    'extralight',
    'light',
    'semilight',
    'book',
    'regular',
    'medium',
    'semibold',
    'bold',
    'extrabold',
    'heavy',
    'black',
    'ultra',
    'fat',
]

width_names = [
    ['extracondensed', 'extracond', 'xcondensed', 'xcond'],
    ['narrow'],
    ['condensed', 'cond', 'cnd'],
    ['semicondensed', 'semicond', 'semicnd', 'semicn'],
    ['normal'],
    ['extended'],
    ['wide'],
    ['xwide'],
    ['expanded'],
]

opsz_names = [
    ['null'],
    ['caption', 'capt'],
    ['5pt'],
    ['7pt'],
    ['smalltext', 'smtxt'],
    ['text'],
    ['normal'],
    ['subhead', 'subh'],
    ['display', 'disp'],
    ['large'],
    ['poster'],
]


def find_longest_match(name_list, match_indices):
    found_names = [
        (len(name), name) for (name_index, name) in enumerate(name_list) if
        name_index in match_indices
    ]
    _, longest_name = sorted(found_names)[-1]
    longest_name_index = name_list.index(longest_name)
    return longest_name_index


def base_file_name(file):
    base_name = os.path.basename(file)
    file_name = os.path.splitext(base_name)[0]
    style_name = file_name.split('-')[-1]
    return style_name


def get_ps_font_name(font):

    if os.path.isdir(font):  # UFO

        fontinfo_path = os.path.join(font, 'fontinfo.plist')
        with open(fontinfo_path, 'rb') as fi_blob:
            fi_data = plistlib.load(fi_blob)

        ps_font_name = fi_data.get('postscriptFontName', None)
        if not ps_font_name:
            family_name = fi_data.get('familyName', 'Family Name')
            style_name = fi_data.get('styleName', 'Style Name')
            ps_font_name = '-'.join([
                family_name.replace(' ', ''),
                style_name.replace(' ', '')
            ])

    else:
        ttf = ttLib.TTFont(os.path.abspath(font))
        name_table = ttf.get('name')
        name_records = name_table.names
        ps_font_name = [
            nr.toUnicode() for nr in name_records if nr.nameID == 6][0]

    return ps_font_name


def sort_fonts(all_fonts, italics_interspersed=False, debug=False):
    '''
    Sort a list of font- or UFO paths by a hard-coded list of
    example style names.
    '''

    matches = {}
    for f in all_fonts:

        opsz_matches = []
        width_matches = []
        weight_matches = []
        ps_font_name = get_ps_font_name(f)

        # finding and scoring optical size
        for opsz_index, opsz_name_list in enumerate(opsz_names):
            for opsz_name_variant in opsz_name_list:
                opsz_expression = re.compile(
                    rf'(.+?)?({opsz_name_variant})(.+?)?', re.IGNORECASE)
                if re.match(opsz_expression, ps_font_name):
                    opsz_matches.append(opsz_index)
        if opsz_matches:
            opsz_score = find_longest_match(opsz_names, opsz_matches)
        else:
            normal_index = opsz_names.index(['normal'])
            opsz_score = normal_index

        # finding and scoring width
        for width_index, width_name_list in enumerate(width_names):
            for width_name_variant in width_name_list:
                width_expression = re.compile(
                    rf'(.+?)?( )?({width_name_variant})( )?(.+?)?', re.IGNORECASE)
                # Removing spaces from style name, so “Extra Condensed” and
                # “ExtraCondensed” both work.
                if re.match(width_expression, ps_font_name.replace(' ', '')):
                    width_matches.append(width_index)
        if width_matches:
            width_score = find_longest_match(width_names, width_matches)
        else:
            normal_index = width_names.index(['normal'])
            width_score = normal_index

        # finding and scoring weight
        for weight_index, weight_name in enumerate(weight_names):
            weight_expression = re.compile(
                rf'(.+?)?({weight_name})(.+?)?', re.IGNORECASE)
            if re.match(weight_expression, ps_font_name.replace(' ', '')):
                weight_matches.append(weight_index)

            if weight_matches:
                weight_score = find_longest_match(weight_names, weight_matches)
            else:
                normal_index = weight_names.index('regular')
                weight_score = normal_index

        # there may be an index number at the end (Source Serif Masters)
        index_match = re.match(r'.+?(\d+?)', ps_font_name)
        if index_match:
            index_score = int(index_match.group(1))
        else:
            index_score = 0

        if italics_interspersed:
            if re.match(r'.*(it)(alic)?.*', ps_font_name, re.IGNORECASE):
                it_score = 1
            else:
                it_score = 0
            style_hash = (
                f'{opsz_score:03d}{width_score:03d}'
                f'{weight_score:03d}{index_score:02d}{it_score}')
        else:
            if re.match(r'.*(it)(alic)?.*', ps_font_name, re.IGNORECASE):
                weight_score += 100
            style_hash = (
                f'{opsz_score:03d}{width_score:03d}'
                f'{weight_score:03d}{index_score:02d}')

        matches.setdefault(f, []).append(int(style_hash))

    score_dict = {min(score_list): f for f, score_list in matches.items()}
    sorted_fonts = [f for _, f in sorted(score_dict.items())]
    unsorted = set(all_fonts) - set(sorted_fonts)

    if unsorted:
        remaining_fonts = sorted(unsorted)  # LOL
        if debug:
            for f in remaining_fonts:
                print(
                    'could not sort',
                    os.path.dirname(f),
                    os.path.basename(f))
        for f in remaining_fonts:
            sorted_fonts.append(f)

    return(sorted_fonts)


def get_font_paths(directory):
    ufo_paths = []
    otf_paths = []
    ttf_paths = []

    if os.path.isdir(directory):
        for root, folders, files in os.walk(directory):
            for folder in folders:
                if folder.endswith('.ufo'):
                    ufo_paths.append(os.path.join(root, folder))
            for file in files:
                extension = os.path.splitext(file.lower())[-1]
                if extension == '.otf':
                    otf_paths.append(os.path.join(root, file))
                if extension == '.ttf':
                    ttf_paths.append(os.path.join(root, file))

    if ufo_paths:
        return ufo_paths
    elif otf_paths:
        return otf_paths
    else:
        return ttf_paths


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Font Sorting Test')

    parser.add_argument(
        'input_dir',
        action='store',
        metavar='FOLDER',
        help=(
            'Directory which may contain (in order of preference) '
            'UFOs, OTFs, or TTFs.'))

    parser.add_argument(
        '-i', '--italics_interspersed',
        action='store_true',
        default=False,
        help=('Italics adjacent to their related Romans'))

    args = parser.parse_args()

    if args.input_dir and os.path.exists(args.input_dir):
        font_list = get_font_paths(args.input_dir)
        if font_list:
            print('unsorted:')
            for font in font_list:
                print(get_ps_font_name(font))
            print()
            sorted_fonts = sort_fonts(
                font_list,
                args.italics_interspersed,
                debug=True
            )
            print('sorted:')
            for font in sorted_fonts:
                print(get_ps_font_name(font))
        else:
            print('no OTFs, TTFs or UFOs found.')
