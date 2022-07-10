import geopandas as gpd
import diffprivlib
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
    return(raw_points)

def getExtremePoints(raw_points):
    return raw_points.dissolve().total_bounds

def removeExtremePoints(raw_points):
    minx, miny, maxx, maxy = getExtremePoints(raw_points)
    no_extreme_x = raw_points[raw_points['longitude'] not in [minx, maxx]]
    no_extreme_xy = no_extreme_x[no_extreme_x['latitude'] not in [miny, maxy]]
    return no_extreme_xy

def getNoisyDomain(raw_points, eps):
    minx, miny, maxx, maxy = getExtremePoints(raw_points)
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    raw_points_x = raw_points['loc'].x
    raw_points_y = raw_points['loc'].y
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    noisy_points_x = raw_points_x.apply(lambda val: lap_x.randomise(value=val))
    noisy_points_y = raw_points_y.apply(lambda val: lap_y.randomise(value=val))
    return noisy_points_x, noisy_points_y

def dp_sql_response(query, datapoint_attribute, conn, epsilon):
    query_points = getQueryPoints(query, datapoint_attribute, conn)
    # löschen query_points = ....
    noisy_geo_df = getNoisyDomain(query_points, epsilon)
    response = sqldf(getQueryPoints(query, datapoint_attribute, conn)[0], noisy_geo_df)
    # 'select' part vom request auf noisy_geo_df anwenden
    return response