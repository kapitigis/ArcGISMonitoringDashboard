#-------------------------------------------------------------
# Name:       ArcGIS Stats extraction
# Purpose:    Extracts data from ArcGIS Server log files and populates tables/feature classes in an EGDB.
# Author:     Keith Miller (keith.miller@kapiticoast.govt.nz)
# Date Created:    10/01/2020
# Copyright:   (c) Kapiti Coast District Council, Eagle Technologies
# ArcGIS Version:   10.0+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import datetime
import requests
import httplib
import urllib
import json
from requests_ntlm import HttpNtlmAuth # This module is only needed when using Windows single sign on into ArcGIS Portal
import time
from calendar import timegm
from collections import Counter

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables

# Logging
loggingEnabled = True # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")

# Email logging
sendErrorEmail = "false"
emailServerName = "smtp.yourdomain.com" # e.g. smtp.gmail.com
emailServerPort = 25 # e.g. 25
emailUser = "gissupport@yourdomain.com"
emailPassword = "password"
emailTo = "user.name@yourdomain.com"
emailSubject = "ArcGIS Stats extraction failure"
emailMessage = "The ArcGIS Stats extraction has failed..."

# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

def log(message):
    if loggingEnabled:
        logger.info(message)

# Start of main function
def mainFunction(logFilename,
                 shortTimePeriod,
                 midTimePeriod,
                 longTimePeriod,
                 serverUsername,
                 serverPassword,
                 serverHostname,
                 serverPort,
                 domainUsername,
                 domainPassword,
                 tokenURL,
                 fcStatsPerTimePeriodURL,
                 fcErrorsURL,
                 fcWarningsURL,
                 fcServicesRequestedURL,
                 fcLayersDrawnURL,
                 fcAvgLayerDrawTimeURL,
                 fcServicesRequestedByUserURL):

    # --------------------------------------- Start of code --------------------------------------- #

    try:
        # Parameter conversions
        shortTimePeriod = int(shortTimePeriod)
        midTimePeriod = int(midTimePeriod)
        longTimePeriod = int(longTimePeriod)
        serverPort = int(serverPort)

        currentDateTimeUTCRaw = datetime.datetime.utcnow()
        statDateUTC = currentDateTimeUTCRaw.strftime("%Y-%m-%d %H:%M:00 %p") # "2020-01-10 10:00:00 AM" format. Rounds down to the nearest minute.

        periodStartUTC = time.strptime(statDateUTC, "%Y-%m-%d %H:%M:%S %p")
        periodStartUTC = timegm(periodStartUTC) * 1000
        timePeriod = shortTimePeriod * 60 * 1000 # In milliseconds
        periodEndUTC = (periodStartUTC - timePeriod) + 1 # add one millisecond so no overlap between time periods

        ########################################################################
        ### Query logs to find number of layers accessed in last time period ###
        ########################################################################

        # Set server security details
        # Get a token
        token = getToken(serverUsername, serverPassword, serverHostname, serverPort)
        if token == "":
            log("Could not generate a token with the username and password provided")
            return
        
        # Construct URL to query the logs
        noOfLogMessagesPerPage = 10000
        logQueryURL = "/arcgis/admin/logs/query"
        logFilter = "{'services':'*','server':'*','machines':'*'}"
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

        # Request logs from server. These come in batches of up to 10,000 messages at a time, so need to use loop to make sure we get all the messages.
        receivedAllLogs = False
        serverLogs = []
        startTime = periodStartUTC
        endTime = periodEndUTC

        while not receivedAllLogs:

            # Set parameters
            log('startTime: ' + str(startTime))
            log('endTime: ' + str(endTime))
            params = urllib.urlencode({'level': 'FINE', 'startTime': startTime, 'endTime': endTime, 'filter':logFilter, 'token': token, 'pageSize': noOfLogMessagesPerPage, 'f': 'json'})

            # Connect to URL and post parameters    
            httpConn = httplib.HTTPConnection(serverHostname, serverPort)
            httpConn.request("POST", logQueryURL, params, headers)

            # Read response
            response = httpConn.getresponse()
            if (response.status != 200):
                httpConn.close()
                log("Error while querying logs")
                return

            data = response.read()
            # log(data)

            # Check that data returned is not an error object
            if not assertJsonSuccess(data):
                log("Error returned by operation " + data)
                break

            # Deserialize response into Python object
            dataObj = json.loads(data)
            httpConn.close()

            serverLogs += dataObj["logMessages"]

            if dataObj["hasMore"]:

                # Find date of oldest log message retrieved
                oldestLogDateUTC = dataObj["logMessages"][noOfLogMessagesPerPage -1]["time"]
                startTime = oldestLogDateUTC - 1 # Subtract one millisecond so we don't get any repeated logs between the batches.
            else:
                log('Received all logs')
                receivedAllLogs = True

        # Need these variables to calculate average draw time for an ExportMapImage call
        layersDrawn = 0
        totalDrawTime = 0
        servicesRequested = 0
        avgDrawTime = 0
        errors = 0
        warnings = 0
        errorsDetails = []
        warningsDetails = []
        servicesDetails = []
        layersDrawnDetails = []
        layersDrawnTimeDetails = []

        log('No of messages: ' + str(len(serverLogs)))

        # Sort server logs by time (ascending)
        serverLogs.sort(key=lambda k: k["time"]) 

        # Iterate over logMessages
        for item in serverLogs:

            if item["code"] == 9029 and not item["message"].endswith('Stats/ArcGISStatsIntGIS/FeatureServer'): # 9029 == Service requested
                servicesRequested += 1
                servicePos = item["message"].find("Service: ")
                serviceName = item["message"][servicePos + len("Service: "):]
                servicesDetails.append(serviceName)

            if item["message"] == "End ExportMapImage":
                layersDrawn +=1
                totalDrawTime += float(item["elapsed"])
                layersDrawnDetails.append(item["source"])

                foundLayer = False
                for ld in layersDrawnTimeDetails:
                    if ld["layer"] == item["source"]:
                        foundLayer = True
                        ld["totalLayerDrawTime"] += float(item["elapsed"])
                        ld["layerCount"] += 1

                if not foundLayer:
                    layersDrawnTimeDetails.append({"layer": item["source"], "totalLayerDrawTime": float(item["elapsed"]), "layerCount": 1})

            if item["type"] == "SEVERE":
                errors += 1
                errorsDetails.append({
                    "attributes" : {
                        "StatDateUTC": statDateUTC,
                        "LogDateUTC": item["time"],
                        "Message": item["message"],
                        "Source": item["source"],
                        "Code": item["code"],
                        "GISUser": item["user"]}
                    })


            if item["type"] == "WARNING":
                warnings += 1
                warningsDetails.append({
                    "attributes" : {
                        "StatDateUTC": statDateUTC,
                        "LogDateUTC": item["time"],
                        "Message": item["message"],
                        "Source": item["source"],
                        "Code": item["code"],
                        "GISUser": item["user"]}
                    })

        log("Layers requested: " + str(servicesRequested))
        log("Total number of draws found in logs: " + str(layersDrawn))
        log("Errors: " + str(errors))
        log("Warnings: " + str(warnings))

        if layersDrawn != 0:
            avgDrawTime = 1.0 * (totalDrawTime / layersDrawn)
            log("Average draw time: " + str(avgDrawTime) + " seconds")


        ##########################################################
        ### Post time-based data to ArcGIS Stats Feature Class ###
        ##########################################################

        # Generate portal token
        # The correct authorisation method needs to be used here. I've used HttpNtlmAuth as that works with Windows single sign on to ArcGIS Portal.
        # For more info see https://requests.readthedocs.io/en/master/user/authentication/
        r = requests.post(tokenURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data = {"f": "json"})
        token = r.json()['token']

        ### General stats ###

        # Set up feature service URL
        featureService = fcStatsPerTimePeriodURL
        addFeaturesURL = featureService + '/addFeatures'

        # Set up the data to post
        data = {
            "f": "json",
            "token": token,
            "features": json.dumps([{
                "attributes" : {
                    "StatDateUTC" : statDateUTC,
                    "ServicesRequested" : servicesRequested,
                    "LayersDrawn": layersDrawn,
                    "AvgLayerDrawTime": avgDrawTime,
                    "Errors" : errors,
                    "Warnings" : warnings
                }
            }])
        }

        # Post data
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

        # log(r.text)

        ### Errors ###

        if errors > 0:
    
            # Set up feature service URL
            featureService = fcErrorsURL
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(errorsDetails)
            }

            # Post data
            r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            # log(r.text)

        ### Warnings ###

        if warnings > 0:

            # log(warningsDetails)

            # Set up feature service URL
            featureService = fcWarningsURL
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(warningsDetails)
            }

            # Post data
            r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            # log(r.text)

        ### Service Request Details ###

        # Construct list of services and how many times they were requested
        servicesAttributes = []
        i = 0
        for service in Counter(servicesDetails).keys():
            servicesAttributes.append({
                "attributes" : {
                    "StatDateUTC": statDateUTC,
                    "Service": service,
                    "ShortTimePeriod": Counter(servicesDetails).values()[i]}
                })
            i = i + 1

        # log(str(servicesAttributes))

        servicesDetails = sorted(servicesAttributes, key=lambda k : k['attributes']['ShortTimePeriod'], reverse=True)
        # log(str(servicesDetails))

        if len(servicesDetails) > 0:

            # Set up feature service URL
            featureService = fcServicesRequestedURL
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(servicesDetails)
            }

            # Post data
            r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            # log(r.text)

        ### Layers Drawn Details ###

        # Construct list of layers and how many times they were drawn
        layersDrawnAttributes = []
        i = 0
        for layer in Counter(layersDrawnDetails).keys():
            layersDrawnAttributes.append({
                "attributes" : {
                    "StatDateUTC": statDateUTC,
                    "Layer": layer,
                    "ShortTimePeriod": Counter(layersDrawnDetails).values()[i]}
                })
            i = i + 1

        layersDrawnDetails = sorted(layersDrawnAttributes, key=lambda k : k['attributes']['ShortTimePeriod'], reverse=True)

        if len(layersDrawnDetails) > 0:

            # Set up feature service URL
            featureService = fcLayersDrawnURL
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(layersDrawnDetails)
            }

            # Post data
            r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            # log(r.text)

        ### Average Layer Draw Times ###

        if len(layersDrawnTimeDetails) > 0:

            # Find average draw times for each layer drawn
            avgDrawTimeAttributes = []
            for lyr in layersDrawnTimeDetails:
                avgDrawTimeAttributes.append({
                    "attributes" : {
                        "StatDateUTC": statDateUTC,
                        "Layer": lyr["layer"],
                        "ShortTimePeriod": lyr["totalLayerDrawTime"] / lyr["layerCount"]}
                })

            # Set up feature service URL
            featureService = fcAvgLayerDrawTimeURL
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(avgDrawTimeAttributes)
            }

            # Post data
            r = requests.post(url = addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            # log(r.text)

        # --------------------------------------- End of code --------------------------------------- #  
            
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':

            # Return the output if there is any
            if output:
                arcpy.SetParameterAsText(1, output)

        # Otherwise return the result          
        else:
            # Return the output if there is any
            if output:
                return output      

        # Logging
        if loggingEnabled:

            # Log end of process
            logger.info("Process ended")
            logger.info("***************")

            # Remove file handler and close log file            
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        pass

    # If arcpy error
    except arcpy.ExecuteError:           

        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)   
        arcpy.AddError(errorMessage)           

        # Logging
        if loggingEnabled:

            # Log error          
            logger.error(errorMessage)

            # Log end of process
            logger.info("Process ended")
            logger.info("***************")

            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)

        if (sendErrorEmail == "true"):

            # Send email
            sendEmail(errorMessage)

    # If python error
    except Exception as e:
        errorMessage = ""

        # Build and show the error message
        for i in range(len(e.args)):

            if (i == 0):
                try:
                    errorMessage = unicode(e.args[i]).encode('utf-8')
                except Exception:
                    errorMessage = 'Unable to encode error message component'
            else:
                try:
                    errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
                except Exception:
                    errorMessage = 'Unable to encode error message component'

        arcpy.AddError(errorMessage)              

        # Logging
        if loggingEnabled:

            # Log error            
            logger.error(errorMessage)

            # Log end of process
            logger.info("Process ended")
            logger.info("***************")

            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)

        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)            

