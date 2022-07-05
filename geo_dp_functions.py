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