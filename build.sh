#!/bin/sh
#

IDENTIFIER="com.github.managedmac"
MMVERS=0.1

GITREV=`git log -n1 --format="%H" -- source`
GITREVINDEX=`git rev-list --reverse HEAD | grep -n $GITREV | cut -d: -f1`
VERSION=$MMVERS.$GITREVINDEX.0

TMPROOT="/tmp/mmbuild-root.$$"

mkdir -p "$TMPROOT"
mkdir -p "$TMPROOT"/usr/local/managedmac
mkdir -p "$TMPROOT"/usr/local/managedmac/mmlib
mkdir -p "$TMPROOT"/Library/LaunchDaemons

cp -a source/managedprinters "$TMPROOT"/usr/local/managedmac
cp -a source/mmlib/*.py "$TMPROOT"/usr/local/managedmac/mmlib
cp -a launchd/LaunchDaemons/com.github.managedmac-managedprinters-check.plist "$TMPROOT"/Library/LaunchDaemons

pkgbuild --root "$TMPROOT" --identifier "$IDENTIFIER" --version "$VERSION" --install-location / --scripts launchd/scripts managedmac.pkg

rm -rf "$TMPROOT"
