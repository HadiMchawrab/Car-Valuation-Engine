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



