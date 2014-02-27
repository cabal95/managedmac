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

