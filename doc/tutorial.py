"""
*** Introduction ***

The acis library provides tools for working with data from the Applied Climate
Information System (ACIS):
    <http://data.rcc-acis.org>.

This tutorial shows how the library can be used to retrieve and read ACIS data.
Familiarity with the ACIS Web Services documentation would be helpful in
understanding the terms used here:
    <http://data.rcc-acis.org/doc>

Follow along with the output of the examples in this file by executing it:
    python tutorial.py > tutorial.txt


*** Installing the Library ***

The latest version of the library can be found at GitHub:
    <https://github.com/mdklatt/acis-python>

The library can retrieved using git or downloaded as a zip file. All the
required files can be found in the acis directory under the project root
directory. In order to be usable the acis directory must be in the Python
import path. By default, Python searches the local directory, the user's
site-packages directory, and the system-wide site-packages directory. For use
with a single application, it is sufficient to copy the acis directory to the
application directory. To install the library in the user's site-packages
directory, used the setup.py script included in the project directory:
    python setup.py install --user


*** Using the Library ***

To use the library, simply import it into the application. This will cause an
error if the library is not visible in the import path.

"""
import acis
print "Using acis library v{0:s}".format(acis.__version__)


"""
*** Using WebServicesCall ***

The core component of the library is the WebServicesCall class. This class
takes care of encoding the parameters for the ACIS call, communicating with the
server, and decoding the result. The user is responsible for creating the
params object and interpreting the result object. This provides the most
flexibility but also requires the most knowledge of the ACIS protocol.

For the first example, let's retrieve the maximum temperature for Oklahoma City
on August 3, 2012 using a StnData call. A params object (a dict) is created,
the call is made, and the result is displayed. Note that the data values are
strings, which allows for special values like "T" or "M". The user must check
for these values and convert to a number as necessary.

"""
print "EXAMPLE 1\n"
acis_call = acis.WebServicesCall("StnData")
params = {"sid": "OKC", "date": "2012-08-03", "elems": "maxt", "meta": "name"}
result = acis_call(params)
site_name = result["meta"]["name"]
date, maxt = result["data"][0]  # first and only record
print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(site_name,
    date, maxt)
print "-"*40



"""
If the params object is not valid the server will respond with an error
and WebServicesCall will raise an execption.

"""
print "EXAMPLE 2\n"
acis_call = acis.WebServicesCall("StnData")
params = {"date": "2012-08-03", "elems": "mint,maxt"}  # oops, no site
try:
    result = acis_call(params)
except acis.RequestError as err:
    print "Oops: {0:s}".format(err.message)
print "-"*40



"""
*** Using Requests ***

The Request class hierarchy simplifies the process of executing an ACIS call by
managing the params object. There is a Request class for each type of ACIS
call: StnMetaRequest, StnDataRequest, and MultiStnDataRequest (the GridData and
General calls are not currently supported--use a WebServicesCall). Each Request
has methods for defining the options appropriate to that request.

Let's repeat the first example using a StnDataRequest. The user does not have
to create a params object but does have to interpret the result object. A
Request returns a query object (another dict) containining both the params
object it created and the result object from the server.

"""
print "EXAMPLE 3\n"
request = acis.StnDataRequest()
request.location(sid="OKC")  # must specify sid or uid
request.dates("2012-08-03")  # single date OK
request.add_element("maxt")  # must add elements one at a time
request.metadata("name")     # multiple arguments okay
query = request.submit()     # {"params": params, "result": result}
result = query["result"]
site_name = result["meta"]["name"]
date, maxt = result["data"][0]
print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(site_name,
    date, maxt)
print "-"*40



"""
The request methods use keyword arguments to specify the various options that
can make up an ACIS call. In most cases these keywords correspond to the same
options that are used in the params object, so familiarity with the ACIS call
syntax is important. For example, a StnMeta call accepts a "uid" or "sid" value
so StnDataRequest requires a uid or sid keyword argument.

"""
print "EXAMPLE 4\n"
request = acis.StnDataRequest()
try:
    request.location("OKC")  # oops, no keyword--is this a sid or uid?
