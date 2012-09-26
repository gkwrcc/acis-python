""" Miscellaneous implementation functions.

"""
import collections

from .date import date_object
from .date import date_string
from .error import RequestError

def annotate(sequence):
    """ Annotate duplicate items in a sequence to make them unique.
    
    Duplicate items will be indexed, e.g. (abc0, abc1, ...). The original order
    of the sequence is preserved, and it is returned as a tuple.
    
    """
    # Reverse the sequence, then the duplicate count acts as a reverse index 
    # while successive duplicates are annotated and the count is decremented. 
    # Reverse the sequence again to restore the orignal order.
    annotated = list(reversed(sequence))
    for key, count in collections.Counter(annotated).items():
        if not count > 1:
            continue
        for pos, item in enumerate(annotated):
            if item != key:
                continue
            count -= 1
            annotated[pos] = item + "{0:d}".format(count)
    return tuple(reversed(annotated))             

    
def date_params(sdate, edate=None):
    """ Set the date range (inclusive) for this request.

    If "edate" is None "sdate" is treated as a single date. The parameters must
    be a date string or "por" (period of record). Acceptable date formats are 
    YYYY-[MM-[DD]] (hyphens are optional but leading zeroes are not; no two-
    digit years).

    """
    verify = lambda s: date_string(date_object(s))
    params = {}
    if edate is None:
        if sdate.lower() == "por":  # entire period of record
            params["sdate"] = params["edate"] = "por"
        else:  # single date
            params["date"] = "por" if sdate.lower() == "por" else verify(sdate)
    else:
        params["sdate"] = "por" if sdate.lower() == "por" else verify(sdate)
        params["edate"] = "por" if edate.lower() == "por" else verify(edate)
    return params


def valid_interval(value):
    """ Return a valid ACIS interval.
    
    An interval can be specified as a name ("dly", "mly", "yly") or a year,
    month, day sequence. For a sequence, only the least-signficant nonzero 
    value is used.
    
    """
    try:
        value = value.lower()
    except AttributeError:  # no lower(), not a str
        # Normalize a (y, m, d) sequence of ints.
        try:  
            yr, mo, da = (int(x) for x in value)
        except ValueError:  # not ints
            raise RequestError("invalid interval: {0:s}".format(value))
        mo = 0 if da > 0 else mo
        yr = 0 if (mo > 0 or da > 0) else yr
        value = (yr, mo, da)             
    else:
        if value not in ("dly", "mly", "yly"):
            raise RequestError("invalid interval name: {0:s}".format(value))
    return value


def date_span(params):
    """
    Determine a request's start date, end date, and interval from params.
    
    If there is no end date it will None. If there is no interval it will be
    "dly".
    
    """
    try:
        sdate = params["sdate"]
    except KeyError:
        sdate = params["data"]
    edate = params.get("edate", None)
    try:
        # All elements must have the same interval, so check the first 
        # element for an interval specification.
        interval = params["elems"][0]["interval"]
    except (TypeError, KeyError): # not an array or no interval defined
        interval = "dly"  # default value is daily
    return sdate, edate, interval