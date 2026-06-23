import re
from decimal import Decimal, ROUND_DOWN

def extract_truncated_version(version_name):
    version_name = version_name.replace('UCON_','')
    version_name = version_name.replace('CON_','')
    prefix = version_name[:2]
    suffix = get_last_two_digits(version_name)
    return (prefix + "_" + suffix)



def get_last_two_digits(alphanumeric_string):
    """
    Extracts the last two numeric digits from an alphanumeric string.
    Args:
        alphanumeric_string (str): The input string.
    Returns:
        str: The last two digits found in the string, or an empty string
             if fewer than two digits are present.
    """
    digits = re.findall(r'\d', alphanumeric_string)
    if len(digits) >= 2:
        return "".join(digits[-2:])
    else:
        return "".join(digits)
    
version=''
extract_truncated_version(version)    