from app import app, db
from geopy.distance import geodesic
import pandas as pd
from app.models import Bar_MasterList, Crawl, User
import requests
import json
import datetime
from flask_login import current_user


def check_if_saved(result_list):
    crawl = Crawl.query.filter_by(bar_1 = result_list[0], bar_2 = result_list[1], bar_3 = result_list[2],
                    bar_4=result_list[3], bar_5 = result_list[4], author=current_user).first()
    if crawl is not None:
        return True
    else:
        return False

def get_lat_and_lon(address):
    GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

    params={
        'address' : address, 
        'key' : app.config['GEO_KEY']
    }
    
    resp = requests.get(GOOGLE_MAPS_API_URL,params=params).json()['results'][0]
    print(resp)
        
    #returns tuple with latitude and longitude
    lat_and_lon = (resp['geometry']['location']['lat'], resp['geometry']['location']['lng'])
        
    return lat_and_lon

# calculates the distance between the user and the bars 
def distance(user_lat, user_long, bar_lat, bar_long):
    user_coordinates = (user_lat, user_long)
    bar_coordinates = (bar_lat, bar_long)
    return round(geodesic(user_coordinates, bar_coordinates).miles, 1)


def create_crawl(user_lat = 40.734198,user_long=-73.988325, date=datetime.date.today()):

    # the sql query used to acces the bar master list in the barhopper db
    #db.engine accesses the app context's connection
    query = "SELECT * FROM barhopper.Bar_MasterList"
    df = pd.read_sql(query, db.engine, index_col = 'bar_id')

    # price was of type object so changed the data type to integer
    df['price'] = df['price'].astype('int64')

    #initialize empty list, which will be what we return. It should contain the ID
    return_list = []
    
    #save user_lat,user_long to temp values, which will be changed since distance is calculated relative to last location
    temp_long = user_long
    temp_lat = user_lat
     # date numeric to weekday converter (dict)
    date_dict = {1:"Monday", 2:"Tuesday", 3:"Wednesday", 4:"Thursday", 5:"Friday", 6:"Saturday", 7:"Sunday"}
    # extracts the day of week using date time object created and the date dictionary
    day_of_week = date_dict[date.isoweekday()]
    #top 5, so run loop until return_list length is 5
    while len(return_list) < 5:
        
        #calculate the distance and score
        df['distance'] = df.apply(lambda x: distance(temp_lat, temp_long, x['latitude'], x['longitude']), axis = 1)
        
        #score function
        df['score'] = ((4-df['price'])/4 + df['rating']/5 - df['distance'] + df[day_of_week])/4

        #sort values, take top value 
        df.sort_values(by = ['score'],ascending = False, inplace = True)
        
        #append top value to return_list
        return_list.append(int(df[:1].index.values))
 
        #update temp_long,temp_lat
        temp_long = df.loc[int(df[:1].index.values),'longitude']
        temp_lat = df.loc[int(df[:1].index.values), 'latitude'] 
        
        #drop bar from df
        df.drop([int(df[:1].index.values)],inplace = True)
    return return_list

def toDate(dateString): 
    return datetime.datetime.strptime(dateString, "%m-%d-%Y").date()