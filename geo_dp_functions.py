import geopandas as gpd
import numpy as np
import diffprivlib
import pandas as pd
from local_dp import square_mechanism

# dividing the query into the SELECT- and FROM-part
def getQueryParts(query):
    query_parts = query.rsplit("FROM")
    return(query_parts)

# interquartile range method to determine q1 and q3
def outliers_iqr(ys):
    quartile_1, quartile_3 = np.percentile(ys, [25, 75])
    iqr = quartile_3 - quartile_1
    return quartile_1 - (iqr * 1.5), quartile_3 + (iqr * 1.5)

# get points affected by query
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

# getting the extreme points of a GeoDataFrame
def getExtremePoints(raw_points):
    return raw_points.dissolve().total_bounds

# removing outliers of a GeoDataFrame using iqr
def removeOutliers(raw_points, datapoint_attribute):
    raw_points_x = raw_points[datapoint_attribute].x
    raw_points_y = raw_points[datapoint_attribute].y
    d = {'longitude': raw_points_x, 'latitude': raw_points_y}
    df= pd.DataFrame(d)
    lowerx, upperx = outliers_iqr(df['longitude'].values)
    lowery, uppery = outliers_iqr(df['latitude'].values)
    df_no_extreme_x = df[df['longitude'].between(lowerx, upperx)]
    df_no_extreme_xy = df_no_extreme_x[df_no_extreme_x['latitude'].between(lowery, uppery)]
    gdf = gpd.GeoDataFrame(
        df_no_extreme_xy, geometry=gpd.points_from_xy(df_no_extreme_xy.longitude, df_no_extreme_xy.latitude))
    gdf.rename_geometry(datapoint_attribute, inplace=True)
    return gdf

# add noise to all points of a GeoDataFrame
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

# getting the Laplace distribution
def getLaplaceDistribution(minx, miny, maxx, maxy, eps):
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    return lap_x, lap_y

# getting the noisy response of a SQL query containing a PostGIS function
# possible PostGIS functions: ST_ENVELOPE, ST_EXTENT, ST_CENTROID, ST_UNION
def noisy_sql_response(query, datapoint_attribute, conn, epsilon, laplace_points, laplace_result, local_dp):
    # get points relevant to query
    points = getQueryPoints(query, datapoint_attribute, conn)
    # removing outliers
    points = removeOutliers(points, datapoint_attribute)
    # getting extreme points
    minx, miny, maxx, maxy = getExtremePoints(points)
    # adding laplace distribution
    lap_x, lap_y = getLaplaceDistribution(minx, miny, maxx, maxy, epsilon)

    geo_df = gpd.GeoDataFrame(points, geometry=datapoint_attribute, crs="4326")
    if laplace_points:
        # adding noise to all points in the GeoDataFrame
        geo_df = getNoisyPoints(minx, miny, maxx, maxy, points, float(epsilon), datapoint_attribute)
    elif local_dp:
        geo_df = square_mechanism(geo_df, float(epsilon), datapoint_attribute)
    # finding PostGIS function in SELECT-part
    select_query =  getQueryParts(query)[0].lower()
    if "st_envelope" in select_query or "st_extent" in select_query:
        # returning the bounding box of the GeoDataFrame
        result = geo_df.dissolve().total_bounds
        if laplace_result:
            # adding noise to the bounding box
            print("Noising result")
            result = [lap_x.randomise(result[0]), lap_y.randomise(result[1]), lap_x.randomise(result[2]), lap_y.randomise(result[3])]
    
    elif "st_centroid" in select_query:
        # returning the center of the GeoDataFrame
        result = geo_df.to_crs(epsg=4326).dissolve().centroid[0]
        if laplace_result:
            # adding noise to the center point
            print("Noising result")
            result = [lap_x.randomise(result.x), lap_y.randomise(result.y)]

    elif "st_union" in select_query:
        # returning the points of  the GeoDataFrame without overlap
        result = [[p.x, p.y] for p in list(geo_df.geometry)]
        if laplace_result:
            # adding noise to each point in the GeoDataFrame
            print("Noising result")
            result = getNoisyPoints(minx, miny, maxx, maxy, geo_df, float(epsilon), datapoint_attribute)
            result = [[p.x, p.y] for p in list(result.geometry)]
    else:
        result = "-"
        print("ERROR: No geo spacial method found in SELECT-part.")
    print("Result: ")
    return result