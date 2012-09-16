""" Classes for streaming ACIS CSV data.

A stream class is an all-in-one for constructing a CSV data request and then
accessing the result. CSV calls are very restricted compared to JSON calls, but
the output can be streamed one record at a time rather than as a single JSON
object; this can be useful for large data requests. Metadata is stored as dict
keyed to a site identifer. Data records are streamed using the iterator
interface. The elems attribute is a tuple of element names for this stream.
See the call, request, and result modules if a CSV request is too limited.

This implementation is based on ACIS Web Services Version 2:
    <http://data.rcc-acis.org/doc/>.

"""
from .__version__ import __version__

import itertools

from .call import WebServicesCall
from .error import RequestError

__all__ = ("StnDataStream", "MultiStnDataStream")


class _CsvStream(object):
    """ Abstract base class for all CSV output.

    CSV output can be streamed, which might be useful for large requests.
    Derived classes must define the _call attribute with the appropriate
    WebServicesCall.

    """
    _call = None  # derived class must define a WebServicesCall

    def __init__(self):
        """ Initialize a _CsvStream object.

        """
        self.meta = {}
        self._params = {"output": "csv", "elems": []}
        self._interval = "dly"
        return

    @property
    def elems(self):
        """ Getter method for the elems attribute.

        """
        return tuple(elem["name"] for elem in self._params["elems"])

    def interval(self, value):
        """ Set the interval for this request.

        The default interval is daily ("dly").
        """
        if value not in ("dly", "mly", "yly"):
            raise RequestError("invalid interval: {0:s}".format(value))
        self._interval = value
        return

    def add_element(self, name, **options):
        """ Add an element to this request.

        Adding an element that already exists will overwrite the existing
        element.
        """
        new_elem = dict([("name", name)] + options.items())
        elements = self._params["elems"]
        for pos, elem in enumerate(elements):
            if elem["name"] == name:
                elements[pos] = new_elem
                break
        else:
            elements.append(new_elem)
        return

    def del_element(self, name=None):
        """ Delete all or just "name" from the requested elements.

        """
        if name is None:
            self._params["elems"] = []
        elements = self._params["elems"]
        for pos, elem in enumerate(elements):
            if elem["name"] == name:
                elements.pop(pos)
                break
        return

    def __iter__(self):
        """ Stream the records from the server.

        """
        first_line, stream = self._connect()
        line_iter = itertools.chain([first_line], stream)
        self._header(line_iter)
        for line in line_iter:
            yield self._record(line.rstrip())
        stream.close()
        return

    def _connect(self):
        """ Connect to the ACIS server.

        Execute the web services call, check for success, and return the first
        line and the stream object.

        """
        for elem in self._params['elems']:
            elem['interval'] = self._interval
        stream = self._call(self._params)
        first_line = stream.readline().rstrip()
        if first_line.startswith("error"):  # "error: error message"
            raise RequestError(first_line.split(":")[1].lstrip())
        return first_line, stream

    def _header(self, line_iter):
        """ Read the stream header.

        Derived classes should override this if the stream contains any header
        information. The iterator must be advanced to the first line of data.

        """
        return  # no header

    def _record(self, line):
        """ Process a line of data from the server.

        Each derived class must implement this to return a record of the form
        (sid, date, elem1, ...).

        """
        raise NotImplementedError


class StnDataStream(_CsvStream):
    """ A StnData stream.

    """
    _call = WebServicesCall("StnData")

    def location(self, **options):
        """ Set the location for this request.

        StnData only accepts a single "uid" or "sid" parameter.

        """
        for key in ("uid", "sid"):  # uid takes precedence
            try:
                self._sid = self._params[key] = options[key]
            except KeyError:
                continue
            break
        else:
            raise RequestError("StnDataStream requires uid or sid")
        return

    def dates(self, sdate, edate=None):
        """ Set the date range (inclusive) for this request.

        If no "edate" is specified "sdate" is treated as a single date. The
        parameters must be a date string or the value "por" which means to
        extend to the period-of-record in that direction. Acceptable date
        formats are YYYY-[MM-[DD]] (hyphens are optional but leading zeroes are
        not; no two-digit years).

        """
        # TODO: Need to validate dates.
        if edate is None:
            if sdate.lower() == "por":  # entire period of record
                self._params["sdate"] = self._params["edate"] = "por"
            else:  # single date
                self._params["date"] = sdate
        else:
            self._params["sdate"] = sdate
            self._params["edate"] = edate
        return

    def _header(self, line_iter):
        """ Read the stream header.

        """
        # The first line is the site name.
        self.meta[self._sid] = {"name": line_iter.next()}
        return

    def _record(self, line):
        """ Process a line of data from the server.

        """
        return [self._sid] + line.split(",")


class MultiStnDataStream(_CsvStream):
    """ A MultiStnData stream.

    """
    _call = WebServicesCall("MultiStnData")

    def date(self, date):
        """ Set the date for this request.

        MultStnData only accepts a single date for CSV output. Acceptable date
        formats are YYYY-[MM-[DD]] (hyphens are optional but leading zeroes
        are not; no two-digit years).

        """
        # TODO: Need to validate date.
        self._params["date"] = date
        return

    def location(self, **options):
        """ Set the location for this request.

        """
        # TODO: Need to validate options.
        self._params.update(options)
        return

    def _record(self, line):
        """ Process a line of data from the server.

        The meta attribute will not be fully populated until every line has
        been receieved.

        """
        # The metadata for each site--name, state, lat/lon, and elevation--is
        # part of its data record.
        record = line.split(",")
        try:
            sid, name, state, lon, lat, elev = record[:6]
        except ValueError:  # blank line at end of output?
            raise StopIteration
        self.meta[sid] = {"name": name, "state": state}
        try:
            self.meta[sid]["elev"] = float(elev)
        except ValueError:  # elev is blank
            pass
        try:
            self.meta[sid]["ll"] = [float(lon), float(lat)]
        except ValueError:  # lat/lon is blank
            pass
        return [sid, self._params["date"]] + record[6:]
