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
setup_timemachine.py
"""
import sys
import time
import os
import subprocess

from mmlib import mmcommon


def run():
    """
    Main processing function.
    """

    pref = mmcommon.pref('TimeMachine')
    if pref is not None:
        processTM(pref)


def processTM(pref):
    """
    If TimeMachine is not already configured then configure it based on
    the settings in the preference dictionary.
    """
    if os.path.isfile('/usr/bin/tmutil') and isConfigured() == False:
        # Get the UUID of the system, required.
        uuid = getUUID()
        if uuid is None:
            mmcommon.log('Could not determine system UUID')
            return

        # Get the OD computer name of the system, required.
        od_name = getODName(uuid)
        if od_name is None:
            mmcommon.log('Could not determine OD system name')
            return

        server = pref.get('Server')
        share = pref.get('Share')
        user = pref.get('User')
        password = pref.get('Password')
        enable = pref.get('Enable')

        user = user.replace("$ODNAME", od_name)

        # Perform actual setup of TimeMachine.
        url = 'afp://' + user + ':' + password + '@' + server + '/' + share
        safeurl = 'afp://' + user + ':********@' + server + '/' + share
        mmcommon.log('Setting up TimeMachine for URL ' + safeurl + '...');
        subprocess.call(['/usr/bin/tmutil', 'setdestination', url], stderr=subprocess.STDOUT)
        if enable:
            subprocess.call(['/usr/bin/tmutil', 'enable'], stderr=subprocess.STDOUT)
        mmcommon.log('Finished.');


def isConfigured():
    try:
        value = subprocess.check_output(["/usr/bin/tmutil", "destinationinfo"], stderr=subprocess.STDOUT)
    except:
        return False

    if value.find('No destinations configured') != -1:
        return False

    return True


def getUUID():
    try:
        value = subprocess.check_output(["/usr/sbin/ioreg -rd1 -c IOPlatformExpertDevice | awk '/IOPlatformUUID/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"], stderr=subprocess.STDOUT, shell=True)
    except:
        return None

    return value.rstrip()


def getODName(uuid):
    try:
        ether = subprocess.check_output(["/sbin/ifconfig en0 | grep ether | awk '{ print $2 }'"], stderr=subprocess.STDOUT, shell=True)
    except:
        return None

    ether = ether.rstrip()
    try:
        name = subprocess.check_output(["/usr/bin/dscl localhost -search /LDAPv3/ldap.hdcnet.org ENetAddress \"" + ether + "\" | grep '^Computers' | awk '{ print $1 }' | cut -f2 -d/ | sed 's/[^-a-z0-9A-Z]//g'"], stderr=subprocess.STDOUT, shell=True)
    except:
        return None

    return name.rstrip()
