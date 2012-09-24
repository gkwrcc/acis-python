""" ACIS utility functions.

This module contains various functions that can be useful for processing ACIS
data.

This implementation is based on ACIS Web Services Version 2:
    <http://data.rcc-acis.org/doc/>.

"""
from .__version__ import __version__

import re

__all__ = ("sids_table",)

_SID_REGEX = re.compile(r"^([^ ]*) (\d+)$")

_SID_TYPES = {
     1: "WBAN", 2: "COOP",  3: "FAA", 4: "WMO",       5: "ICAO",
     6: "GHCN", 7: "NWSLI", 8: "RCC", 9: "ThreadEx", 10: "CoCoRaHS"}


def sids_table(sids):
    """ Return a dict of site IDs keyed by their ID types.

    The parameter is a list of SIDs from ACIS metadata where each SID is a
    single string containing an identifier and its integer type code separated
    by a space, e.g. "13697 1".

    """
    table = {}
    for sid in sids:
        try:
            ident, code = _SID_REGEX.search(sid).groups()
        except AttributeError:  # search returned None
            raise ValueError("invalid SID: {0:s}".format(sid))
        try:
            table[_SID_TYPES[int(code)]] = ident
        except KeyError:
            raise ValueError("unknown SID type: {0:s}".format(code))
    return table
