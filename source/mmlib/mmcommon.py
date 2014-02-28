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
common.py
"""
import urllib
import os
import sys
import subprocess
import tempfile
import re
import platform
import datetime
from Foundation import NSDictionary
from Foundation import CFPreferencesCopyAppValue


BUNDLE_ID = "ManagedMac"
MANAGED_MAC_DIR = "/Library/" + BUNDLE_ID
MANAGED_MAC_LOGDIR = MANAGED_MAC_DIR + "/Logs"
MANAGED_MAC_LOGFILE = MANAGED_MAC_LOGDIR + "/ManagedMac.log"
MANAGED_MAC_CATALOGDIR = MANAGED_MAC_DIR + "/catalogs"
MANAGED_MAC_MANIFESTDIR = MANAGED_MAC_DIR + "/manifests"
MANAGED_MAC_CATALOG_PLIST = MANAGED_MAC_CATALOGDIR + "/client_catalog.plist"
MANAGED_MAC_MANIFEST_PLIST = MANAGED_MAC_MANIFESTDIR + "/client_manifest.plist"

log_console = False
log_module_name = 'Core'


def prepare(needRoot = True):
    #
    # If the tool needs to be run as root, verify.
    #
    if needRoot and os.getuid() != 0:
        print "You must run this as root!"
        sys.exit(1)

    #
    # Attempt to create the required directories if we are root.
    #
    if os.getuid() == 0:
        createPath(MANAGED_MAC_DIR)
        createPath(MANAGED_MAC_LOGDIR)
        createPath(MANAGED_MAC_CATALOGDIR)
        createPath(MANAGED_MAC_MANIFESTDIR)


def createPath(path):
    if os.path.exists(path) == False:
        try:
            os.mkdir(path)
        except:
            print "Could not create " + path + " and folder does not exist. Cannot continue."
            sys.exit(1)


def readDictionary(filepath):
    """
    Use Foundation calls to read a property list (dictionary)
    from disk.
    """
    return NSDictionary.dictionaryWithContentsOfFile_(filepath)


def writeDictionary(dict, filepath):
    """
    Write dictionary to disk using Foundation call.
    """
    dictObj = NSDictionary.dictionaryWithDictionary_(dict)
    dictObj.writeToFile_atomically_(filepath, 1)


def download(url, destination_path = None):
    """
    Download the given URL to the destination_path. If destination_path
    was not specified then a temporary file is generated. The path to
    the file is returned. If there was an error then an exception is
    raised.
    """
    url = urllib.urlopen(url)

    if url.getcode() != 200 and url.getcode() is not None:
        raise IOError('Invalid response received: ' + str(url.getcode()))

    try:
        if destination_path is None:
            (fd, filename) = tempfile.mkstemp()
            os.close(fd)
            destination_path = filename

        with open(destination_path, 'wb') as fp:
            fp.write(url.read(-1))
    except:
        raise
    finally:
        fp.close()

    return destination_path


def systemIdleTimer():
    """
    Return idle time in seconds.
    Source: http://stackoverflow.com/questions/2425087/testing-for-inactivity-in-python-on-mac
    """

    # Get the output from 
    # ioreg -c IOHIDSystem
    s = subprocess.Popen(["ioreg", "-c", "IOHIDSystem"], stdout=subprocess.PIPE).communicate()[0]
    lines = s.split('\n')

    raw_line = ''
    for line in lines:
        if line.find('HIDIdleTime') > 0:
            raw_line = line
            break

    nano_seconds = long(raw_line.split('=')[-1])
    seconds = nano_seconds/10**9
    return seconds


def systemSerialNumber():
    """
    Return the SerialNumber of the system.
    """

    # Get the output from 
    # ioreg -c IOPlatformExpertDevice
    s = subprocess.Popen(["ioreg", "-c", "IOPlatformExpertDevice"], stdout=subprocess.PIPE).communicate()[0]
    lines = s.split('\n')

    matches = re.findall('.*\"IOPlatformSerialNumber\" = \"(.*)\"', s)
    return "" if len(matches) == 0 else matches[0]


def pref(pref_name, default = None):
    default_prefs = {
        'RepoURL': 'http://munki/managedmac',
        'ClientIdentifier': '',
    }
    pref_value = CFPreferencesCopyAppValue(pref_name, BUNDLE_ID)
    if pref_value == None:
        pref_value = default_prefs.get(pref_name)
    return pref_value


def log(message):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %I:%M:%S] ")
    if log_console:
        print timestamp + log_module_name + ": " + message
    with open(MANAGED_MAC_LOGFILE, "a") as fp:
        fp.write(timestamp + log_module_name + ": " + message + "\n")

    statinfo = os.stat(MANAGED_MAC_LOGFILE)
    if statinfo.st_size > 1000000:
        try:
            if os.path.exists(MANAGED_MAC_LOGFILE + ".5"):
                os.remove(MANAGED_MAC_LOGFILE + ".5")
            for x in [4, 3, 2, 1, 0]:
                if os.path.exists(MANAGED_MAC_LOGFILE + "." + str(x)):
                    os.rename(MANAGED_MAC_LOGFILE + "." + str(x), MANAGED_MAC_LOGFILE + "." + str(x + 1))
            os.rename(MANAGED_MAC_LOGFILE, MANAGED_MAC_LOGFILE + ".0")
        except:
            pass


def valueForKeyPath(dict, keypath, default = None):
    """
    Get the keypath value of the specified dictionary.
    """
    keys = keypath.split('.')
    for key in keys:
        if key not in dict:
            return default
        dict = dict[key]

    return dict


def updateRepo():
    """
    Download the manifest and catalogs for this client.
    """
    getManifest()
    processManifestKeyPath(None, None, None, None)


MANIFESTS = {}
def getManifest(manifest_name = None):
    """
    Download a client manifest.
    """
    global MANIFESTS
    baseurl = pref("RepoURL") + '/manifests/'

    if manifest_name is None:
        if 'client_manifest' in MANIFESTS:
            return MANIFESTS['client_manifest']

        #
        # Make a list of the identifiers to try.
        #
        if pref('ClientIdentifier') == "":
            hostname = platform.node()
            identifiers = [ hostname ]
            if hostname.find('.') != -1:
                identifiers += [ hostname.split(".")[0] ]
            identifiers += [ systemSerialNumber(), "site_default" ]
        else:
            identifiers = [ pref("ClientIdentifier") ]

        #
        # Try each of the identifiers until we find one that works.
        #
        for identifier in identifiers:
            url = baseurl + identifier
            log("Downloading manifest from " + url)
            try:
                download(url, MANAGED_MAC_MANIFEST_PLIST)
                data = readDictionary(MANAGED_MAC_MANIFEST_PLIST)
                if data is not None:
                    MANIFESTS['client_manifest'] = data
                return data
            except Exception, e:
                log("Download failed: " + str(e))
                pass

        #
        # Try to use the local copy instead.
        #
        try:
            data = readDictionary(MANAGED_MAC_MANIFEST_PLIST)
            if data is not None:
                MANIFESTS['client_manifest'] = data
            return data
        except:
            MANIFESTS['client_manifest'] = None
            return None
    else:
        url = baseurl + manifest_name
        path = MANAGED_MAC_MANIFESTDIR + '/' + manifest_name

        if manifest_name in MANIFESTS:
            return MANIFESTS[manifest_name]

        log('Downloading manifest from ' + url)
        try:
            download(url, path)
        except Exception, e:
            log("Download failed: " + str(e))

        try:
            data = readDictionary(path)
            if data is not None:
                MANIFESTS[manifest_name] = data
            return data
        except:
            MANIFESTS[manifest_name] = None
            return None


CATALOGS = {}
def getCatalog(catalog_name = None):
    """
    Download a catalog.
    """
    global CATALOGS
    baseurl = pref("RepoURL") + '/catalogs/'
    url = baseurl + catalog_name
    path = MANAGED_MAC_CATALOGDIR + '/' + catalog_name

    if catalog_name in CATALOGS:
        return CATALOGS[catalog_name]

    log('Downloading catalog from ' + url)
    try:
        download(url, path)
    except Exception, e:
        log("Download failed: " + str(e))

    try:
        data = readDictionary(path)
        if data is not None:
            CATALOGS[catalog_name] = data
        return data
    except:
        CATALOGS[catalog_name] = None
        return None


def getCatalogs(cataloglist):
    """
    Download all the catalogs listed.
    """

    for catalog in cataloglist:
        getCatalog(catalog)


def processManifestKeyPath(manifest_name, keypath, runinfo, handler, parentcatalogs = None):
    """
    Process the all the values of keypath in the manifest. For each
    item call the handler. Recursively checks included manifests.
    """

    manifest = getManifest(manifest_name)
    if manifest is None:
        return None

    cataloglist = manifest.get('catalogs')
    if cataloglist:
        getCatalogs(cataloglist)
    elif parentcatalogs:
        cataloglist = parentcatalogs

    #
    # Check for nested manifests
    #
    if 'included_manifests' in manifest:
        for item in manifest['included_manifests']:
            processManifestKeyPath(item, keypath, runinfo, handler, cataloglist)

    #
    # Process the keys.
    #
    if keypath is not None:
        items = valueForKeyPath(manifest, keypath)
        if items is not None:
            for item in items:
                handler(item, cataloglist, runinfo)


def getFirstCatalogKeyPath(cataloglist, keypath, default = None):
    """
    Get the value of the keypath in the first catalog containing it.
    """
    for name in cataloglist:
        catalog = getCatalog(name)
        if catalog is not None:
            value = valueForKeyPath(catalog, keypath)
            if value is not None:
                return value

    return default