except TypeError:
    print "Oops: forgot a keyword for location"
try:
    request.location(id="OKC")  # oops, wrong keyword
except acis.RequestError as err:
    print "Oops: {0:s}".format(err.message)
print "-"*40



"""
StnDataRequest and MultiStnDataRequests both require date ranges, as given in
a call to dates(). Use a single argument for a single date, or two arguments
to specify the a date range (inclusive). The dates must be in an acceptable
string format, i.e. YYYY, YYYY-MM, or YYYY-MM-DD. The hyphens are optional,
but the year must be 4 digits and the month and day must be 2 digits. A StnData
call also accepts "por" insted of a date string; this means extend for the
period of record in that direction. A single "por" value for dates() will
retrieve the entire period of record for that site.

Let's retrieve all max and min temps for Oklahoma City since September 1, 2012.

"""
print "EXAMPLE 5\n"
request = acis.StnDataRequest()
request.location(sid="OKC")
request.dates("2012-09-01", "por")
request.add_element("maxt")
request.add_element("mint")
request.metadata("name")
query = request.submit()
print query["result"]["meta"]["name"]
for record in query["result"]["data"]:
    date, maxt, mint = record
    print "On {0:s} the high was {1:s}F, and the low was {2:s}F.".format(date,
        maxt, mint)
print "-"*40



"""
By default an ACIS call retrieves daily data, but this can be changed using
the interval() method for StnDataRequest and MultiStnDataRequest. Valid
intervals are "dly" (daily), "mly" (monthly), and "yly" (yearly). When an
using an interval other than daily, a reduction must be specified. Each element
will have the same interval, but they can have their own reductions and summary
values.

Let's get the monthly maximum temperature, minimum temperature, and maximum
daily rainfall for Oklahoma City for August 2012, along with the dates of each
occurrence. The additional options for each element must be specified using
keyword arugments. Note that the reduce option in this case must be specified
as a dict because of the "add" option.

"""
print "EXAMPLE 6\n"
request = acis.StnDataRequest()
request.location(sid="OKC")
request.dates("2012-08")  # monthly, don't need day
request.interval("mly")
request.add_element("maxt", reduce={"reduce": "max", "add": "date"})
request.add_element("mint", reduce={"reduce": "min", "add": "date"})
request.add_element("pcpn", reduce={"reduce": "max", "add": "date"})
request.metadata("name")
query = request.submit()
date, maxt, mint, pcpn = query["result"]["data"][0]
print "***{0:s} -- AUGUST 2012***".format(query["result"]["meta"]["name"])
print "The maximum temperature of {0:s}F occurred on {1:s}.".format(*maxt)
print "The minimum temperature of {0:s}F occurred on {1:s}.".format(*mint)
print "The maximum rainfall of {0:s}\" occurred on {1:s}.".format(*pcpn)
print "-"*40


"""
*** Using Results ***

The Result class hierarchy simplifies the interpretation of an ACIS result
object. These classes are designed to be used with their corresponding Request
classes, but this is not mandatory. There is a Result class for each type of
ACIS call: StnMetaResult, StnDataResult, and MultiStnDataResult (the GridData
and General calls are not currently supported--use the result object from a
WebServicesCall).

The interface for the each type of Result is the same even though the
underlying result object has a different structure for each type of call.
All Results hava a meta attribute for accessing metadata. This is keyed to the
ACIS site UID, so this must be specifically requested as part of the metadata
(using a Request automatically takes care of this). StnDataResult and
MultiStnDataResult also have a data attribute and smry attribute for
accesssing the result's data and summary values, respectively. Like the meta
attribute, these attributes are keyed to the ACIS site UID. Results with a data
attribute support iteration, which yields each record in the result in the same
format regardless of the call type. A Result is initialized using a query
object containing the params object sent to the server and the result object
it sent back. Note that this is conveniently the output of a Request submit()
call.

Let's repeat the very first example, retrieving the maximum temperature for
Oklahoma City for August 3, 2012. Iteration is used to illustrate the concept
even though this is for a single day at a single site.

"""
print "EXAMPLE 7\n"
request = acis.StnDataRequest()  # request type must match result type
request.location(sid="OKC")
request.dates("2012-08-03")
request.add_element("maxt")
request.metadata("name")  # uid is automatically added
result = acis.StnDataResult(request.submit())
for record in result:
    uid, date, maxt = record
    print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(
            result.meta[uid]["name"], date, maxt)
