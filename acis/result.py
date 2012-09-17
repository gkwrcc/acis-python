""" Classes for working with ACIS JSON results.

The goal of this module is to provide a common interface regardless of the call
(StnData, MultiStnData, etc.) that generated the result. If the result contains
metadata they will be stored as a dict keyed by site identifier. If a result
contains data they will also be stored as a dict keyed to the same identifer
used for the metadata. Iterating over a StnData or MultiStnData result will
yield data in the same format.

These classes are designed to used with their request module counterparts, but
this is not mandatory. A current limitation is the handling of "groupby"
results; see the class documentation for specifics. GridData and General call
results are not currently implemented.

This implementation is based on ACIS Web Services Version 2:
    <http://data.rcc-acis.org/doc/>.

"""
from .__version__ import __version__

import itertools

from .date import date_range
from .error import RequestError
from .error import ResultError

__all__ = ("StnMetaResult", "StnDataResult", "MultiStnDataResult")


class _JsonResult(object):
    """ Abstract base class for all result objects.

    """
    def __init__(self, query):
        """ Initialize a _JsonResult object.

        The query parameter is a dict containing the "params" dict that was
        sent to the server and the "result" dict that it returned.

        """
        # Error checking.
        try:
            params = query["params"]
            result = query["result"]
        except KeyError:
            raise ValueError("missing required params and/or result values")
        try:
            raise ResultError(result["error"])
        except KeyError:  # no error
            return


class StnMetaResult(_JsonResult):
    """ A result from a StnMeta call.

    The meta attribute is a dict keyed to the ACIS site UID, so this field
    must be included in the result metadata.

    """
    def __init__(self, query):
        """ Initialize a StnMetaResult object.

        """
        super(StnMetaResult, self).__init__(query)
        meta = query["result"]["meta"]
        try:
            self.meta = {site.pop("uid"): site for site in meta}
        except KeyError:
            raise ResultError("metadata does not contain uid")
        return


class _DataResult(_JsonResult):
    """ Abstract base class for station data results.

    _DataResult objects have data, meta, and smry attributes corresponding to
    the data, metadata, and summary result in the result object. Each attribute
    is a dict keyed to the ACIS site UID so this field must be included in the
    result metadata. The elems attribute is a tuple of element names for this
    result.

    """
    def __init__(self, query):
        """ Initialize a _DataResult object.

        """
        super(_DataResult, self).__init__(query)
        self.data = {}
        self.meta = {}
        self.smry = {}
        elems = query["params"]["elems"]
        try:  # a comma-delimited string?
            self.elems = tuple([elem.strip() for elem in elems.split(",")])
        except AttributeError:  # no split()
            try:  # a sequence of dicts?
                self.elems = tuple([elem["name"] for elem in elems])
            except TypeError:  # no string indices
                self.elems = tuple(elems) # a sequence of strings
        return

    def __len__(self):
        """ Return the number of data records in this result.

        For "groupby" results this will be the number of groups, not individual
        records.

        """
        count = 0
        for uid in self.data:
            count += len(self.data[uid])
        return count

    def __iter__(self):
        """ Iterate over all data records.

        Each record is of the form (uid, date, elem1, ...). Each element will
        be a single value or a list depending on how it was specified in the
        original call (e.g. [value, flag, time]). Iterating over a "groupby"
        result might give unexpected results; see the specific class
        documentation for details.

        """
        raise NotImplementedError


class StnDataResult(_DataResult):
    """ A result from a StnData call.

    The interface is the same as for StnMetaResult and MultiStnDataResult even
    though this is only for a single site.

    """
    def __init__(self, query):
        """ Initialize a StnDataResult object.

        """
        super(StnDataResult, self).__init__(query)
        result = query["result"]
        try:
            uid = result["meta"].pop("uid")
        except KeyError:
            raise ResultError("metadata does not contain uid")
        self.meta[uid] = result["meta"]
        self.data[uid] = result["data"]
        self.smry[uid] = result.get("smry", [])
        return

    def __iter__(self):
        """ Iterate over all data records.

        Records are in chronological order. For a "groupby" result this will 
        iterate over each group, not each individual record.

        """
        for uid, data in self.data.items():
            for record in data:
                record.insert(0, uid)
                yield record
        return


class MultiStnDataResult(_DataResult):
    """ A MultiStnData result.

    """
    def __init__(self, query):
        """ Initialize a MultiStnDataResult object.

        """
        super(MultiStnDataResult, self).__init__(query)
        self._dates = tuple(date_range(query["params"]))
        for site in query["result"]["data"]:
            try:
                uid = site["meta"].pop("uid")
            except KeyError:
                raise ResultError("metadata does not contain uid")
            self.meta[uid] = site["meta"]
            # For single-date requests MultStnData returns the single record
            # for each site as a 1D list instead of a 2D list, i.e. no time
            # dimension. (StnData returns a 2D list no matter what.)
            #
            # self.data[uid] = site["data"]  # preferred
            data1d = len(self._dates) == 1
            self.data[uid] = [site["data"]] if data1d else site["data"]
            # END WORKAROUND
            try:
                self.smry[uid]  = site["smry"]
            except KeyError:  # no "smry"
                continue
        return

    def __iter__(self):
        """ Iterate over all data records.

        Records are grouped by site and in chronological order for each site.
        For a "groupby" result this will yield each group, not each individual
        record.

        IN THE CURRENT IMPLEMENTATION THE DATES FOR A "GROUPBY" RESULT WILL NOT
        BE CORRECT.

        """
        # TODO: Correct dates for "groupby" results, c.f. date_range().
        date_iter = itertools.cycle(self._dates)
        for uid, data in self.data.items():
            for record in data:
                record.insert(0, uid)
                record.insert(1, date_iter.next())
                yield record
        return
