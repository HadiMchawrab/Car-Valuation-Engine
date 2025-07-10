export const getTransmissionType = (code) => {
  const transmissionMap = {
    '1': 'Manual',
    '2': 'Automatic'
  };
  return transmissionMap[code?.toString()] || code || 'N/A';
};


export const getBodyType = (code) => {
  const bodyTypeMap = {
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
  };
  return bodyTypeMap[code?.toString()] || code || 'N/A';
};

export const getColor = (code) => {
  const colorMap = {
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
  };
  return colorMap[code?.toString()] || code || 'N/A';
};



