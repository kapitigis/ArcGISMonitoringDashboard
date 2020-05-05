REM ----- ArcGIS Stats 2 extract -----
REM
REM You will need to amend this file so that it reflects your environment.
REM This will mean amending the path to the Python 3.6 exe, where your script lives, and also server details, usernames and passwords.
REM
REM Here is a list detailing what each of the parameters are:
REM    Log filename
REM    H Portal URL (e.g. https://subdomain.yourdomain.com/arcgis)
REM    I Portal username which will be used to grab data from the ArcGIS Python API (if used)
REM    J Portal password for above user
REM    A ArcGIS Server admin username
REM    B ArcGIS Server admin password
REM    C ArcGIS Server hostname (e.g. svr-gisapp.yourdomain.com)
REM    D ArcGIS Server port (e.g. 6080)
REM    E ArcGIS Portal username (for Windows single sign on it will in the format domain\username)
REM    F ArcGIS Portal password
REM    G ArcGIS generate token URL (e.g. https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken)
REM    URL for Feature Class containing Services Status
REM    URL for Feature Class containing Services Down
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "C:\Scripts\ArcGIS_Stats\generate_stats_2.py" ^
    "intGIS_Stats_2.log" ^
    "https://intgis.yourdomain.com/arcgis" ^
    "prod_portal_username" ^
    "prod_portal_password" ^
    "" ^
    "" ^
    "" ^
    "" ^
    "preprod_portal_username" ^
    "preprod_portal_password" ^
    "https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken" ^
    "https://ppintgis.yourdomain.com/arcgis_server/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/7" ^
    "https://ppintgis.yourdomain.com/arcgis_server/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/8" ^
