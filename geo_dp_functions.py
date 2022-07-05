import geopandas as gpd

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
    part_from = getQueryParts(query)[1]
    print("Getting all points of query...")
    raw_points_query = "SELECT "+ datapoint_attribute + " FROM " + part_from
    raw_points = gpd.GeoDataFrame.from_postgis(raw_points_query, conn, geom_col='loc' )
    return(raw_points)