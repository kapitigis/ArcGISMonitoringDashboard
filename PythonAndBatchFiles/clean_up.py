#-------------------------------------------------------------
# Name:       ArcGIS Stats clean up
# Purpose:    Removes any stats data which is more than 30 days old
# Author:     Keith Miller (keith.miller@kapiticoast.govt.nz)
# Date Created:    07/02/2020
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
from requests_ntlm import HttpNtlmAuth
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
emailSubject = "ArcGIS Stats clean up failure"
emailMessage = "The ArcGIS Stats clean up has failed..."

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
                 daysStatsToKeep,
                 domainUsername,
                 domainPassword,
                 tokenURL,
                 fcIntGISStatsPerTimePeriodURL,
                 fcIntGISErrorsURL,
                 fcIntGISWarningsURL,
                 fcIntGISServicesRequestedURL,
                 fcIntGISLayersDrawnURL,
                 fcIntGISAvgLayerDrawTimeURL,
                 fcIntGISServicesRequestedByUserURL,
                 fcIntGISStatsServicesStatus,
                 fcIntGISStatsServicesDown,
                 fcPublicGISStatsPerTimePeriodURL,
                 fcPublicGISErrorsURL,
                 fcPublicGISWarningsURL,
                 fcPublicGISServicesRequestedURL,
                 fcPublicGISLayersDrawnURL,
                 fcPublicGISAvgLayerDrawTimeURL,
                 fcPublicGISServicesRequestedByUserURL,
                 fcPublicGISStatsServicesStatus,
                 fcPublicGISStatsServicesDown):

    # --------------------------------------- Start of code --------------------------------------- #

    try:
        ########################
        ### Remove old stats ###
        ########################
        
        # Generate portal token
        r = requests.post(tokenURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data = {"f": "json"})
        token = r.json()['token']

        # Loop through feature services
        featureServices = argv[5:]
        for featureService in featureServices:

            # Set up URLs and 'where' clause
            whereClause = "StatDateUTC < CURRENT_TIMESTAMP - " + daysStatsToKeep
            queryURL = featureService + '/query'
            deleteFeaturesURL = featureService + '/deleteFeatures'

            # Find out how many records will be deleted
            data = {
                "f": "json",
                "token": token,
                "where": whereClause,
                "returnCountOnly": "true"
            }

            # Post data
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            r = requests.post(url = queryURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            log(featureService)
            log(r.text)

            # Delete the records
            data = {
                "f": "json",
                "token": token,
                "where": whereClause
            }

            # Post data
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            r = requests.post(url = deleteFeaturesURL, auth=HttpNtlmAuth(domainUsername, domainPassword), data=data, headers=headers)

            log(r.text)


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


def generateToken(username, password, portalUrl):
    '''Retrieves a token to be used with API requests.'''
    parameters = urllib.urlencode({'username' : username,
                                   'password' : password,
                                   'client' : 'referer',
                                   'referer': portalUrl,
                                   'expiration': 60,
                                   'f' : 'json'})
    response = urllib.urlopen(portalUrl + '/sharing/rest/generateToken?',
                              parameters).read()
    try:
        jsonResponse = json.loads(response)
        if 'token' in jsonResponse:
            return jsonResponse['token']
        elif 'error' in jsonResponse:
            log(jsonResponse['error']['message'])
            for detail in jsonResponse['error']['details']:
                log(detail)
    except ValueError as e:
        log('An unspecified error occurred.')
        log(e)


#A function to generate a token given username, password and the adminURL.
def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/admin/generateToken
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
        

#A function that checks that the input JSON object
#  is not an error object.    
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
