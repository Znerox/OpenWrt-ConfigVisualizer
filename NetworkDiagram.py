# This scipt reads the files "network" and "dhcp", and optionally a "hosts" file with other clients
# "network" contains information about network interfaces (interface name, interface ip, netmask, WireGuard hosts endpoint ip)
# "dhcp" contains information about dhcp clients in each network (interface name, client name, client ip)
# "hosts" can contain information about clients with static IP. The format is [hostname IP], do not include the brackets. One per line.

# Ask user if there is a custom file
importHostsFile = input("Should the script import clients specified in 'hosts' file? (y/n)").lower().strip()
# Should we append something at the end of the interface name for WireGuard interfaces
WGInterfaceSuffix = input("Should WireGuard interfaces have a suffix at the end of the name? E.g. '-WG'. (Write y/n or your custom suffix)")

# Define interfaces and hosts as empty nested lists

interfaces = [[]] 
# Level 0 = interfaces
# Level 1 = interface_name,IP,firstThreeOctets,netmask,CIDR,sortKey,interfaceType

hosts = [[]]
# Level 0 = hosts
# Level 1 = hostname,IP,firstThreeOctets,sortKey,correspondingWGInterfaceName,hostType

temporaryInterfaceList = ["","","","","","",""]
temporaryHostList = ["","","","","",""]

interfaceNumber = -1
hostNumber = -1

# Used when reading network file
interfaceNameFound = 0
interfaceIPfound = 0
interfaceNetmaskFound = 0
interfaceWGAddressFound = 0
textblockIsEthernetInterface = 0
textblockIsWireGuardInterface = 0
textblockIsWireGuardClient = 0
WGClientNameFound = 0
WGClientIPFound = 0
interfaceNameLinkedToThisWGClient = 0
correspondingWGInterfaceName = 0

# Used when reading dhcp file
hostNameFound = 0
hostIPFound = 0

# Used for both
sortKey = 0
hostType = 0

# sortKey is a parameter associated with every client. It's used to display clients in numerical order in the diagram
# E.g. a client with IP 192.168.1.50 would get the sortKey 192168001050, 10.0.0.2 would be 10000000002.
def generateSortKey(input):
    thisIPSplittedAndStandardized = ["","","",""]
    for count, x in enumerate(input):
        match len(x):
            case 1:
                x = "00" + str(x)
            case 2:
                x = "0" + str(x)
        thisIPSplittedAndStandardized[count]=x
        # sortKey will be an int with the IP of the network interface
        sortKey = int(str(thisIPSplittedAndStandardized[0]) + str(thisIPSplittedAndStandardized[1]) + str(thisIPSplittedAndStandardized[2]) + str(thisIPSplittedAndStandardized[3]))
    return sortKey