# End of main function


# A function to generate a token given username, password and the adminURL.
def getToken(username, password, serverName, serverPort):

    tokenURL = "/arcgis/admin/generateToken"
    
    # URL-encode the token parameters
    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print("Error while fetching tokens from admin URL. Please check the URL and try again.")
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return
        
        # Extract the toke from it
        token = json.loads(data)       
        return token['token']            
        

# A function that checks that the input JSON object is not an error object.    
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print("Error: JSON object returns an error. " + str(obj))
        return False
    else:
        return True

# Start of set logging function
def setLogging(logFile):

    # Create a logger
    logger = logging.getLogger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)

    # Setup log message handler
    logMessage = logging.FileHandler(logFile)

    # Setup the log formatting
    logFormat = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s", "%d/%m/%Y - %H:%M:%S")

    # Add formatter to log message handler
    logMessage.setFormatter(logFormat)

    # Add log message handler to logger
    logger.addHandler(logMessage) 

    return logger, logMessage

# End of set logging function


# Start of send email function
def sendEmail(message):

    # Send an email
    arcpy.AddMessage("Sending email...")

    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName, emailServerPort) 
    smtpServer.ehlo()
    smtpServer.starttls() 
    smtpServer.ehlo

    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)

    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage + '\n' + '\n' + message

    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, body)    

# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':

    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))

    logFilename = argv[0]
    logFile = os.path.join(os.path.dirname(__file__), "Logs", logFilename)
    print(logFile)

    # Logging
    if loggingEnabled:

        # Setup logging
        logger, logMessage = setLogging(logFile)

        # Log start of process
        logger.info("***************")
        logger.info("Process started")

    # Setup the use of a proxy for requests
    if (enableProxy == "true"):

        # Setup the proxy
        proxy = urllib2.ProxyHandler({requestProtocol : proxyURL})
        openURL = urllib2.build_opener(proxy)

        # Install the proxy
        urllib2.install_opener(openURL)

    mainFunction(*argv)
