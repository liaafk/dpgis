import geopandas as gpd
import diffprivlib
from idna import valid_contextj

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

def getNoisyDomain(raw_points, eps):
    minx, miny, maxx, maxy = raw_points.dissolve().total_bounds
    xsensitivity = maxx-minx
    ysensitivity = maxy-miny
    raw_points_x = raw_points['loc'].x
    raw_points_y = raw_points['loc'].y
    lap_x = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=xsensitivity, lower=minx, upper=maxx)
    lap_y = diffprivlib.mechanisms.LaplaceBoundedDomain(epsilon=eps, sensitivity=ysensitivity, lower=miny, upper=maxy)
    noisy_points_x = raw_points_x.apply(lambda val: lap_x.randomise(value=val))
    noisy_points_y = raw_points_y.apply(lambda val: lap_y.randomise(value=val))
    return noisy_points_x, noisy_points_y