# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 08:44:43 2021

@author: nb137

This file does the ground work of importing and calculating key values for time-series performance data

A lot of this is based off of 
https://github.com/NREL/rdtools/blob/master/docs/degradation_and_soiling_example.ipynb
As was retrieved on 2/27/21
"""

import pandas as pd
import numpy as np
import pvlib
''' IMPORT DATA '''
file_name = '84-Site_12-BP-Solar.csv'
df = pd.read_csv(file_name) #146MB
df = df.rename(columns = {
    u'12 BP Solar - Active Power (kW)':'power',
    u'12 BP Solar - Wind Speed (m/s)': 'wind',
    u'12 BP Solar - Weather Temperature Celsius (\xb0C)': 'Tamb',
    u'12 BP Solar - Global Horizontal Radiation (W/m\xb2)': 'ghi',
    u'12 BP Solar - Diffuse Horizontal Radiation (W/m\xb2)': 'dhi'
})

meta = {"latitude": -23.762028,
        "longitude": 133.874886,
        "timezone": 'Australia/North',
        "tempco": -0.005,
        "azimuth": 0,
        "tilt": 20,
        "pdc": 5100.0,
        "temp_model": 'open_rack_cell_polymerback',
        "a":-3.56,
        "b":-0.075,
        'delT':3} # a b delT for open rack glass/polymer module model


df.index = pd.to_datetime(df.Timestamp) # Now index is time stamp col
df.index = df.index.tz_localize(meta["timezone"], ambiguous = 'infer')  # Timezone added to index tims

df['power'] = df.power * 1000
freq = pd.infer_freq(df.index[:10])
df = df.resample(freq).median() # infer median values from average freq
df['energy'] = df.power * pd.to_timedelta(df.power.index.freq).total_seconds()/(3600)

loc = pvlib.location.Location(meta['latitude'], meta['longitude'], tz=meta['timezone'])
sun = loc.get_solarposition(df.index)

sky = pvlib.irradiance.isotropic(meta['tilt'], df.dhi)  # Returns diffuse light
df['dni'] = (df.ghi - df.dhi)/np.cos(np.deg2rad(sun.zenith))
beam = pvlib.irradiance.beam_component(meta['tilt'], meta['azimuth'], sun.zenith, sun.azimuth, df.dni) # Direct beam of sun
df['poa'] = beam+sky

df['Tcell'] = pvlib.temperature.sapm_cell(df.poa, df.Tamb, df.wind, meta['a'], meta['b'], meta['delT'])

df.loc[df['poa'] > 1300, 'poa'] = np.nan    # Just clear out some entries with unrealistic/extreme data