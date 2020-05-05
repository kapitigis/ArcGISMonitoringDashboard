REM ----- ArcGIS Stats extract -----
REM
REM You will need to amend this file so that it reflects your environment.
REM This will mean amending the path to the Python 2.7 exe, where your script lives, and also server details, usernames and passwords.
REM
REM Here is a list detailing what each of the parameters are:
REM    Log filename
REM    Short time period (e.g. 5 minutes)
REM    Mid time period - currently unused
REM    Long time period - currently unused
REM    A ArcGIS Server admin username
REM    B ArcGIS Server admin password
REM    C ArcGIS Server hostname (e.g. svr-gisapp.yourdomain.com)
REM    D ArcGIS Server port (e.g. 6080)
REM    E ArcGIS Portal username (for Windows single sign on it will in the format domain\username)
REM    F ArcGIS Portal password
REM    G ArcGIS generate token URL (e.g. https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken)
REM    URL for Feature Class containing Stats Per Time Period
REM    URL for Feature Class containing Errors
REM    URL for Feature Class containing Warnings
REM    URL for Feature Class containing Services Requested
REM    URL for Feature Class containing Layers Drawn
REM    URL for Feature Class containing Average Layer Draw Time
REM    URL for Feature Class containing Services Requested by User - currently unused
C:\Python27\ArcGIS10.7\python "C:\Scripts\ArcGIS_Stats\generate_stats.py" ^
    "intGIS_Stats.log" ^
    "5" ^
    "30" ^
    "720" ^
    "prod_server_admin_username" ^
    "prod_server_admin_password" ^
    "svr-gisapp.yourdomain.com" ^
    "6080" ^
    "preprod_portal_username" ^
    "preprod_portal_password" ^
    "https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/0" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/1" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/2" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/3" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/4" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/5" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/6" ^
