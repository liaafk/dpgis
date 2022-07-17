import geopandas as gpd
import diffprivlib
import pandas as pd
from pandasql import sqldf
from shapely import geometry

def getQueryParts(query):
    query_parts = query.rsplit("FROM")
    return(query_parts)

def getQueryPoints(query, datapoint_attribute, conn):
    try:
        part_from = getQueryParts(query)[1]
    except:
            print("ERROR: Query doesn't contain 'FROM'")
            return
    print("Getting all points of query")
    try:
        raw_points_query = "SELECT "+ datapoint_attribute + " FROM " + part_from
    except:
        print("ERROR: SQL request wrong, probably wrong datapoint attribute name")
    raw_points = gpd.GeoDataFrame.from_postgis(raw_points_query, conn, datapoint_attribute)
    return raw_points

def getExtremePoints(raw_points):
    return raw_points.dissolve().total_bounds

def removeExtremePoints(raw_points, datapoint_attribute):
    print("Removing extreme points")
    minx, miny, maxx, maxy = getExtremePoints(raw_points)
    raw_points_x = raw_points[datapoint_attribute].x
    raw_points_y = raw_points[datapoint_attribute].y
    d = {'longitude': raw_points_x, 'latitude': raw_points_y}
    df= pd.DataFrame(d)
    df_no_extreme_x = df[~df['longitude'].isin([minx, maxx])]
    df_no_extreme_xy = df_no_extreme_x[~df_no_extreme_x['latitude'].isin([miny, maxy])]
    if df_no_extreme_xy.shape[0] < 0.25*df.shape[0]:
        gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    else:
        gdf = gpd.GeoDataFrame(
            df_no_extreme_xy, geometry=gpd.points_from_xy(df_no_extreme_xy.longitude, df_no_extreme_xy.latitude))
    gdf.rename_geometry(datapoint_attribute, inplace=True)
    return gdf

def getNoisyPoints(minx, miny, maxx, maxy, raw_points, eps, datapoint_attribute):
    print("Noising points")
    raw_points_x = raw_points[datapoint_attribute].x
    raw_points_y = raw_points[datapoint_attribute].y
    lap_x, lap_y = getLaplaceDistribution(minx, miny, maxx, maxy, eps)
    noisy_points_x = raw_points_x.apply(lambda val: lap_x.randomise(value=val))
    noisy_points_y = raw_points_y.apply(lambda val: lap_y.randomise(value=val))
    df = {"longitude": noisy_points_x, "latitude": noisy_points_y}
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']), crs="EPSG:4326")
    gdf.rename_geometry(datapoint_attribute, inplace=True)
    return gdf

def getLaplaceDistribution(minx, miny, maxx, maxy, eps):
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    return lap_x, lap_y

def noisy_sql_response(query, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result):
    # get points relevant to query
    points = getQueryPoints(query, datapoint_attribute, conn)
    # get extreme points
    minx, miny, maxx, maxy = getExtremePoints(points)
    # adding laplace noise
    lap_x, lap_y = getLaplaceDistribution(minx, miny, maxx, maxy, epsilon)

    if remove_extreme_points:
        points = removeExtremePoints(points, datapoint_attribute)

    geo_df = gpd.GeoDataFrame(points, geometry=datapoint_attribute, crs="EPSG:4326")
    if noisy_points:
        # point as geodf WITH noise
        geo_df = getNoisyPoints(minx, miny, maxx, maxy, points, float(epsilon), datapoint_attribute)

    select_query =  getQueryParts(query)[0].lower()
    if "st_envelope" or "st_extent" in select_query:
        result = geo_df.dissolve().total_bounds
        if noisy_result:
            print("Noising result")
            result = [lap_x.randomise(result[0]), lap_y.randomise(result[1]), lap_x.randomise(result[2]), lap_y.randomise(result[3])]
    
    elif "st_centroid" in select_query:
        result = geo_df.dissolve().centroid[0]
        if noisy_result:
            print("Noising result")
            result = [lap_x.randomise(result.x), lap_y.randomise(result.y)]

    elif "st_union" in select_query:
        result = geometry.Polygon([[p.x, p.y] for p in list(geo_df.geometry)])
        if noisy_result:
            print("Noising result")
            result = getNoisyPoints(minx, miny, maxx, maxy, geo_df, float(epsilon), datapoint_attribute)
            result = geometry.Polygon([[p.x, p.y] for p in list(result.geometry)])
        
    else:
        result = ""
        print("ERROR: No geo spacial method found in SELECT-part.")
    print("Result: ")
    return result