import math
import re
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objs as go
import plotly.offline
import plotly.plotly as py
from read_data import *
import configparser

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

plotly.tools.set_credentials_file(username=config['DEFAULT']['NREL_USERNAME'], api_key=config['DEFAULT']['NREL_API_KEY'])
MAPBOX_ACCESS_TOKEN = config['DEFAULT']['MAPBOX_ACCESS_TOKEN']

colors = ['#800000', '#8B0000', '#A52A2A', '#B22222', '#DC143C', '#FF0000', '#FF6347', '#FF7F50', '#CD5C5C', '#F08080',
          '#E9967A', '#FA8072', '#FFA07A', '#FF4500', '#FF8C00', '#FFA500', '#FFD700', '#B8860B', '#DAA520', '#EEE8AA',
          '#BDB76B', '#F0E68C', '#808000', '#FFFF00', '#9ACD32', '#556B2F', '#6B8E23', '#7CFC00', '#7FFF00', '#ADFF2F',
          '#006400', '#008000', '#228B22', '#00FF00', '#32CD32', '#90EE90', '#98FB98', '#8FBC8F', '#00FA9A', '#00FF7F',
          '#2E8B57', '#66CDAA', '#3CB371', '#20B2AA', '#2F4F4F', '#008080', '#008B8B', '#00FFFF', '#00FFFF', '#E0FFFF',
          '#00CED1', '#40E0D0', '#48D1CC', '#AFEEEE', '#7FFFD4', '#B0E0E6', '#5F9EA0', '#4682B4', '#6495ED', '#00BFFF',
          '#1E90FF', '#ADD8E6', '#87CEEB', '#87CEFA', '#191970', '#000080', '#00008B', '#0000CD', '#0000FF', '#4169E1',
          '#8A2BE2', '#4B0082', '#483D8B', '#6A5ACD', '#7B68EE', '#9370DB', '#8B008B', '#9400D3', '#9932CC', '#BA55D3',
          '#800080', '#D8BFD8', '#DDA0DD', '#EE82EE', '#FF00FF', '#DA70D6', '#C71585', '#DB7093', '#FF1493', '#FF69B4',
          '#FFB6C1', '#FFC0CB', '#FAEBD7', '#F5F5DC', '#FFE4C4', '#FFEBCD', '#F5DEB3', '#FFF8DC', '#FFFACD', '#FAFAD2',
          '#FFFFE0', '#8B4513', '#A0522D', '#D2691E', '#CD853F', '#F4A460', '#DEB887', '#D2B48C', '#BC8F8F', '#FFE4B5',
          '#FFDEAD', '#FFDAB9', '#FFE4E1', '#FFF0F5', '#FAF0E6', '#FDF5E6', '#FFEFD5', '#FFF5EE', '#F5FFFA', '#708090',
          '#778899', '#B0C4DE', '#E6E6FA', '#FFFAF0', '#F0F8FF', '#F8F8FF', '#F0FFF0', '#FFFFF0', '#F0FFFF', '#FFFAFA',
          '#000000', '#696969', '#808080', '#A9A9A9', '#C0C0C0', '#D3D3D3', '#DCDCDC', '#F5F5F5', '#FFFFFF']


def capacity_bubbleplot(df, title_string, scale, color='rgb(0,116,217)', filename=None, show=True,
                        legend_string='Capacity', relative=False, logit=False):
    pts = []
    # pt = go.Scattergeo(
    #     locationmode = 'USA-states',
    #     lon = df['lon'],
    #     lat = df['lat'],
    #     text = df['text'] if 'text' in df.columns else None,
    #     marker = go.scattergeo.Marker(
    #         size = df['capacity']/scale,
    #         color = color,
    #         line = go.scattergeo.marker.Line(
    #             width=0.5, color='rgb(40,40,40)'
    #         ),
    #         sizemode = 'area'
    #     ),
    #     name = legend_string
    #  )
    if relative:
        df['relative'] = (df['capacity'] - min(df['capacity'])) / (max(df['capacity']) - min(df['capacity']))
        if logit:
            df['relative'].apply(lambda x: 1.0 / (1.0 + 2.0 * math.exp(x - 0.5)))
    sz = 10
    if scale is not None:
        sz = df['relative'] / scale if relative else df['capacity'] / scale
    pt = go.Scattermapbox(
        lon=df['lon'],
        lat=df['lat'],
        text=df['text'] if 'text' in df.columns else None,
        marker=go.scattermapbox.Marker(
            size=sz,
            color=df['capacity'] if not re.match(r'rgb\(.*\)', color) else color,
            colorscale=color if not re.match(r'rgb\(.*\)', color) else None,
            showscale=True if not re.match(r'rgb\(.*\)', color) else False,
            reversescale=True if color in {'Greens'} else False,
            sizemode='area',
            opacity=0.5 if re.match(r'rgb\(.*\)', color) else 0.8,
            sizemin=1
        ),
        line=go.scattermapbox.Line(
            width=0.5, color='rgb(40,40,40)'
        ),
        name=legend_string
    )
    pts.append(pt)
    layout = go.Layout(
        title=go.layout.Title(
            text=title_string
        ),
        showlegend=True,
        # geo = go.layout.Geo(
        #     scope = 'usa',
        #     projection = go.layout.geo.Projection(
        #         type='albers usa'
        #     ),
        #     showland = True,
        #     landcolor = 'rgb(217, 217, 217)',
        #     subunitwidth=1,
        #     countrywidth=1,
        #     subunitcolor="rgb(255, 255, 255)",
        #     countrycolor="rgb(255, 255, 255)"
        # )
        mapbox=go.layout.Mapbox(
            accesstoken=MAPBOX_ACCESS_TOKEN,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=38,
                lon=-94
            ),
            pitch=0,
            zoom=3,
            # style='light''
        ),
        autosize=True,
        hovermode='closest'
    )

    fig = go.Figure(data=pts, layout=layout)

    if show: py.plot(fig, filename=re.sub(r'[\s/]+', '-', title_string) if filename is None else filename)
    return fig


