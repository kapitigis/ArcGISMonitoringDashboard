Instructions for setting up ArcGIS Monitoring Dashboard
=======================================================

These instructions describe how I set up the dashboard for my working environment. I set up two monitoring dashboards - one to monitor our internal GIS (intGIS), and one for external GIS (publicGIS). The bulk of the set up was done on our pre-production (ppintGIS) environment, to keep any processing overheads away from the production servers. However, these overheads probably aren't that significant and so production servers could likely be used to host the monitoring if that's all you have.

Both my pre-production GIS environment and internal (production) GIS environment are federated servers running ArcGIS 10.7.1.

Your environment will likely differ from mine, and you'll have to adapt these scripts to work in your environment. You may only need to monitor one Enterprise Server for example. Also, it may be possible to host the Feature Layers and data in ArcGIS Online but I've not tried to do this. You'd still have to have the Python scripts running somewhere in your environment, and then change the batch files so that they write to AGOL. As I say, I've not tried it but would be keen to hear if anyone has success in doing this.

I've included a Powerpoint presentation (in the /Docs folder) that I gave to the New Zealand ESRI Virtual User Conference in April 2020 which contains a diagram and screenshots of the dashboards which may come in handy. Feedback from that presentation asking for copies of the code / how to set up the dashboards is why I've written this documentation. :)

Here goes with the instructions...

