# dpgis

This ist the code to run the local differential privacy (LDP) proxy for PostGIS. We implement the LDP algorithm as stated in [collecting].

## How to use

Create a conda environment and install all necessary packages by running the following commands:

``` bash
conda create --name dpgis
conda activate dpgis
pip install -r requirements.txt
```

Within `config_file.py` you can define

QUERY: list of queries to be run
DATAPOINT_ATTRIBUTE: the name of the PostGIS database column containing geometry data
EPSILON: 
NOISY_POINTS: Whether to use Laplace noise
LOCAL_DP: Whether to use the square mechanism (LDP)

Be aware that only one of NOISY_POINTS and LOCAL_DP can be [True] at a time.

To connect with your PostGIS database, configure the following in `database.ini`:

host: the location of your PostgreSQL server
database: the name of your PostGIS database
user: username to connect to your database
password: password to connect to your database

Once configuring is finished, the proxy is ready to use by running the following command:

``` bash
python main.py
```

To see examples of queries currently supported by the proxy, see `query_list.txt`.