# Read network config file
with open("network", "r") as networkFile:
    # Read line by line
    intputFileNetwork = networkFile.read()
    lines = intputFileNetwork.split('\n')

    # Look for interfaces, add them to temporary list
    for thisLine in lines:
        # Find interface name / network name
        stringPositionOfInterface = thisLine.find("config interface")
        if stringPositionOfInterface == 0:
            # If line has been found, first increment counter to make sure details on following lines are associated with this interface
            interfaceNumber += 1
            lineLength = len(thisLine)
            thisInterfaceName = thisLine[18:lineLength-1]
            # Read interface name into temporary list
            temporaryInterfaceList[0] = thisInterfaceName
            interfaceNameFound = 1

        # Find IP on this interface (ethernet)
        stringPositionOfIP = thisLine.find("option ipaddr")
        if stringPositionOfIP != -1:
            textblockIsEthernetInterface = 1
            lineLength = len(thisLine)
            thisIP = thisLine[16:lineLength-1]
            temporaryInterfaceList[1] = thisIP
            thisIPSplitted = thisIP.split('.')
            # thisIPSplitted[0/1/2/3] now contains the four octests of the interface IP
            firstThreeOctets = thisIPSplitted[0] + thisIPSplitted[1] + thisIPSplitted[2]
            temporaryInterfaceList[2] = firstThreeOctets
            sortKey = generateSortKey(thisIPSplitted)
            temporaryInterfaceList[5] = sortKey
            interfaceIPfound = 1
        
        # Find netmask on this interface
        stringPositionOfnetmask = thisLine.find("option netmask")
        if stringPositionOfnetmask != -1:
            textblockIsEthernetInterface = 1
            lineLength = len(thisLine)
            thisNetmask = thisLine[17:lineLength-1]

            # Convert netmask to CIDR notation
            # (This isn't really that useful, other parts of this script assumes /24)
            thisNetmaskSplit = thisNetmask.split('.')
            CIDRParts = ["","","",""]
            for count, thisPart in enumerate(thisNetmaskSplit):
                match thisPart:
                    case "255":
                        CIDRParts[count] = 8
                    case "254":
                        CIDRParts[count] = 7
                    case "252":
                        CIDRParts[count] = 6
                    case "248":
                        CIDRParts[count] = 5
                    case "240":
                        CIDRParts[count] = 4
                    case "224":
                        CIDRParts[count] = 3
                    case "192":
                        CIDRParts[count] = 2
                    case "128":
                        CIDRParts[count] = 1
                    case "0":
                        CIDRParts[count] = 0
            
            CIDR = CIDRParts[0] + CIDRParts[1] + CIDRParts[2] + CIDRParts[3]
            temporaryInterfaceList[3] = thisNetmask
            temporaryInterfaceList[4] = CIDR
            interfaceNetmaskFound = 1
        
        stringPositionOfProtoWG = thisLine.find("option proto 'wireguard'")
        if stringPositionOfProtoWG != -1:
            textblockIsWireGuardInterface = 1
        
        stringPositionOfListAddresses = thisLine.find("list addresses")
        if stringPositionOfListAddresses != -1:
            lineLength = len(thisLine)
            thisAddress = thisLine[17:lineLength-1]
            temporaryInterfaceList[1] = thisAddress
            thisAddressSplitted = thisAddress.split('.')

            # WireGuard interface might have /32 at the end, remove that as it causes problems for the sortKey
            stringPositionOfSlash32 = thisAddressSplitted[3].find("/")
            if stringPositionOfSlash32 != -1:
                thisAddressSplitted[3] = (thisAddressSplitted[3])[:-3]
            
            sortKey = generateSortKey(thisAddressSplitted)
            temporaryInterfaceList[5] = sortKey
            firstThreeOctets = thisAddressSplitted[0] + thisAddressSplitted[1] + thisAddressSplitted[2]
            temporaryInterfaceList[2] = firstThreeOctets      
            interfaceWGAddressFound = 1 #This might cause problems if other protocols use the phrase "list addresses"   

        stringPositionOfWireGuardClient = thisLine.find("config wireguard")
        if stringPositionOfWireGuardClient != -1:
            textblockIsWireGuardClient = 1
            # We need to read the name of the WireGuard interface to be able to correctly match peers to interfaces
            lineLength = len(thisLine)
            interfaceNameLinkedToThisWGClient = thisLine[17:lineLength] 
            temporaryHostList[4] = interfaceNameLinkedToThisWGClient
            temporaryHostList[5] = "wg"

            # Some WireGuard clients may have multiple "allowed_ips", that can cause a bug where wrong peer name/IP is put in the diagram
            # To avoid this, reset this variable whenever starting on a new "textblockIsWireGuardClient"
            WGClientIPFound = 0
        
        stringPositionOfWireGuardClientDescription = thisLine.find("option description")
        if stringPositionOfWireGuardClientDescription != -1:
            lineLength = len(thisLine)
            thisWGClientName = thisLine[21:lineLength-1]
            temporaryHostList[0] = thisWGClientName
            WGClientNameFound = 1
        
        stringPositionOfWireGuardClientInternalIP = thisLine.find("list allowed_ips")
        if stringPositionOfWireGuardClientInternalIP != -1:
            lineLength = len(thisLine)
            thisWGClientIP = thisLine[19:lineLength-1]
            temporaryHostList[1] = thisWGClientIP
            thisWGClientIPSplitted = thisWGClientIP.split('.')
            firstThreeOctets = thisWGClientIPSplitted[0] + thisWGClientIPSplitted[1] + thisWGClientIPSplitted[2]
            temporaryHostList[2] = firstThreeOctets

            # WireGuard allowed ips might have /32 at the end, remove that as it causes problems for the sortKey
            stringPositionOfSlash32 = thisWGClientIPSplitted[3].find("/")
            if stringPositionOfSlash32 != -1:
                thisWGClientIPSplitted[3] = (thisWGClientIPSplitted[3])[:-3]

            sortKey = generateSortKey(thisWGClientIPSplitted)            
            temporaryHostList[3] = sortKey
            WGClientIPFound = 1

        if ((textblockIsEthernetInterface) and not (textblockIsWireGuardInterface) and not (textblockIsWireGuardClient)):
            # When name and IP of netmask is found, add details to list
            if ((interfaceIPfound) and (interfaceNetmaskFound) and (interfaceNameFound)):
                temporaryInterfaceList[6] = "ethernet"
                interfaces.append(temporaryInterfaceList)
                # Reset variables, get ready for finding another interface/network
                interfaceNameFound = 0
                interfaceIPfound = 0
                interfaceNetmaskFound = 0
                textblockIsEthernetInterface = 0
                temporaryInterfaceList = ["","","","","","",""]
        
        if ((textblockIsWireGuardInterface) and not (textblockIsEthernetInterface) and not (textblockIsWireGuardClient)):
            # When details are found, add details to list
            if ((interfaceNameFound) and (interfaceWGAddressFound)):
                temporaryInterfaceList[6] = "wg"
                interfaces.append(temporaryInterfaceList)
                # Reset variables, get ready for finding another interface/network
                interfaceNameFound = 0
                interfaceWGAddressFound = 0
                textblockIsWireGuardInterface = 0
                temporaryInterfaceList = ["","","","","","",""]
        
        if ((textblockIsWireGuardClient) and not (textblockIsEthernetInterface) and not (textblockIsWireGuardInterface)):
            # When details are found, add details to list
            if ((WGClientNameFound) and (WGClientIPFound)):
                hosts.append(temporaryHostList)
                # Reset variables, get ready for finding another interface/network
                WGClientNameFound = 0
                WGClientIPFound = 0
                textblockIsWireGuardClient = 0
                correspondingWGInterfaceName = 0
                temporaryHostList = ["","","","","",""]              

