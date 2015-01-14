#!/usr/bin/python
#
# Copyright 2014 Daniel Hazelbaker.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
managedprinters.py
"""
import sys
import time
import os

from mmlib import mmcommon
from mmlib import printers


MANAGED_PRINTERS_STATUS_PLIST = mmcommon.MANAGED_MAC_DIR + "/PrinterStatus.plist"
MANAGED_PRINTERS_PLIST = mmcommon.MANAGED_MAC_DIR + "/ManagedPrinters.plist"
MANAGED_PRINTERS_USERLIST_DIR = mmcommon.MANAGED_MAC_DIR + "/ManagedPrinters/UserPrinters"


def run():
    """
    Main processing function.
    """
    installinfo = { }
    uninstallinfo = { }

    # Process user selections (e.g. via munki)
    try:
        files = [f for f in os.listdir(MANAGED_PRINTERS_USERLIST_DIR) if os.path.isfile(os.path.join(MANAGED_PRINTERS_USERLIST_DIR, f))]
    except:
        files = []
    for p in files:
        mmcommon.processManualRun(None, installinfo, processUserInstall, p)
    for p in userPrinters():
        if p not in files:
            mmcommon.processManualRun(None, uninstallinfo, processUserUninstall, p)

    # Process system mandated items
    mmcommon.processManifestKeyPath(None, 'ManagedPrinters.Uninstall', uninstallinfo, processSystemUninstall)
    mmcommon.processManifestKeyPath(None, 'ManagedPrinters.Install', installinfo, processSystemInstall)


def processUserUninstall(pname, cataloglist, runinfo):
    processUninstall(pname, cataloglist, True, runinfo)


def processSystemUninstall(pname, cataloglist, runinfo):
    processUninstall(pname, cataloglist, False, runinfo)


def processUninstall(pname, cataloglist, asuser, runinfo):
    """
    Go through all the printers listed and try to remove them
    from the system.
    """
    try:
        if printers.exists(pname):
            mmcommon.log('Printer ' + pname + ' has been marked for uninstall.')
            if printers.delete(pname) == False:
                raise RuntimeWarning('Unknown error trying to delete printer');
            mmcommon.log('Printer ' + pname + ' removed.')
            if asuser:
                removedUserPrinter(pname);
    except Exception, e:
        mmcommon.log('Error trying to remove printer ' + pname + '. Error = ' + str(e))


def processUserInstall(pname, cataloglist, runinfo):
    processInstall(pname, cataloglist, True, runinfo)


def processSystemInstall(pname, cataloglist, runinfo):
    processInstall(pname, cataloglist, False, runinfo)


def processInstall(pname, cataloglist, asuser, runinfo):
    """
    Go through all the printers listed and try to add them into
    the system. A printer is only added if the printer type does
    not match what it should be, this handles cases where the
    printer is installed but the PPD does not match what is on
    disk. Right now that means the printer model does not match.
    """
    if pname in runinfo:
        return
    runinfo[pname] = True

    mmcommon.log("Printer " + pname + " has been marked for install.")
    needToAdd = 1
    data = mmcommon.getFirstCatalogKeyPath(cataloglist, 'ManagedPrinters.' + pname)
    if data is None:
        mmcommon.log('Printer does not exist in any catalog, ignoring.')
        return

    exists = printers.exists(pname)
    model = data['Model']
    deviceUri = data['DeviceURI']
    location = data["Location"]
    ppdUrl = data["PPDURL"]
    try:
        description = data['Description']
    except:
        description = pname

    if exists:
        #
        # If the printer exists, check it's current information
        # against what it should be to determine if we need to
        # re-install.
        #
        currentInfo = printers.ppdInfo('/etc/cups/ppd/' + pname + '.ppd')
        currentUri = printers.uri(pname);

        #
        # Check if we should be up to date based on available information.
        #
        if currentUri == deviceUri and printerLastUpdate(pname) == data["LastUpdate"]:
            if currentInfo['ModelName'] == model or currentInfo['NickName'] == model:
                mmcommon.log("Printer " + pname + " is already installed and up to date.")
                return

    mmcommon.log("Printer " + pname + " will be installed.")

    #
    # Check to make sure the printer is not currently printing.
    # If there are more than 2 print jobs queued or the system
    # idle timer is greater than 120 seconds then skip adding
    # this printer immedietly. Otherwise wait for up to 30
    # seconds for the jobs to clear. If there are too many
    # print jobs or the system has been idle, we assume the
    # print job(s) may take a long time to complete.
    #
    if exists:
        #
        # Wait for any existing jobs to clear.
        #
        if printers.hasJobs(pname):
            if mmcommon.systemIdleTimer() > 120 or printers.jobCount(pname) > 2:
                mmcommon.log("Printer " + pname + " is in use and will be updated later.")
                return

            mmcommon.log("Waiting for printer " + pname + " to become idle.")
            untilTime = (time.time() + 30)
            while time.time() < untilTime and printers.jobCount(pname) > 0:
                time.sleep(5)
            if time.time() >= untilTime:
                mmcommon.log("Printer " + pname + " is still in use and will be updated later.")
                return

        #
        # Try to reject jobs before we modify the printer, if
        # the user sneaks a print job in then just forget it
        # and we will try again later.
        #
        printers.rejectJobs(pname)
        if printers.hasJobs(pname):
            mmcommon.log("Failed to pause printer " + pname + ". Printer will be updated later.")
            printers.acceptJobs(pname)
            return

    #
    # Okay, add the printer.
    #
    try:
        #
        # Try to download the new PPD.
        #
        if ppdUrl[:4] == 'drv:':
            ppdfile = ppdUrl
        else:
            mmcommon.log("Downloading PPD from " + ppdUrl)
            ppdfile = mmcommon.download(ppdUrl)

        #
        # Build up any options.
        #
        if "PPDOptions" in data:
            options = data["PPDOptions"]
        else:
            options = None

        #
        # Add the printer.
        #
        try:
            if printers.add(pname, deviceUri, ppdfile, location, description) == False:
                raise RuntimeWarning("Failed to add printer.")
            if options != None and printers.setOptions(pname, options) == False:
                raise RuntimeWarning("Failed to set options for printer.")
            printerLastUpdate(pname, data["LastUpdate"])
            mmcommon.log("Printer " + pname + " has been installed.")
            if asuser:
                addedUserPrinter(pname);
        except:
            raise
        finally:
            if ppdfile[:1] == '/':
                os.remove(ppdfile)
    except Exception, e:
        mmcommon.log("Encountered an error trying to install printer " + pname + ": " + str(e))
    finally:
        if exists:
            printers.acceptJobs(pname)


def printerLastUpdate(printer_name, value = None):
    """
    Get the LastUpdate value for the installed named printer.
    """
    status = mmcommon.readDictionary(MANAGED_PRINTERS_STATUS_PLIST)

    if value is None:
        if status is None:
            return -1

        if printer_name not in status or "LastUpdate" not in status[printer_name]:
            return -1

        return status[printer_name]["LastUpdate"]
    else:
        if status is None:
            status = { }

        if printer_name not in status:
            status[printer_name] = { }

        status[printer_name]["LastUpdate"] = value

        try:
            mmcommon.writeDictionary(status, MANAGED_PRINTERS_STATUS_PLIST)
        except:
            raise

        return value


def userPrinters():
    dict = mmcommon.readDictionary(MANAGED_PRINTERS_PLIST)
    if dict is None:
        return []
    if "UserPrinters" not in dict:
        return []

    return dict["UserPrinters"]


def addedUserPrinter(pname):
    dict = mmcommon.readDictionary(MANAGED_PRINTERS_PLIST)
    if dict is None:
        dict = { }
    if "UserPrinters" not in dict:
        dict["UserPrinters"] = [ ]

    if pname not in dict["UserPrinters"]:
        dict["UserPrinters"] += [pname]
        mmcommon.writeDictionary(dict, MANAGED_PRINTERS_PLIST)


def removedUserPrinter(pname):
    dict = mmcommon.readDictionary(MANAGED_PRINTERS_PLIST)
    if dict is None:
        return
    if "UserPrinters" not in dict:
        return

    if pname in dict["UserPrinters"]:
        dict["UserPrinters"] = [p for p in dict["UserPrinters"] if p != pname]
        mmcommon.writeDictionary(dict, MANAGED_PRINTERS_PLIST)

