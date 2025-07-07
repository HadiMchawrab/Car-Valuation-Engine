transmission_map = {
    '1': 'Manual',
    '2': 'Automatic'
}

transmission_name_to_code = {v.lower(): k for k, v in transmission_map.items()}


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

body_type_name_to_code = {v.lower(): k for k, v in body_type_map.items()}


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

color_name_to_code = {v.lower(): k for k, v in color_map.items()}