# Read dhcp (clients) config file
with open("dhcp", "r") as dhcpFile:
    intputFileDHCP = dhcpFile.read()
    lines = intputFileDHCP.split('\n')

    # Look for hosts, add them to temporary list
    for thisLine in lines:
        stringPositionOfHostStarter = thisLine.find("config host")
        if stringPositionOfHostStarter == 0:
            hostNumber += 1
        
        # Find name of this host
        stringPositionOfHostIP = thisLine.find("option name")
        if stringPositionOfHostIP != -1:
            lineLength = len(thisLine)
            thisName = thisLine[14:lineLength-1]
            temporaryHostList[0] = thisName
            hostNameFound = 1
        
        # Find IP of this host
        stringPositionOfHostIP = thisLine.find("option ip")
        if stringPositionOfHostIP != -1:
            lineLength = len(thisLine)
            thisIP = thisLine[12:lineLength-1]
            temporaryHostList[1] = thisIP
            thisIPSplitted = thisIP.split('.')
            firstThreeOctets = thisIPSplitted[0] + thisIPSplitted[1] + thisIPSplitted[2]
            temporaryHostList[2] = firstThreeOctets
            sortKey = generateSortKey(thisIPSplitted)
            temporaryHostList[3] = sortKey
            temporaryHostList[5] = "dhcp"
            hostIPFound = 1
        
        # When name and IP of host is found, add details to list
        if ((hostNameFound) and (hostIPFound)):
            hosts.append(temporaryHostList)
            # Reset variables, get ready for finding another interface/network
            hostNameFound = 0
            hostIPFound = 0
            temporaryHostList = ["","","","","",""]

