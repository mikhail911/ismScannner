""" Function, which finds manufacturer of device by MAC address
Source: https://gist.github.com/aallan/b4bb86db86079509e6159810ae9bd3e4 """

def search_manufacturer_by_mac(mac):
    """ Search manufacturer by MAC address
    
    Args:
        mac(str): Mac address, ex. '00:00:EF:EE:FD:E1'.
    
    Returns:
        Function returns a string with name of manufacturer if exist in database, if not
        function returns None.
    """
    
    mac_vendors_file = open('src/vendors/mac-vendor.txt', 'r', encoding="utf8")
    mac_temp = mac.replace(':', '')[:6].split(" ")[0]
    for line in mac_vendors_file.readlines():
        if str(mac_temp) == str(line[:6]):
            return str(line[7:]).rstrip()