print "-"*40


"""
Using a MultiStnDataResult is the same as using a StnDataResult even though the
actual result object from a MultiStnData call will be much more complicated. A
MultiStnDataResult calculates the date for each data record based on the params
object used to generate the data. (NOTE: due to a limiation in the current
version, "groupby" results will NOT give the correct date.)

Let's repeat the example above, but this time with multiple dates and sites.
Very little code has to be changed, and the output code doesn't have to be
changed at all.

"""
print "EXAMPLE 8\n"
request = acis.MultiStnDataRequest()  # change Request type
request.location(sids="OKC,TUL,LAW,MLC,GAG")  # change keyword and SID list
request.dates("2012-08-01", "2012-08-03")  # sdate and edate
request.add_element("maxt")
request.metadata("name")
result = acis.MultiStnDataResult(request.submit())  # change Result type
for record in result:
    uid, date, maxt = record
    print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(
       result.meta[uid]["name"], date, maxt)
print "({0:d} records returned)".format(len(result))  # Results support len()
print "-"*40


"""
A Result with a data attribute also has an elems attribute, which is a tuple of
the element names in the result. This can be used to refer to record fields by
name instead of index. Here's another version of the previous example using
named fields.

"""
print "EXAMPLE 9\n"
request = acis.MultiStnDataRequest()
request.location(sids="OKC,TUL,LAW,MLC,GAG")
request.dates("2012-08-01", "2012-08-03")
request.add_element("maxt")
request.metadata("name")
result = acis.MultiStnDataResult(request.submit())  # change Result type
for record in result:
    # Don't need to know the order or number of elements.
    (uid, date), elems = record[0:2], dict(zip(result.elems, record[2:]))
    print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(
       result.meta[uid]["name"], date, elems['maxt'])
print "({0:d} records returned)".format(len(result))
print "-"*40


"""
A potential drawback of using a Request/Result is that the entire result object
has to be received before the first record can be processed. With the Stream
classes, however, records can be streamed one by one from the server as soon as
its ready to return data. The total execution time will probably be the same
or even slightly longer for a Stream, but for large requests the delay between
executing the call and the start of data processing might be shorter.

The StnDataStream and MultiStnDataStream classes are used to both generate the
data request (like a Resquest) and iterate over the result (like a Result).
Streams are implemented using ACIS CSV output, so they are only available for
a subset of StnData and MultiStnData calls. Metadata options are fixed for each
type of call. Advanced element options, like "add", are not allowed. Only one
date is allowed for a MultiStnData call. Like a Result, streams have an elems
attribute and a meta attribute that is populated as records are received.

This is a MultiStnDataStream version of the previous example, except that it's
limited to a single date. The code is similar to the Request/Result version.

"""
print "EXAMPLE 10\n"
stream = acis.MultiStnDataStream()
stream.location(sids="OKC,TUL,LAW,MLC,GAG")
stream.date("2012-08-03")  # date() not dates()
stream.add_element("maxt")
count = 0
for record in stream:
    count += 1
    (sid, date), elems = record[0:2], dict(zip(stream.elems, record[2:]))
    print "The high temperature for {0:s} on {1:s} was {2:s}F.".format(
       stream.meta[sid]["name"], date, elems['maxt'])
print "({0:d} records returned)".format(count)  # Streams don't have len()
print "-"*40