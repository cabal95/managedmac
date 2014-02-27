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
printers.py
"""
import os
import subprocess
import re


def ppdInfo(filename):
    """
    Get information from the printer's installed PPD file. All keys will
    be set to blank strings if they could not be found in the PPD.
    """
    textfile = open(filename, 'r')
    filetext = textfile.read()
    textfile.close()

    info = { }
    matches = re.findall('\*Manufacturer:[ \t]*\"(.*)\"', filetext)
    if len(matches) > 0:
        info['Manufacturer'] = matches[0]
    else:
        info['Manufacturer'] = ''

    matches = re.findall('\*ModelName:[ \t]*\"(.*)\"', filetext)
    if len(matches) > 0:
        info['ModelName'] = matches[0]
    else:
        info['ModelName'] = ''

    matches = re.findall('\*NickName:[ \t]*\"(.*)\"', filetext)
    if len(matches) > 0:
        info['NickName'] = matches[0]
    else:
        info['NickName'] = ''

    #
    # Update the Model and NickName to include the Manufacturer
    # if they do not already.
    #
    if len(info['ModelName']) > 0:
        if info['ModelName'].find(info['Manufacturer']) != 0:
            info['ModelName'] = info['Manufacturer'] + " " + info['ModelName']
        if info['NickName'].find(info['Manufacturer']) != 0:
            info['NickName'] = info['Manufacturer'] + " " + info['NickName']

    return info


def add(printer_name, uri, ppd, location):
    """
    Add a new printer to the system with the given parameters.
    """
    try:
        with open(os.devnull, "w") as fnull:
            args = ["lpadmin", "-p", printer_name, "-v", uri, "-P", ppd, "-L", location, "-E"]
            status = subprocess.call(args, stdout=fnull, stderr=subprocess.STDOUT)
    except:
        return False

    return True if status == 0 else False


def delete(printer_name):
    """
    Delete the given named printer from the system.
    """
    try:
        with open(os.devnull, 'w') as fnull:
            status = subprocess.call(['/usr/sbin/lpadmin', '-x', printer_name], stdout=fnull, stderr=subprocess.STDOUT)
    except:
        return False

    return True if status == 0 else False


def exists(printer_name):
    """
    Check if the named printer exists.
    """
    try:
        with open(os.devnull, 'w') as fnull:
            status = subprocess.call(['/usr/bin/lpstat', '-a', printer_name], stdout=fnull, stderr=subprocess.STDOUT)
    except:
        return False

    return True if status == 0 else False


def setOptions(printer_name, options):
    """
    Check if the named printer exists.
    """
    try:
        args = [ '/usr/sbin/lpadmin', '-p', printer_name ]
        for key in options:
            args += [ '-o', key + "=" + options[key] ]
        with open(os.devnull, 'w') as fnull:
            status = subprocess.call(args, stdout=fnull, stderr=subprocess.STDOUT)
    except Exception as e:
        print str(e)
        return False

    return True if status == 0 else False


def acceptJobs(printer_name):
    """
    Tell the CUPS system to start accepting jobs for the named printer.
    """
    try:
        with open(os.devnull, 'w') as fnull:
            status = subprocess.call(['/usr/sbin/cupsaccept', printer_name], stdout=fnull, stderr=subprocess.STDOUT)
    except:
        return False

    return True if status == 0 else False


def rejectJobs(printer_name):
    """
    Tell the CUPS system to stop accepting jobs for the named printer.
    """
    try:
        with open(os.devnull, 'w') as fnull:
            status = subprocess.call(['/usr/sbin/cupsreject', printer_name], stdout=fnull, stderr=subprocess.STDOUT)
    except:
        return False

    return True if status == 0 else False


def hasJobs(printer_name):
    """
    Determine if the named printer has any print jobs queued up.
    """
    return True if jobCount(printer_name) > 0 else False


def jobCount(printer_name):
    """
    Retrieve the number of jobs in the named printer's queue.
    """
    try:
        value = subprocess.check_output(['/usr/bin/lpstat', '-o', printer_name], stderr=subprocess.STDOUT)
    except:
        return -1

    return (len(value.split("\n")) - 1)


def status(printer_name):
    """
    Retrieve the status of the printer. Returns one of the following strings:
    idle, printing, paused, unknown
    """
    try:
        value = subprocess.check_output(['/usr/bin/lpstat', '-p', printer_name], stderr=subprocess.STDOUT)
    except:
        return 0

    if value.find(' is idle.') != -1:
        return 'idle'
    elif value.find(' now printing ') != -1:
        return 'printing'
    elif value.find(' disabled since ') != -1:
        return 'paused'
    else:
        return 'unknown'


def isPrinting(printer_name):
    """
    Tests wether the named printer is currently printing a document.
    """
    return True if printerStatus(printer_name) == 'printing' else False


def uri(printer_name):
    """
    Retrieve the current URI for the named printer.
    """
    try:
        value = subprocess.check_output(['/usr/bin/lpstat', '-v', printer_name], stderr=subprocess.STDOUT)
    except:
        return 0

    matches = re.findall('[^:]*:[ \t]+(.*)', value)
    if len(matches) > 0:
        return matches[0]

    return ""

