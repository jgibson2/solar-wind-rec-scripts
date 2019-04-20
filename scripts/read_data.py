import pandas as pd
import requests
import geojson
import time as tm
import statistics
from geohash import decode_exactly, decode, encode

def extract_wind_capacities(filename, region='east'):
    '''
    Reads GeoJSON file and extracts wind capacities
    :param filename: string of filename
    :return: dataframe of scaled wind capacities
    '''
    capstr = 'net_capacity_factor'
    if region == 'west':
        capstr = 'capacity_factor'
    with open(filename, 'r') as f:
        s = f.read()
        j = geojson.loads(s)
    data = [(e['geometry']['coordinates'][1], e['geometry']['coordinates'][0], e['properties'][capstr])
            for e in j.features if isinstance(e, geojson.feature.Feature)]
    return pd.DataFrame.from_records(data, columns=['lat', 'lon', 'capacity'])


def extract_power_plant_capacities(filename):
    x = pd.read_excel(filename, sheet_name=0, header=1)
    x.columns = map(lambda x: x.strip(), x.columns)
    data = []
    for pid in set(x['Plant ID']):
        try:
            df = x.loc[x['Plant ID'] == pid, ['Latitude', 'Longitude', 'Nameplate Capacity (MW)', 'Plant Name', 'Technology']]
            data.append((df.iloc[0]['Latitude'], df.iloc[0]['Longitude'], sum(df['Nameplate Capacity (MW)']), df.iloc[0]['Plant Name'] + ' ({})'.format(df.iloc[0]['Technology'])))
        except IndexError:
            pass
    df = pd.DataFrame.from_records(data, columns = ['lat', 'lon', 'capacity', 'name'])
    del x
    return df


def query_solar_capacities(api_key, coordinates=None, df=None, lat=None, lon=None, time='annual', dtype='avg_dni', hash_precision=5, request=True, delay=0.0, verbose=False):
    # get the coordinates we need
    data = []
    coords = coordinates
    if coords is None:
        if df is None:
            if lat is not None and lon is not None:
                if len(lat) != len(lon):
                    raise ValueError('Lat and Lon coord lists are not of equal lengths')
                coords = list(zip(lat, lon))
        else:
            coords = list(zip(df['lat'], df['lon']))
    if coords is None:
        raise ValueError('Coordinates not given!')

    hashes, hashdict = limit_coordinates(coords, precision=hash_precision)
    valdict = dict()
    count = 0
    if request:
        for hash, coord in hashdict.items():
            try:
                count += 1
                if verbose and count % 100 == 0:
                    print('Made {} requests of {}'.format(count, len(hashdict.keys())))
                qlat,qlon = coord
                r = requests.get('https://developer.nrel.gov/api/solar/solar_resource/v1.json',
                                 params={'api_key': api_key, 'lat': qlat, 'lon': qlon})
                j = r.json()
                if r.status_code != 200:
                    raise ValueError(j['error']['message'])
                valdict[hash] = j['outputs'][dtype][time]
                tm.sleep(delay)
            except Exception as e:
                print(e)
                pass
        for lat, lon, hash in hashes:
            data.append((lat, lon, valdict.get(hash, 0.0)))
    else:
        print('Would make {} requests to NREL API to obtain information for {} datapoints.'.format(len(hashdict.keys()), len(hashes)))
    return pd.DataFrame.from_records(data, columns=['lat', 'lon', 'capacity'])

def save_all_solar_capacities(api_key, filename, coordinates=None, df=None, lat=None, lon=None, request=True, delay=0.0):
    # get the coordinates we need
    data = []
    coords = coordinates
    if coords is None:
        if df is None:
            if lat is not None and lon is not None:
                if len(lat) != len(lon):
                    raise ValueError('Lat and Lon coord lists are not of equal lengths')
                coords = list(zip(lat, lon))
        else:
            coords = list(zip(df['lat'], df['lon']))
    if coords is None:
        raise ValueError('Coordinates not given!')

    hashes, hashdict = limit_coordinates(coords)
    valdict = dict()
    with open(filename, 'w') as f:
        if request:
            for hash, coord in hashdict.items():
                qlat,qlon = coord
                r = requests.get('https://developer.nrel.gov/api/solar/solar_resource/v1.json',
                                 params={'api_key': api_key, 'lat': qlat, 'lon': qlon})
                f.write(r.text + '\n')
                tm.sleep(delay)
            for lat, lon, hash in hashes:
                data.append((lat, lon, valdict[hash]))
        else:
            print('Would make {} requests to NREL API to obtain information for {} datapoints.'.format(len(hashdict.keys()), len(hashes)))


def limit_coordinates(coordinates, precision=5):
    '''
    Combines coordinates based on geohash precision
    :param coordinates: list of (lat, lon) tuples
    :param precision: geohash precision
    :return:
    '''

    hashes = [(lat, lon, encode(lat, lon, precision)) for lat, lon in coordinates]
    hashdict = dict([(h, decode(h)) for h in set([h[2] for h in hashes])])
    return hashes, hashdict

def limit_df_coordinates(df, precision=5):
    '''
    Combines coordinates based on geohash precision
    :param coordinates: list of (lat, lon) tuples
    :param precision: geohash precision
    :return:
    '''

    hashes = [tup + (encode(getattr(tup,'lat'), getattr(tup,'lon'), precision),) for tup in df.itertuples()]
    temp_dict = dict()
    for tup in hashes: temp_dict[tup[-1]] = temp_dict.get(tup[-1], tup[1:-1])
    used_coords = list(temp_dict.values())
    del temp_dict
    return pd.DataFrame.from_records(used_coords,  columns=df.columns)

def determine_wind_scaling_factor(df_west, df_east, precision=5):
    westcoords = zip(df_west['lat'], df_west['lon'], df_west['capacity'])
    eastcoords = zip(df_east['lat'], df_east['lon'], df_east['capacity'])

    westhash = [(lat, lon, cap, encode(lat, lon, precision)) for lat, lon, cap in westcoords]
    easthash = [(lat, lon, cap, encode(lat, lon, precision)) for lat, lon, cap in eastcoords]

    d = dict()
    for lat, lon, cap, h in westhash:
        d[h] = d.get(h, ([], []))
        d[h][0].append(cap)
    for lat, lon, cap, h in easthash:
        d[h] = d.get(h, ([], []))
        d[h][1].append(cap)
    factors = [statistics.mean(l1) / statistics.mean(l2) for l1,l2 in d.values() if len(l1) > 0 and len(l2) > 0]
    # print(statistics.mean(factors), statistics.median(factors))
    return statistics.median(factors)



if __name__ == '__main__':
    wind1 = extract_wind_capacities('../data/nrel-west_wind_site_metadata.json', region='west')
    wind2 = extract_wind_capacities('../data/nrel-east_wind_site_metadata.json', region='east')
    pp = extract_power_plant_capacities('../data/december_generator2017.xlsx')
    # solar = pd.read_csv('solar_capacities.csv', index_col=0)
    solar = query_solar_capacities('0N0jKddAOiNVOkIqIWIKMVrpqtmfd9XjhACEoU52', df=pp.append(wind1).append(wind2), dtype='avg_ghi', request=False, delay=3.6, verbose=True, hash_precision=4)
    solar.to_csv('solar_capacities_ghi.csv')

    # windW = extract_wind_capacities('../data/nrel-west_wind_site_metadata.json', region='west')
    # windE = extract_wind_capacities('../data/nrel-east_wind_site_metadata.json', region='east')
    # factor = determine_wind_scaling_factor(windW, windE)
    # windE['capacity'] *= factor
    # wind = windW.append(windE)
    # print(wind)





