import re

# Base maps
transmission_map = {
    '1': 'Manual',
    '2': 'Automatic'
}

body_type_map = {
    '1': 'Sports / Coupe',
    '2': 'Convertible',
    '3': 'Sedan',
    '4': 'Hatchback',
    '5': 'SUV',
    '6': 'Other',
    '7': 'Van / Bus',
    '8': 'Estate',
    '9': 'MPV',
    '10': 'Pickup',
    '11': 'Small City Car'
}

color_map = {
    '1': 'Black',
    '2': 'Blue',
    '3': 'Brown',
    '4': 'Cyan',
    '5': 'Gold',
    '6': 'Green',
    '7': 'Grey',
    '8': 'Orange',
    '9': 'Purple',
    '10': 'Red',
    '11': 'Silver',
    '12': 'White',
    '13': 'Yellow',
    '14': 'Other',
    '15': 'Beige',
    '16': 'Titanium',
    '17': 'Cyan',
    '18': 'Oily Color',
    '19': 'Navy',
    '20': 'Pearl',
    '21': 'Maroon'
}

# Aliases for common variants
transmission_aliases = {
    'manual': 'Manual',
    'auto': 'Automatic',
    'automatic': 'Automatic',
    'automatic transmission': 'Automatic'
}

body_type_aliases = {
    'sports': 'Sports / Coupe',
    'coupe': 'Sports / Coupe',
    'sports coupe': 'Sports / Coupe',
    'estate car': 'Estate',
    'wagon': 'Estate',
    'city car': 'Small City Car',
    'bus': 'Van / Bus',
    'mpv': 'MPV',
    'pickup truck': 'Pickup',
    'van': 'Van / Bus'
}

color_aliases = {
    'navy blue': 'Navy',
    'pearl white': 'White',
    'light grey': 'Grey',
    'dark grey': 'Grey',
    'silver grey': 'Silver',
    'metallic blue': 'Blue'
}


def normalize(text):
    """
    Lowercase, strip, remove punctuation, collapse spaces.
    """
    t = text.lower().strip()
    t = re.sub(r'[^\w\s]', ' ', t)
    return re.sub(r'\s+', ' ', t)


def lookup(code_map, name):
    """
    Normalize and attempt exact or substring match.
    """
    if not name:
        return None
    name_n = normalize(name)
    # exact match
    for code, label in code_map.items():
        if normalize(label) == name_n:
            return code
    # partial match
    for code, label in code_map.items():
        label_n = normalize(label)
        if label_n in name_n or name_n in label_n:
            return code
    return None


def lookup_with_alias(code_map, alias_map, name):
    """
    Try alias lookup then fallback to normalize+lookup.
    """
    if not name:
        return None
    name_n = normalize(name)
    if name_n in alias_map:
        target = alias_map[name_n]
        # find code for target label
        for code, label in code_map.items():
            if normalize(label) == normalize(target):
                return code
    return lookup(code_map, name)


# Public APIs
def get_transmission_code(name):
    return lookup_with_alias(transmission_map, transmission_aliases, name)


def get_body_type_code(name):
    return lookup_with_alias(body_type_map, body_type_aliases, name)


def get_color_code(name):
    return lookup_with_alias(color_map, color_aliases, name)
