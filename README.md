# dpgis

This library provides a proxy based on Differential Privacy (DP) for PostGIS requests. The proxy provides two options for making a reqest more private. 

The first solution uses the Local Differential Privacy (LDP) algorithm as stated in [1]. LDP means that on the point from an end user Differential Privacy is applied locally and then send to the server. In our case it is not aggregated from clients, but we get the points from querying the Database and appling LDP to each point. LDP insures that the result is differentialy private.

The second solution is Lalpace noice mechanism. We are giving the freedom that the Laplace noise is applied whether only to the raw points or to the result (e.g. result of Bounding Box) or to both options. But we have no evidence that this is truly Diferrentialy Private.


## How to use

Create a conda environment and install all necessary packages by running the following commands:

``` bash
conda create --name dpgis
conda activate dpgis
pip install -r requirements.txt
```

Within `config_file.py` you can define

```
QUERY: [<list of queries to be run>]
DATAPOINT_ATTRIBUTE: '<name of the PostGIS database column containing geometry data as a String>'
EPSILON: [<privacy parameter epsilon for Laplace/square mechanism as a float>]
NOISY_POINTS: [<boolean, whether to use Laplace noise>]
LOCAL_DP: [<boolean, whether to use the square mechanism (LDP)>]
```

Be aware that only one of NOISY_POINTS and LOCAL_DP can be [True] at a time.

To connect with your PostGIS database, configure the following in `database.ini`:

```
[postgresql]
host: <the location of your PostgreSQL server>
database: <the name of your PostGIS database>
user: <username to connect to your database>
password: <password to connect to your database>
```

Once configuring is finished, the proxy is ready to use by running the following command:

``` bash
python main.py
```

To see examples of queries currently supported by the proxy, see `query_list.txt`.

[1] D. Hong, W. Jung and K. Shim, "Collecting Geospatial Data with Local Differential Privacy for Personalized Services," 2021 IEEE 37th International Conference on Data Engineering (ICDE), 2021, pp. 2237-2242, doi: 10.1109/ICDE51399.2021.00230.