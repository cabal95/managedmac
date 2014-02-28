# Managing Printers

The managedprinters script will provide you with a method to centrally
manage your printers across your network. Each client will retrieve a
manifest with dictates what printers get installed or removed as well
as reference a catalog with contains the information about that printer.

The general process is similar to how munki operates. Once an hour the
client will attempt to retrieve the manifest and catalog from the server.
If new files were downloaded or cached version are already available (but
the server could not be contacted) then processing of the Install and
Uninstalls for the printers will commence.

For each printer listed in the Uninstall section, the system will check to
see if that printer is installed and if so it will delete it from the CUPS
system.

For each priner listed in the Install section, the system will go through
the following checks:

- If printer is not installed, install.
- Test installed printer Model against what it should be, update if different.
- Test installed printer URI against what it should be, update if different.
- Test installed printer LastUpdate reference against the LastUpdate
reference in the catalog, update if different.
- Check if there are jobs queued, if none then update.
- If there are jobs queued, wait for job queue to clear for up to 30 seconds,
if the queue does not clear then abort this printer and try again next run.

This means that you can swap a printer out for a new model, update your
catalog and the clients will pickup the new settings. Or if your URI changes
then the clients will also pickup the new settings. If you added a new
feature option to the printer (say more RAM) and you need to update the
default options then you can use the LastUpdate flag to force an update.

## How Manifests are chosen

There is a application setting called ClientIdentifier that can be set to
specify a specific manifest to use. If not set (or set to an empty string)
then the system will use the following list in order to aquire a manifest:

1. Fully Qualified Domain Name
2. Hostname
3. Serial Number
4. "site_default"

Each manifest must reference one or more catalogs, though at the time of this
writing only the first catalog specified will be used. There are plans to
allow multiple catalogs to be referenced and have them merged into a single
catalog automatically.

## Sample Manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>catalogs</key>
	<array>
		<string>production</string>
	</array>
	<key>ManagedPrinters</key>
	<dict>
		<key>Install</key>
		<array>
			<string>Buford</string>
			<string>Conrad</string>
			<string>Radar</string>
		</array>
		<key>Uninstall</key>
		<array>
			<string>mcx_0</string>
			<string>mcx_1</string>
		</array>
	</dict>
</dict>
</plist>
```

This manifest would cause the printers named **Buford**, **Conrad**, and
**Radar** to be installed (or updated) as neccessary. It would also cause
the removal of **mcx_0** and **mcx_1** if they were installed. In this case
we switched from MCX managed printers to this script, so we want to make
sure the old printers get removed.

The manifest also references the **production** catalog (as seen below) with
contains the information about the printers themselves.

## Sample Catalog

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>ManagedPrinters</key>
	<dict>
		<key>Radar</key>
		<dict>
			<key>DeviceURI</key>
			<string>lpd://radar-copier.example.org/</string>
			<key>Model</key>
			<string>Canon iR-ADV C7260/7270 Z</string>
			<key>Location</key>
			<string>North West Office</string>
			<key>PPDOptions</key>
			<dict>
				<key>CNDuplex</key>
				<string>None</string>
				<key>CNFinisher</key>
				<string>BFINL1</string>
				<key>CNPuncher</key>
				<string>PUNU23</string>
				<key>Resolution</key>
				<string>600</string>
				<key>CNColorMode</key>
				<string>mono</string>
			</dict>
			<key>PPDURL</key>
			<string>file://localhost/Library/Printers/PPDs/Contents/Resources/CNPZUIRAC7260ZU.ppd.gz</string>
			<key>LastUpdate</key>
			<string>6</string>
		</dict>
		<key>Conrad</key>
		<dict>
			<key>DeviceURI</key>
			<string>ipp://printserver.example.org/printers/Conrad</string>
			<key>Model</key>
			<string>HP LaserJet 4200 Series</string>
			<key>Location</key>
			<string>North East Office</string>
			<key>PPDOptions</key>
			<dict>
				<key>HPOption_EnvFeeder</key>
				<string>True</string>
				<key>InstalledMemory</key>
				<string>Mem2</string>
			</dict>
			<key>PPDURL</key>
			<string>file://localhost/Library/Printers/PPDs/Contents/Resources/hp LaserJet 4200 Series.gz</string>
			<key>LastUpdate</key>
			<string>1</string>
		</dict>
		<key>Buford</key>
		<dict>
			<key>DeviceURI</key>
			<string>ipp://buford-copier.example.org/</string>
			<key>Model</key>
			<string>Canon iR-ADV 8085/8095 PS</string>
			<key>Location</key>
			<string>South Copy Room</string>
			<key>PPDOptions</key>
			<dict>
				<key>CNDuplex</key>
				<string>None</string>
				<key>CNFinisher</key>
				<string>BFIND1</string>
				<key>CNHalftone</key>
				<string>highresolution</string>
				<key>CNPuncher</key>
				<string>PUNU23</string>
				<key>CNSidePaperDeck</key>
				<string>Small</string>
				<key>CNSpecID</key>
				<string>0200</string>
				<key>Resolution</key>
				<string>1200</string>
			</dict>
			<key>PPDURL</key>
			<string>file://localhost/Library/Printers/PPDs/Contents/Resources/CNMCIRA8095S2US.ppd.gz</string>
			<key>LastUpdate</key>
			<string>1</string>
		</dict>
	</dict>
</dict>
</plist>
```

Each major dictionary entry (for example, **Buford**) contains all the
information needed to install the printer on the client. Let's break this
down to each element.

```xml
<key>DeviceURI</key>
<string>ipp://buford-copier.example.org/</string>
```

This provides the URI needed to print to this device. Any URI that you can
use in CUPS (and/or Mac) can be entered here.


```xml
<key>Model</key>
<string>HP LaserJet 4200 Series</string>
```

This should correspond to the model name of the printer. You can find this
by examining the PPD directly and looking at the ModelName property.

```xml
<key>Location</key>
<string>North East Office</string>
```

```xml
<key>PPDOptions</key>
<dict>
    <key>CNDuplex</key>
    <string>None</string>
</dict>
```

This allows you to set default options for the printer. Each key/string pair
corresponds to an option name/value in the PPD. You will need to examine the
PPD directly to figure out what these are. In the above example this turns
off duplex printing by default (Canon copiers have this turned on by default
which is annoying for us as much of our printing should intentionally not be
duplexed).


```xml
<key>PPDURL</key>
<string>file://localhost/Library/Printers/PPDs/Contents/Resources/CNMCIRA8095S2US.ppd.gz</string>
```

The URL of the PPD.  Normally, this can be a file://localhost/ reference to
the file on the client system. If for some reason you want to pull a PPD from
your server you may enter a full http URL here as well. You must still install
the print driver on the client machines as most Mac PPDs reference utilities
that must be installed and run on the client machine during printing.

```xml
<key>LastUpdate</key>
<string>1</string>
```

The LastUpdate parameter is used to force the printer to update even if, for
whatever reason, it thinks it doesn't need to. Right now any time this does
not match the installed version it is updated, but in the future this will
probably be changed to a greater than test.
