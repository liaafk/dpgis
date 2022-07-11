import geopandas as gpd
import diffprivlib
import pandas as pd
from pandasql import sqldf

def testquery(conn, sql):
    df = gpd.GeoDataFrame.from_postgis(sql, conn, geom_col='loc' )
    return(df)
    
def ANON_ST_Envelope(cur, query):
    cur.execute(query)
    query_results = cur.fetchall()

    return(query_results)

def getQueryParts(query):
    print("Splitting parts of query...")
    query_parts = query.rsplit("FROM")
    return(query_parts)

def getQueryPoints(query, datapoint_attribute, conn):
    try:
        part_from = getQueryParts(query)[1]
    except:
            print("ERROR: Query doesn't contain 'FROM'.")
            return
    print("Getting all points of query...")
    try:
        raw_points_query = "SELECT "+ datapoint_attribute + " FROM " + part_from
    except:
        print("ERROR: SQL request wrong, probably wrong datapoint attribute name.")
    raw_points = gpd.GeoDataFrame.from_postgis(raw_points_query, conn, datapoint_attribute)
    return raw_points

def getExtremePoints(raw_points):
    return raw_points.dissolve().total_bounds

def removeExtremePoints(raw_points, datapoint_attribute):
    minx, miny, maxx, maxy = getExtremePoints(raw_points)
    raw_points_x = raw_points[datapoint_attribute].x
    raw_points_y = raw_points[datapoint_attribute].y
    d = {'longitude': raw_points_x, 'latitude': raw_points_y}
    df= pd.DataFrame(d)
    #df_no_extreme_x = df.drop(df[df['longitude'].isin([minx, maxx])])
    #df_no_extreme_xy = df.drop(df[df['latitude'].isin([miny, maxy])])
    df_no_extreme_x = df[~df['longitude'].isin([minx, maxx])]
    df_no_extreme_xy = df_no_extreme_x[~df_no_extreme_x['latitude'].isin([miny, maxy])]
    gdf = gpd.GeoDataFrame(
        df_no_extreme_xy, geometry=gpd.points_from_xy(df_no_extreme_xy.longitude, df_no_extreme_xy.latitude))
    return gdf

def getNoisyPoints(minx, miny, maxx, maxy, raw_points, eps):
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    raw_points_x = raw_points['geometry'].x
    raw_points_y = raw_points['geometry'].y
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    noisy_points_x = raw_points_x.apply(lambda val: lap_x.randomise(value=val))
    noisy_points_y = raw_points_y.apply(lambda val: lap_y.randomise(value=val))
    df = {"longitude": noisy_points_x, "latitude": noisy_points_y}
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']), crs="EPSG:4326")
    return gdf

def addLaplaceToResponse(minx, miny, maxx, maxy, response, eps):
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    
    return

def dp_sql_response(query, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result):
    #points relevant to query
    points = getQueryPoints(query, datapoint_attribute, conn)
    print("points wo noise: ", points)
    #get extreme points
    minx, miny, maxx, maxy = getExtremePoints(points)
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=float(epsilon), sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=float(epsilon), sensitivity=ysensitivity, lower=miny, upper=maxy)

    if remove_extreme_points:
        #points relevant to query WITHOUT extreme points
        print("removing extreme points")
        points = removeExtremePoints(points, datapoint_attribute)
        print("removed extreme points")
    
    #points (with or without extreme points) as geodf WITHOUT noise
    print("defining geo_df")
    print("points (w/o extreme?): ", points)
    print("points type: ", type(points))
    print("points['geometry'].x: ", points['geometry'].x)
    geo_df = gpd.GeoDataFrame(points, crs="EPSG:4326")
    if noisy_points:
        #point as geodf WITH noise
        print("get noisy points")
        geo_df = getNoisyPoints(minx, miny, maxx, maxy, points, float(epsilon))
        print("defined geo_df")

    select_query =  getQueryParts(query)[0].lower()
    if "st_envelope" in select_query:
        result = geo_df.dissolve().total_bounds
        if noisy_result:
            result = [lap_x.randomise(result[0]), lap_y.randomise(result[1]), lap_x.randomise(result[2]), lap_y.randomise(result[3])]
    
    elif "st_centroid" in select_query:
        result = geo_df.dissolve().centroid[0]
        if noisy_result:
            result = [lap_x.randomise(result.x), lap_y.randomise(result.y)]

    elif "st_union" in select_query:
        result = geo_df.dissolve().union
        if noisy_result:
            result = getNoisyPoints(minx, miny, maxx, maxy, geo_df, float(epsilon))
            result.dissolve().union
        
    else:
        result = ""
        print("ERROR: No geo spacial method found in SELECT-part.")
    print("Result: ")
    return result