import folium
import json
import urllib.request
import pandas as pd


url1 = "https://api.covid19api.com/summary"
url2 = "https://restcountries.eu/rest/v2/all"
url3 = "https://raw.githubusercontent.com/Sandeeppushp/Covid19Map/master/data/countriesBorderJson.json"


# url_req function returns a json object,using the urrlib.request module open the url passed as an argument.
# the request is converted to json object


def url_req(url):
    request = urllib.request.urlopen(url)
    if(request.getcode() == 200):
        data = json.loads(request.read())
    else:
        print("Error receiving data", request.getcode())
    return data


# the covid-19 data is converted to dataframe
df1 = pd.json_normalize(url_req(url1)["Countries"])

# the countries data for latitude and longitude is converted to dataframe
df2 = pd.json_normalize(url_req(url2))

# slicing the dataframes for the required columns of data
df2 = df2.loc[:, ["name", "latlng"]]
df1 = df1.loc[:, ['Country', 'TotalConfirmed',
                  'TotalDeaths', 'TotalRecovered']]

# the intersection of the new dataframes after slicing is taken using merge function ,
# the intersection is done with country names inorder to filter out the countries
# without the covid-19 data.
df3 = pd.merge(df1, df2, how="inner", left_on="Country", right_on="name")

# converting the dataframe columns to list for python operations
countryName = list(df3['Country'])
lat = list(df3['latlng'])
totalConfirmed = list(df3['TotalConfirmed'])
totalDeaths = list(df3['TotalDeaths'])
totalRecovered = list(df3['TotalRecovered'])

# geojson data is requested , for choropleth
countriesBorder = url_req(url3)

# replacing the country name in df3 for  matching with the geojson data
# this has to be done or the countries with abbreviation will not be in the choropleth
df3.replace('United States of America', 'USA', inplace=True)
df3.replace('Tanzania, United Republic of',
            'United Republic of Tanzania', inplace=True)
df3.replace('Russian Federation', 'Russia', inplace=True)
df3.replace('Timor-Leste', 'East Timor', inplace=True)
df3.replace('Brunei Darussalam', 'Brunei', inplace=True)
df3.replace("Côte d'Ivoire", 'Ivory Coast', inplace=True)
df3.replace('Republic of Kosovo	', 'Kosovo', inplace=True)
df3.replace('Serbia', 'Republic of Serbia', inplace=True)
df3.replace('Viet Nam', 'Vietnam', inplace=True)

# color_producer takes in the death and confirmed cases
# returns a color according to cfr
# cfr is calculated with death to infected percentage,
# for giving colour indicator to the marker


def color_producer(death, confirmed):
    cfr = (death/confirmed)*100
    if cfr < 5:
        return "green"
    elif 5 <= cfr < 20:
        return "orange"
    else:
        return "red"


# Base map is made with inital location set with Indian lat and long
map = folium.Map(location=[21, 78], zoom_start=4, tiles=None)

# used to give tile and inorder to give a name for the map in layerc control
folium.TileLayer('cartodbpositron', name='Covid-19 Map').add_to(map)

# feature group is made to set layer for marker and also provide name and initial state of the layer
# show=False sets the marker layer unchecked when the basemap loads initially
fg = folium.FeatureGroup(name="Details", show=False)

# lists are iterated to set the details of each country
# the lists are iterated parallely using zip() in the for loop in order to retrieve data regarding a particular country
# the Marker fucntion sets the maker on basemap with the given coordinates along with a popup displaying the details

for cord, namelt, ttlCnf, ttlDeths, ttlRcvrd in zip(lat, countryName, totalConfirmed, totalDeaths, totalRecovered):
    fg.add_child(folium.Marker(  # the deaths,confirmed and recovered are converted to string to display along with styling
        location=cord, popup=folium.Popup(("<strong><b>Country : "+namelt+"</strong><br>" +
                                           "<strong><b>Total Cases : "+str(ttlCnf)+"</strong><br>" +
                                           "<strong><font color=red>Deaths : </font>" + str(ttlDeths)+"</strong><br>" +
                                           "<strong><font color=green>Recovered :</font> "+str(ttlRcvrd)+"</strong>"), max_width=200,),
        # color_producer returns a color for the marker
        icon=folium.Icon(color_producer(ttlDeths, ttlCnf))))

# Choropleth function takes in th geodata of countries and the covid data
# with columns that are used to represent the choropleth data and key_on argument that matches the geodata and covid data

choroplethData = folium.Choropleth(
    geo_data=countriesBorder,
    name="Choropleth COVID-19",
    data=df3,
    columns=['Country', 'TotalConfirmed'],
    key_on='feature.properties.name',
    fill_color='Blues',
    fill_opacity=1,
    fill_line=1,
    nan_fill_color='gray',
    line_color='blue',
    legend_name='Confirmed cases',
).add_to(map)

# tooltip to show the country name when the choropleth is displayed
folium.GeoJsonTooltip(
    ['name'],
    lables=False
).add_to(choroplethData.geojson)

# the feature group is added to map
map.add_child(fg)

# layer control is set
map.add_child(folium.LayerControl())
map.save("index.html")
