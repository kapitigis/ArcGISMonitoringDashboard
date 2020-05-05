#-------------------------------------------------------------
# Name:       ArcGIS Stats extraction script 2
# Purpose:    Extracts data from ArcGIS Server log files and populates tables/feature classes in an EGDB.
# Author:     Keith Miller (keith.miller@kapiticoast.govt.nz)
# Date Created:    10/01/2020
# Copyright:   (c) Kapiti Coast District Council, Eagle Technologies
# ArcGIS Version:   10.7+
# Python Version:   3.6+
#--------------------------------

import os
import sys
import logging
import smtplib
import arcpy
import datetime
import requests
import json
from requests_ntlm import HttpNtlmAuth
import time
from calendar import timegm
from collections import Counter
from arcgis.gis import GIS

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
emailSubject = "ArcGIS Stats 2 extraction failure"
emailMessage = "The ArcGIS Stats 2 extraction has failed..."

# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

def log(message):
    if loggingEnabled:
        logger.info(message)


def mainFunction(logFilename,
                 serverURL,
                 portalUsername,
                 portalPassword,
                 serverUsername,
                 serverPassword,
                 serverHostname,
                 serverPort,
                 domainUsername,
                 domainPassword,
                 tokenURL,
                 fcStatsServicesStatus,
                 fcStatsServucesDown):

    # --------------------------------------- Start of code --------------------------------------- #

    try:
        # Parameter conversions
        currentDateTimeUTCRaw = datetime.datetime.utcnow()
        statDateUTC = currentDateTimeUTCRaw.strftime("%Y-%m-%d %H:%M:00 %p") # "2020-01-10 10:00:00 AM" format. Rounds down to the nearest minute.

        services = []
        servicesUp = []
        servicesDown = []

        if 'intgis' in serverURL:

            ### Find status of each service ###
            gis = GIS(serverURL, portalUsername, portalPassword)
            gis_servers = gis.admin.servers.list()
            server1 = gis_servers[0]

            # Get list of folders on server
            folders = server1.services.folders

            # Get list of all services in all folders
            for folder in folders:
                services += server1.services.list(folder=folder)
            
            log('Total services: ' + str(len(services)))

            # Find out which services (which should be running) are up/down
            for service in services:

                serviceName = service.properties["serviceName"]
                serviceConfiguredState = service.status["configuredState"]
                serviceRealTimeState = service.status["realTimeState"]

                if serviceConfiguredState == "STARTED":
                    if serviceRealTimeState == "STARTED":
                        servicesUp.append(serviceName)
                    else:
                        servicesDown.append({
                            "attributes" : {
                                "StatDateUTC": statDateUTC,
                                "Service": serviceName}
                            })

        elif 'publicgis' in serverURL:

            rawServerURL = "http://" + serverHostname + ":" + serverPort

            # Get a token
            token = getToken(rawServerURL, serverUsername, serverPassword)

            # Fetch list of folders on server            
            servicesURL = rawServerURL + '/arcgis/admin/services'
            params = {'token': token, 'f': 'json'}
            resp = requests.post(servicesURL, data=params)

            if resp.status_code != 200:
                log("Error while getting list of folders on server")
                sys.exit()

            folders = [''] + resp.json()['folders']
            # log(str(folders))

            # Get list of all services in all folders
            services = []
            for folder in folders:

                folderURL = rawServerURL + "/arcgis/admin/services/" + folder
                params = {'token': token, 'f': 'json'}
                resp = requests.post(folderURL, data=params)
                
                if resp.status_code != 200:
                    log("Error while getting list of services in folder '" + folder + "'")
                    sys.exit()

                servicesInFolder = resp.json()['services']

                # Loop through each service in the folder and find its status
                for service in servicesInFolder:

                    serviceName = service['serviceName'] + "." + service['type']

                    # Construct URL to stop or start service, then make the request                
                    if folder == "":
                        statusURL = rawServerURL + "/arcgis/admin/services/" + serviceName + "/status"
                    else:
                        statusURL = rawServerURL + "/arcgis/admin/services/" + folder + "/" + serviceName + "/status"

                    # log(statusURL)
                    resp = requests.post(statusURL, data=params)

                    if resp.status_code != 200:
                        log("Error while getting status of service '" + serviceName + "'")
                        sys.exit()

                    serviceConfiguredState = resp.json()['configuredState']
                    serviceRealTimeState = resp.json()['realTimeState']

                    if serviceConfiguredState == "STARTED":
                        if serviceRealTimeState == "STARTED":
                            servicesUp.append(serviceName)
                        else:
                            servicesDown.append({
                                "attributes" : {
                                    "StatDateUTC": statDateUTC,
                                    "Service": serviceName}
                                })

        log("Services up: " + str(len(servicesUp)))
        log("Services down: " + str(len(servicesDown)))
        log("Services down list: " + str(servicesDown))

        ##########################################################
        ### Post time-based data to ArcGIS Stats Feature Class ###
        ##########################################################

        # Generate portal token
        r = requests.post(tokenURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data = {"f": "json"})
        token = r.json()['token']

        ### Services Status ###

        # Set up feature service URL
        featureService = fcStatsServicesStatus
        addFeaturesURL = featureService + '/addFeatures'

        # Set up the data to post
        data = {
            "f": "json",
            "token": token,
            "features": json.dumps([{
                "attributes" : {
                    "StatDateUTC" : statDateUTC,
                    "ServicesUp" : len(servicesUp),
                    "ServicesDown": len(servicesDown),
                    "TotalServices": len(services)
                }
            }])
        }

        # Post data
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        r = requests.post(url=addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

        log(r.text)

        ### Services Down ###

        if len(servicesDown):

            # Send email
            if sendErrorEmail:
                sendEmail("Service(s) down on " + serverURL, str(servicesDown))

            # Set up feature service URL
            featureService = fcStatsServucesDown
            addFeaturesURL = featureService + '/addFeatures'

            # Set up the data to post
            data = {
                "f": "json",
                "token": token,
                "features": json.dumps(servicesDown)
            }

            # Post data
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            r = requests.post(url=addFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            log(r.text)


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

        if sendErrorEmail:
            emailMessage = emailFailureMessage + '\n' + '\n' + errorMessage
            sendEmail(emailFailureSubject, emailMessage)

    # If python error
    except Exception as e:
        raise
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

        if sendErrorEmail:
            emailMessage = emailFailureMessage + '\n' + '\n' + errorMessage
            sendEmail(emailFailureSubject, emailMessage)

# End of main function


# A function to generate a token given username, password and the adminURL.
def getToken(rawServerURL, username, password):

    tokenURL = rawServerURL + "/arcgis/admin/generateToken"
    params = {'username': username, 'password': password, 'client': 'requestip', 'f': 'json'}
    resp = requests.post(tokenURL, data=params)

    if resp.status_code != 200:
        log("Error while fetching tokens from admin URL. Please check the URL and try again.")
        sys.exit()

    # Extract the token
    token = resp.json()['token']       
    return token       
        

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
def sendEmail(emailSubject, emailMessage):

    # Send an email
    arcpy.AddMessage("Sending email...")
    log("Sending email...")

    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName, emailServerPort) 
    smtpServer.ehlo()
    smtpServer.starttls() 
    smtpServer.ehlo

    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)

    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage

    # Send the email and close the connection
    res = smtpServer.sendmail(emailUser, emailTo, body)

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

    mainFunction(*argv)

