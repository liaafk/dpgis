import geopandas as gpd

def testquery(conn, sql):
    df = gpd.GeoDataFrame.from_postgis(sql, conn, geom_col='loc' )
    return(df)
    
def ANON_ST_Envelope(cur, query):
    cur.execute(query)
    query_results = cur.fetchall()

    return(query_results)
    