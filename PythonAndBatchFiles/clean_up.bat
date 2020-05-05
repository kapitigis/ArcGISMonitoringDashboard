REM ----- ArcGIS Stats extract -----
REM
REM Clean up script to remove old entries from the Feature Layers after x days
REM
REM Here is a list detailing what each of the parameters are:
REM    Log filename
REM    Number of days stats are to be kept
REM    E ArcGIS Portal username (for Windows single sign on it will in the format domain\username)
REM    F ArcGIS Portal password
REM    G ArcGIS generate token URL (e.g. https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken)
REM    Multiple URLs for Feature Classes which are to have their stats trimmed
C:\Python27\ArcGIS10.7\python "C:\Scripts\ArcGIS_Stats\clean_up.py" ^
    "clean_up.log" ^
    "30" ^
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
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/7" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsIntGIS/FeatureServer/8" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/0" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/1" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/2" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/3" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/4" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/5" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/6" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/7" ^
    "https://ppintgis.yourdomain.com/arcgisadm/rest/services/Stats/ArcGISStatsPublicGIS/FeatureServer/8" ^