if importHostsFile in ("y", "yes"):
    # Read hosts (manually added clients) file
    with open("hosts", "r") as hostsFile:
        intputFileHosts = hostsFile.read()
        lines = intputFileHosts.split('\n')
        
        # Look for hosts, add them to temporary list
        for thisLine in lines:
            # Some text editors insert a newline character at the end of the last line, that will give an empty line at the bottom.
            # If the length of this line is 0 or 1, stop processing this line.
            if len(thisLine) <= 1:
                continue
            stringPositionOfSpace = thisLine.find(" ")
            hostNumber += 1
            
            # Find name of this host
            thisName = thisLine[0:stringPositionOfSpace]
            temporaryHostList[0] = thisName
            
            # Find IP of this host
            lineLength = len(thisLine)
            thisIP = thisLine[stringPositionOfSpace+1:lineLength]
            temporaryHostList[1] = thisIP
            thisIPSplitted = thisIP.split('.')
            firstThreeOctets = thisIPSplitted[0] + thisIPSplitted[1] + thisIPSplitted[2]
            temporaryHostList[2] = firstThreeOctets
            
            sortKey = generateSortKey(thisIPSplitted)
            temporaryHostList[3] = sortKey
            temporaryHostList[5] = "manual" 
            hosts.append(temporaryHostList)
            temporaryHostList = ["","","","","",""]

# All information about interfaces/networks and clients is found
# Remove the first item in each list, which is empty. And the loopback interface
interfaces.pop(0)
hosts.pop(0)
interfaces = [x for x in interfaces if x[0] !="loopback"]

# Sort interfaces/networks by IP
interfacesSorted = sorted(interfaces, key=lambda x: x[5])
# Sort clients by IP
hostsSorted = sorted(hosts, key=lambda x: x[3])

# Start generating the output text
NwDiagInputText = " nwdiag{Internet[shape=cloud];Internet -- OpenWrt;"

for thisInterface in interfacesSorted: 
    # This is looping over interfaces
    # First add network name
    NwDiagInputText += "network "
    NwDiagInputText += str(thisInterface[0])
    # If requested, show that this is a WireGuard interface, not a local interface
    if thisInterface[6] == "wg":
        if WGInterfaceSuffix in ("y", "yes"):
            NwDiagInputText += "-WG"
        else:
            if WGInterfaceSuffix not in ("n", "no"):
                NwDiagInputText += WGInterfaceSuffix
 
    # Add network range
    NwDiagInputText += '{address="'
    interfaceSubnet = thisInterface[1].split('.')
    # For WireGuard interfaces, we want to show the full IP
    if thisInterface[6] == "wg":
        NwDiagInputText += str(interfaceSubnet[0]) + "." + str(interfaceSubnet[1]) + "." + str(interfaceSubnet[2]) + "." + str(interfaceSubnet[3])
    # For Ethernet interfaces, we want to show the subnet that is used on the LAN. E.g. 192.168.1.x/24
    if thisInterface[6] != "wg":
        NwDiagInputText += str(interfaceSubnet[0]) + "." + str(interfaceSubnet[1]) + "." + str(interfaceSubnet[2]) + ".x"
        NwDiagInputText += "/"
        NwDiagInputText += str(thisInterface[4])
    NwDiagInputText += '";'
    # Add host details for OpenWrt
    NwDiagInputText += "OpenWrt" #Using OpenWrt as hostname for the device this config is sourced from
    NwDiagInputText += '[address="'
    NwDiagInputText += thisInterface[1]
    NwDiagInputText += '"];'
    # Now add other hosts in this network, taken from DHCP file and hosts file
    for thisHost in hostsSorted:
        if thisHost[5] == "dhcp" or thisHost[5] == "manual":
            # Check that the first three octetes from the host IP match the first three octets from the interface IP
            # # This works as long as it's a /24 subnet (netmask 255.255.255.0)
            if thisHost[2] == thisInterface[2]:
                # firstThreeOctets matches, add information about this client to this interface/network
                NwDiagInputText += '"'
                NwDiagInputText += thisHost[0]
                NwDiagInputText += '"[address="'
                NwDiagInputText += thisHost[1]
                NwDiagInputText += '"];'
        
        if thisHost[5] == "wg":
            if thisHost[4] == thisInterface[0]:
                # This host belongs to this interface
                NwDiagInputText += '"'
                NwDiagInputText += thisHost[0]
                NwDiagInputText += '"[address="'                
                NwDiagInputText += thisHost[1]
                NwDiagInputText += '"];'

    # Completed adding hosts. This interface is complete
    NwDiagInputText += "}"

# Completed adding networks. Output is completed
NwDiagInputText += "}"
print (NwDiagInputText)