Import Feature Classes
----------------------
Use the ArcGIS tool 'Import XML Workspace Document'
- Choose the Enterprise Geodatabase you want to add these feature classes to (I tried to use a File Geodatabase but that didn't work for me)
- Import the file /FeatureClasses/FEATURECLASSES.XML
- Set the Import Options to be SCHEMA_ONLY
- Leave the Configuration Keyword field blank

Running this tool should create the necessary feature classes in the geodatabase.

Publish Feature Layer
---------------------

- Open the ArcMap document /MapDocuments/ArcGISStatsIntGIS.mxd
- Fix the data source of each of the layers so that they point to your newly created feature classes
- Publish the map document as a Map Service (File > Share As > Service). I published it onto my PreProduction Enterprise Portal into a new folder called Stats. This should create a new service called Stats/ArcGISStatsIntGIS (if you haven't changed the name), comprising of one layer for each feature class.
- In your web browser open the ArcGIS Server Manager for the server you published the service to, and click on the service you've just published.
- On the Capabilities screen, tick the 'Feature Access' tickbox and click the Save and Restart button. This allows you to add data to the service via the /addFeatures method - something that the Python script will be doing. If you click on the REST URL, you will see the feature layers that the Python script will populate.

Configure Feature Layer within Portal
-------------------------------------

- Find your newly created Feature Layer within Portal. This should automatically have been created in Portal when you enabled Feature Access in the steps above. Our Portal is federated with the Server. I believe that's why the Feature Layer is automatically created in Portal or not. If not, then I'm guessing the Feature Layer could be manually created.
- Share this layer - I've set it to be shared to Everyone, but it's possible that it could just be shared with your organisation. Our preproduction and internal servers are behind a firewall so Public in our case is effectively just the organisation.
- Make a note of the id of the Feature Layer. It will be in the Feature Layer's URL (and will look something like 8585f8f75c074a5bb293f041fd9220ef). You'll need this id later on.
- On the Feature Layer page you should see a list of the layers within the Feature Layer. For each of these layers do the following steps:
  - Click Open In and choose Open in Map Viewer
  - A webmap will open showing this one layer. Move your mouse over the layer in the Contents pane and click on the three horizontal dots.
  - Choose Refresh Interval and set it to be 1 minute.
  - Click the three dots again if necessary and choose Save Layer

Add Python scripts & batch files
--------------------------------

Choose the machine that will run the scheduled tasks / batch files / python scripts. This machine has to have Python 2.7 and 3.6 installed onto it (i.e. one with both ArcMap and ArcGIS Pro installed onto it). My server which runs the ArcGIS Data Store is the one I used. Ideally it should be a server which is constantly running and not a desktop machine / laptop which may well be shut down occassionally. I believe that there can be problems if installing these desktop apps onto the ArcGIS Server machine itself however.

There are 3 scripts and associated batch files:
- **generate_stats.py** (run by intGIS_Stats.bat and publicGIS_Stats.bat) - This is the main python script which does the bulk of the log processing and writing to feature layers. This runs on Python 2.7.
- **generate_stats_2.py** (run by intGIS_Stats_2.bat and publicGIS_Stats_2.bat) - This is an additional python script which works out if the services are up and running or not. I initially wrote it for our internal GIS and uses the ArcGIS Python API (which requires python 3.6). For our public GIS I was unable to use the ArcGIS Python API and so I had to resort to grabbing the information in a different way. Both ways are visible in this file's code. You will likely have to adapt this code for your own environment.
- **clean_up.py** (run by clean_up.bat) - This is a fairly simple script which removes old data from the feature layers.

**NB** See the Usernames and Passwords section below as this may come in handy when working out which account details to use in the batch files.

Steps to install files:
- Copy the files and empty Logs folder from the /PythonAndBatchFiles folder into your desired location on your chosen server.
- Edit the parameters in each .bat file in turn, following the guidance within each file.

Once you've changed the parameters in the batch files, it's worth running the batch files manually (using a Windows user with the correct permissions) to check that they run as expected (i.e. pull data from the log files and write data to the Feature layers). Log files are generated by the Python scripts and can be found in the Logs folder. Additional log entries can be added to the python scripts by using the log() function.

Set up scheduled tasks 
----------------------

- On the server which contains your Python scripts and batch files, open the Windows Task Scheduler app.
- Create a new Basic Task to run the intGIS_Stats.bat file every 5 minutes. Make sure that the task is run by a Windows user with appropriate permissions to run the batch files & Python script.
- Repeat as necessary for the other batch files. (The clean up batch file only needs to be run once a day).

**NB** Example images of the scheduled tasks can be found in the /ScheduledTasks folder.

Create Dashboard
----------------

- In the folder /Dashboard, open the file Data.json in your favourite text editor.
- Search for the text 8585f8f75c074a5bb293f041fd9220ef and replace this with the id of your Feature Layer that you got earlier. This will then point the dashboard to the Feature Layer that you created.
- Choose Select All and then Copy.
- In your Enterprise Portal (pre-production in my case), create an empty Operations Dashboard.
- Then go to https://ago-assistant.esri.com/ and log into your Portal using the same user that owns the Operation Dashboard you just created.
- Choose 'View an item's JSON' from the 'I want to...' dropdown.
- Still in ago-assistant, click on the dashboard item in the left column that you've just created. The right column should show 2 panes on JSON - Description and Data
- In ago-assistant, click on the Edit JSON button on the Data pane and paste over the top of the existing Data JSON that is present in ago-assistant. (I've included my Description.json but you most likely won't need that).
- Click the Save button on the Data pane to save the JSON.
- View the Dashboard in Portal and it should work! OK, it probably won't work first time, but hopefully you'll get there without too many hassles.

Usernames and passwords
-----------------------

Unfortunately, the batch files that kick off the python scripts require usernames, passwords and URLs be saved in the batch files themselves. So be careful where you put these files. Here's a rundown of what you'll need to use.

## intGIS_Stats.bat and publicGIS_Stats.bat
- ArcGIS Server
    - A Server Admin username
    - B Server Admin password
    - C Server hostname (e.g. svr-gisapp.yourdomain.com)
    - D Server port (e.g. 6080)
- ArcGIS Portal (pre-production)
    - E Username for ArcGIS Portal account used to run and manage the GIS services. This user will need to have rights to be able to write data to the Feature Layers. If Windows Single Sign on is used then this will likely be in the format domain\username.
    - F Password for above ArcGIS Portal account
    - G Portal generate token URL (e.g. https://ppintgis.yourdomain.com/arcgis/sharing/rest/generateToken)

## intGIS_Stats_2.bat and publicGIS_Stats_2.bat
- ArcGIS Portal (internal)
    - H URL of Portal that you are getting data for (e.g. https://subdomain.yourdomain.com/arcgis)
    - I Portal username which will be used to grab data from the ArcGIS Python API (if used)
    - J Portal password for above user
- ArcGIS Server
    - A As above
    - B As above
    - C As above
    - D As above
- ArcGIS Portal (pre-production)
    - E As above
    - F As above
    - G As above

## clean_up.py and clean_up.bat
- ArcGIS Portal (pre-production)
    - E As above
    - F As above
    - G As above

Good luck!

Contact: keith.miller@kapiticoast.govt.nz