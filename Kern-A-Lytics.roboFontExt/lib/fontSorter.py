import re

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


def sort_fonts(all_fonts):
    '''
    Sort fonts by a hard-coded list of style names
    '''
    matches = {}
    for f in all_fonts:
        for match_index, weight_name in enumerate(weight_names):
            weight_expression = re.compile(
                r'{}(\-| )?(it)?(alic)?'.format(weight_name), re.IGNORECASE)
            if re.match(weight_expression, f.info.styleName):
                if re.match(
                    r'.*(it)(alic)?.*', f.info.styleName, re.IGNORECASE
                ):
                    match_index += 100
                    # sort the Italics in the back
                matches.setdefault(f, []).append(match_index)

    # the Regular style is often not explicitly named,
    # that’s why it may be left out of the matching
    for f in set(all_fonts) - set(matches):
        regular_index = weight_names.index('regular')
        if re.match(r'.*(it)(alic)?.*', f.info.styleName, re.IGNORECASE):
            regular_index += 100
        matches.setdefault(f, [regular_index])

    score_dict = {min(score_list): f for f, score_list in matches.items()}
    sorted_fonts = [f for _, f in sorted(score_dict.items())]
    return(sorted_fonts)
