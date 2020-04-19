from app import app
from geopy.distance import geodesic
from sqlalchemy import create_engine
import pandas as pd
from config import Config
 

# calculates the distance between the user and the bars 
def distance(user_lat, user_long, bar_lat, bar_long):
    user_cordinates = (user_lat, user_long)
    bar_cordinates = (bar_lat, bar_long)
    return round(geodesic(user_cordinates, bar_cordinates).miles, 1)


def create_crawl(user_lat = 40.734198,user_long=-73.988325):
    # creates connection to database with master list
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    con = engine.connect()

    # the sql query used to acces the bar master list in the barhopper db
    query = "SELECT * FROM barhopper.Bar_MasterList"
    df = pd.read_sql(query, con, index_col = 'bar_id')

    # price was of type object so changed the data type to integer
    df['price'] = df['price'].astype('int64')

    #initialize empty list, which will be what we return. It should contain the ID
    return_list = []
    
    df2 = df.copy()
    #save user_lat,user_long to temp values, which will be changed since distance is calculated relative to last location
    temp_long = user_long
    temp_lat = user_lat
    
    #top 5, so run loop until return_list length is 5
    while len(return_list) < 5:
        
        #calculate the distance and score
        df2['distance'] = df2.apply(lambda x: distance(temp_lat, temp_long, x['latitude'], x['longitude']), axis = 1)
        
        #score function
        df2['score'] = ((4-df2['price'])/4 + df2['rating']/5 - df2['distance'])/3

        #sort values, take top value 
        df2.sort_values(by = ['score'],ascending = False, inplace = True)
        
        #append top value to return_list
        return_list.append(int(df2[:1].index.values))
 
        #update temp_long,temp_lat
        temp_long = df2.loc[int(df2[:1].index.values),'longitude']
        temp_lat = df2.loc[int(df2[:1].index.values), 'latitude'] 
        
        #drop bar from df
        df2.drop([int(df2[:1].index.values)],inplace = True)
        
    return(return_list)
    