def capacity_bubbleplot_multicolor(df, title_string, scale, split='technology', filename=None, show=True,
                                      legend_string='Capacity', relative=False, logit=False):
    pts = []
    color_set = dict([(col, idx) for idx, col in enumerate(set(pp[split]))])
    pp['color'] = pp[split].map(lambda x: colors[(color_set[x] * len(colors) // len(color_set)) % len(colors)])
    if relative:
        df['relative'] = (df['capacity'] - min(df['capacity'])) / (max(df['capacity']) - min(df['capacity']))
        if logit:
            df['relative'].apply(lambda x: 1.0 / (1.0 + 2.0 * math.exp(x - 0.5)))
    df['size'] = 10
    if scale is not None:
        df['size'] = df['relative'] / scale if relative else df['capacity'] / scale
    for s in sorted(set(df[split])):
        dfsplit = df.loc[df[split] == s]
        pt = go.Scattermapbox(
            lon=dfsplit['lon'],
            lat=dfsplit['lat'],
            text=dfsplit['text'] if 'text' in dfsplit.columns else None,
            marker=go.scattermapbox.Marker(
                size=dfsplit['size'],
                color=dfsplit['color'],
                showscale=False,
                reversescale=False,
                sizemode='area',
                opacity=0.75,
                sizemin=2
            ),
            line=go.scattermapbox.Line(
                width=0.5, color='rgb(40,40,40)'
            ),
            name=dfsplit.iloc[0][split]
        )
        pts.append(pt)
    layout = go.Layout(
        title=go.layout.Title(
            text=title_string
        ),
        showlegend=True,
        # geo = go.layout.Geo(
        #     scope = 'usa',
        #     projection = go.layout.geo.Projection(
        #         type='albers usa'
        #     ),
        #     showland = True,
        #     landcolor = 'rgb(217, 217, 217)',
        #     subunitwidth=1,
        #     countrywidth=1,
        #     subunitcolor="rgb(255, 255, 255)",
        #     countrycolor="rgb(255, 255, 255)"
        # )
        mapbox=go.layout.Mapbox(
            accesstoken=MAPBOX_ACCESS_TOKEN,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=38,
                lon=-94
            ),
            pitch=0,
            zoom=3,
            # style='light'
        ),
        autosize=True,
        hovermode='closest'
    )

    fig = go.Figure(data=pts, layout=layout)

    if show: py.plot(fig, filename=re.sub(r'[\s/]+', '-', title_string) if filename is None else filename)
    return fig


def capacity_bubbleplot_multi(dfs, title_string, scales, colors=['rgb(0,116,217)'], filename=None, show=True,
                              legend_strings=['Capacity'], relative=[False], logit=False):
    pts = []
    for i, df in enumerate(dfs):
        if relative[i % len(relative)]:
            df['relative'] = (df['capacity'] - min(df['capacity'])) / (max(df['capacity']) - min(df['capacity']))
            if logit:
                df['relative'].apply(lambda x: 1.0 / (1.0 + 2.0 * math.exp(x - 0.5)))
        sz = 10
        if scales[i % len(scales)] is not None:
            sz = df['relative'] / scales[i % len(scales)] if relative[i % len(relative)] else df['capacity'] / scales[
                i % len(scales)]
        pt = go.Scattermapbox(
            lon=df['lon'] + 0.005 * np.random.randn(len(df)),  # add jitter
            lat=df['lat'] + 0.005 * np.random.randn(len(df)),
            text=df['text'] if 'text' in df.columns else None,
            marker=go.scattermapbox.Marker(
                size=sz,
                color=colors[i % len(colors)] if re.match(r'rgb\(.*\)', colors[i % len(colors)]) else df['capacity'],
                colorscale=colors[i % len(colors)] if not re.match(r'rgb\(.*\)', colors[i % len(colors)]) else None,
                reversescale=True if colors[i % len(colors)] in {'Greens'} else False,
                # showscale=True if gradients is not None else False,
                sizemode='area',
                opacity=0.5 if re.match(r'rgb\(.*\)', colors[i % len(colors)]) else 0.8,
                sizemin=1
            ),
            line=go.scattermapbox.Line(
                width=0.5, color='rgb(40,40,40)'
            ),
            name=legend_strings[i % len(legend_strings)]
        )
        pts.append(pt)
    # layout = go.Layout(
    #     title=go.layout.Title(
    #         text=title_string
    #     ),
    #     showlegend=True,
    #     geo=go.layout.Geo(
    #         scope='usa',
    #         projection=go.layout.geo.Projection(
    #             type='albers usa'
    #         ),
    #         showland=True,
    #         landcolor='rgb(217, 217, 217)',
    #         subunitwidth=1,
    #         countrywidth=1,
    #         subunitcolor="rgb(255, 255, 255)",
    #         countrycolor="rgb(255, 255, 255)"
    #     )
    layout = go.Layout(
        title=go.layout.Title(
            text=title_string
        ),
        showlegend=True,
        mapbox=go.layout.Mapbox(
            accesstoken=MAPBOX_ACCESS_TOKEN,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=38,
                lon=-94
            ),
            pitch=0,
            zoom=3,
            # style='light'
        ),
        autosize=True,
        hovermode='closest'
    )

    fig = go.Figure(data=pts, layout=layout)
    if show: py.plot(fig, filename=re.sub(r'[\s/]+', '-', title_string) if filename is None else filename)
    return fig


if __name__ == '__main__':
    pp = extract_power_plant_capacities('../data/december_generator2017.xlsx')
    pp['text'] = pp['name'] + '<br>Production Capacity: ' + pp['capacity'].map('{:.1f}'.format) + ' MW'
    pp['technology'] = pp['name'].map(lambda x: re.match(r'.*\((.*)\)', x).group(1))


    print(pp)
    capacity_bubbleplot_multicolor(pp, 'Power Plant Capacities in MW By Type', 10, legend_string='Power Plant Capacity')

    solar = pd.read_csv('../data/solar_capacities_ghi_nozeros.csv', index_col=0)
    solar = limit_df_coordinates(solar, 4)
    solar['text'] = 'Global Horizontal Irradiance: ' + solar['capacity'].map('{:.1f}'.format) + ' kWh/m^2/day'
    # solar['text'] = 'Direct Normal Irradiance: ' + solar['capacity'].map('{:.1f}'.format) + ' kWh/m^2/day'
    capacity_bubbleplot(solar, 'Solar Capacities in kWh/m^2/day', 0.0035, legend_string='Solar Capacity', color='rgb(250,194,5)', relative=True, logit=True)
    capacity_bubbleplot(solar, 'Solar Capacities in kWh/m^2/day', None, legend_string='Solar Capacity', color='Reds', filename='Gradient-Solar-Capacities')

    windW = extract_wind_capacities('../data/nrel-west_wind_site_metadata.json', region='west')
    windE = extract_wind_capacities('../data/nrel-east_wind_site_metadata.json', region='east')
    factor = determine_wind_scaling_factor(windW, windE)
    windE['capacity'] *= factor
    wind = limit_df_coordinates(windW.append(windE), precision=4)
    wind['text'] = 'Capacity Factor: ' + wind['capacity'].map('{:.2f}'.format)
    capacity_bubbleplot(wind, 'Wind Capacity Factors', 0.01, legend_string='Wind Capacity',
                        color='rgb(45,249,5)', relative=True, logit=True)
    capacity_bubbleplot(wind, 'Wind Capacity Factors', None, legend_string='Wind Capacity',
                        color='Greens', filename='Gradient-Wind-Capacities')

    capacity_bubbleplot_multi([solar, wind, pp], 'Wind and Solar Capacity Factors with Power Plant Capacities', [None, None, 10],
                              legend_strings=['Solar Capacity Factor', 'Wind Capacity Factor', 'Power Plant Capacities'],
                              colors=['Reds', 'Greens', 'rgb(0,116,217)'])

    capacity_bubbleplot_multi(
        [solar.sort_values('capacity', ascending=False).head(100),
         wind.sort_values('capacity', ascending=False).head(100),
         pp.loc[pp['capacity'] >= 100.0]],
        'Limited Wind and Solar Capacity Factors with Power Plant Capacities',
        [0.05, 0.225, 20],
        legend_strings=['Solar Capacity Factor', 'Wind Capacity Factor', 'Power Plant Capacities'],
        colors=['rgb(250,194,5)', 'rgb(45,249,5)', 'rgb(0,116,217)'])

    with plt.style.context('seaborn'):

        plt.figure()

        plt.subplot(1,3,1)
        plt.hist(pp['capacity'], color='b', bins=20)
        plt.xlabel('Capacity (MW)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Power Plant Capacity')

        plt.subplot(1, 3, 2)
        plt.hist(solar['capacity'], color='r', bins=20)
        plt.xlabel('Capacity (kW/m^2/hr)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Solar Capacity')

        plt.subplot(1, 3, 3)
        plt.hist(wind['capacity'], color='g', bins=20)
        plt.xlabel('Capacity Factor')
        plt.ylabel('Frequency')
        plt.title('Histogram of Wind Capacity Factors')

        plt.show()
