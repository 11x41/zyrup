#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging

from os import path

#import gevent
import logging as gevent

from suds.client import Client
from suds.cache import FileCache
from suds.xsd.doctor import Import, ImportDoctor

from .util import generate_select_list, generate_search_conditions

logger = logging.getLogger(__package__)


def session_required(fn):
    """
    Decorator for functions that require a valid Zuora Session

    :param function:
    :return:
    """

    def check_session(arg, *args, **kwargs):
        if arg.login_required():
            try:
                login_result = arg.login()
                if 'Session' not in login_result:
                    return False
            except Exception as e:
                logger.error(e)
                return False
        return fn(arg, *args, **kwargs)
    return check_session


class Zuora(object):

    # The SOAP Client
    client = None

    # Settings
    _default_batch_min = _batch_min = 8
    _default_batch_max = _batch_max = 50
    _default_query_batch_size_max = _query_batch_size_max = 2000  # Batch size for query or queryMore.
    _batch_objects = ['create', 'update', 'delete', 'subscribe', 'amend']  # Todo: Test subscribe, amend

    # Session ID and Endpoint info
    __session_id = None
    __next_login_time = datetime.now()
    __session_length_millis = 600000
    __endpoint = None
    __session_header = None
    
    def __init__(self, **kwargs):
        """
        Connect to Zuora

        'wsdl' : Location of WSDL
        'cacheDuration' : Duration of HTTP GET cache in seconds, or 0 for no cache
        'username' : Username for HTTP auth when using a proxy ONLY
        'password' : Password for HTTP auth when using a proxy ONLY
        """
        # Suds can only accept WSDL locations with a protocol prepended
        wsdl = kwargs['wsdl']
        base_dir = path.dirname(__file__)
        wsdl = 'file:///%s' % path.abspath(base_dir + "/" + wsdl)

        cache_duration = 0
        if 'cache_duration' in kwargs:
            cache_duration = kwargs['cache_duration']
        if cache_duration > 0:
            cache = FileCache()
            cache.setduration(seconds=cache_duration)
        else:
            cache = None

        # Fix missing types with ImportDoctor
        schema_url = 'http://object.api.zyrup.com/'
        schema_import = Import(schema_url)
        schema_doctor = ImportDoctor(schema_import)

        self.client = Client(url=wsdl, cache=cache, doctor=schema_doctor)

        # Set HTTP headers for logging each request
        headers = {
            'User-Agent': Zuora.__name__ + '/' + '.'.join(str(x) for x in "1.0.0"),
            'Content-Type': 'text/xml; charset=utf-8'
        }

        # This HTTP header will not work until Suds gunzips/inflates the content
        # 'Accept-Encoding': 'gzip, deflate'
        self.client.set_options(headers=headers)
        if cache is None:
            self.client.set_options(cache=None)

        if 'username' in kwargs:
            self.client.set_options(username=kwargs['username'])
            self.username = kwargs['username']

        if 'password' in kwargs:
            self.client.set_options(password=kwargs['password'])
            self.password = kwargs['password']

        if 'session_length_millis' in kwargs:
            self.set_session_length_millis(kwargs['session_length_millis'])

        if 'query_batch_size' in kwargs:
            self.set_query_batch_size(kwargs['query_batch_size'])

        if 'batch_size' in kwargs:
            self.set_batch_sizes(kwargs['batch_size'])

    def query(self, query_string=None):
        """
        Executes the query specified and returns data that matches the criteria.

        Use query_batch_size to change the batch size.  Defaulted to 2000.

        :param query_string:
        :return:
        """
        return self.call(self.client.service.query, query_string)

    def query_more(self, query_locator):
        """
        Retrieves the next batch of objects from a query.
        """
        return self.call(self.client.service.queryMore, query_locator)

    def retrieve(self, z_object_type=None, field_list=[], id_list=[]):
        """
        Retrieves one or more objects based on the specified object ID(s).
        """
        if z_object_type is None:
            raise ValueError("z_object_type cannot be Blank")
        if not isinstance(field_list, (list, tuple)):
            raise NotImplemented("field_list must be a list, if empty only Id will be selected")
        if not isinstance(id_list, (list, tuple)):
            raise NotImplemented("id_list must be a list")
        if id_list is []:
            raise ValueError("id_list cannot be an empty list")

        select_list = generate_select_list(field_list)
        search_conditions = generate_search_conditions(values=id_list)

        query = "SELECT {select_list} FROM {z_object_type} WHERE {search_conditions}"
        query = query.format(select_list=select_list, z_object_type=z_object_type, search_conditions=search_conditions)
        return self.query(query)

    def subscribe(self, z_objects):
        return self.call(self.client.service.subscribe, z_objects)

    def create(self, z_objects):
        return self.call(self.client.service.create, z_objects)

    def update(self, z_objects):
        return self.call(self.client.service.update, z_objects)

    def delete(self, z_object_type, id_list=[]):
        return self.call(self.client.service.delete, z_object_type, id_list)

    def amend(self, amend_request):
        return self.call(self.client.service.amend, amend_request)

    @session_required
    def call(self, f=None, *args, **kwargs):
        self.set_headers(f.method.name)
        if f.method.name in self._batch_objects:
            if isinstance(args[0], list) and len(args[0]) > self._batch_min:
                z_objects_or_id_list = args[0]
                return self.__batch(f, z_objects_or_id_list)
            elif len(args) > 1 and isinstance(args[1], list) and len(args[1] > self._batch_min):
                z_object_type = args[0]
                z_objects_or_id_list = args[1]
                return self.__batch(f, z_objects_or_id_list, z_object_type)
        results = f(*args, **kwargs)
        if len(results) == 1:
            return results[0]
        return results

    @session_required
    def call2(self, f=None, *args, **kwargs):
        self.set_headers(f.method.name)
        if f.method.name in self._batch_objects:
            if isinstance(args[0], list):
                z_objects_or_id_list = args[0]
                return self.b.create_or_update(f, z_objects_or_id_list)
            elif len(args) > 1 and isinstance(args[1], list):
                z_object_type = args[0]
                z_objects_or_id_list = args[1]
                return self.b.delete(f, z_object_type, z_objects_or_id_list)
        results = f(*args, **kwargs)
        if len(results) == 1:
            return results[0]
        return results

    @session_required
    def __batch(self, f, z_objects_or_id_list, z_object_type=None):
        """ Batch the call so we can do more than the maximum per call (which is usually 50) """
        batches = []

        batch_max = self._batch_max
        object_or_id_count = len(z_objects_or_id_list)

        logger.info("%s items requested for batching (batch size is %s)" % (object_or_id_count, batch_max))

        if z_object_type is not None:
            for i in xrange(0, object_or_id_count, batch_max):
                # Todo: Change signature to use gevent...also, so it doesn't call Zuora right away...
                batches.append(f(z_object_type, z_objects_or_id_list[i:self._batch_max+i]))

                # This way will they will need to be called in a loop
                # batches.append((f, z_object_type, z_objects_or_id_list[i:self._batch_max+i]))


                    #gevent.spawn(
                        #[f(z_object_type, z_objects_or_id_list[i:self._batch_max+i])]
                    #)
                #)
        else:
            for i in xrange(0, object_or_id_count, batch_max):
                batches.append(f(z_objects_or_id_list[i:self._batch_max+i]))
                    #gevent.spawn(
                        #[f(z_objects_or_id_list[i:self._batch_max+i])]
                    #)
                #)

        logger.info("%s items placed into %s batches" % (object_or_id_count, len(batches)))

        #gevent.joinall(batches, timeout=2)

        #results = [batch.value for batch in batches]
        results = batches

        logger.info("Total results...%s" % len(results))

        return results
    # Toolkit-specific methods
    def generate_header(self, z_object_type):
        """
        Generate a SOAP header as defined in:
        http://www.salesforce.com/us/developer/docs/api/Content/soap_headers.htm
        """
        try:
            return self.client.factory.create(z_object_type)
        except Exception as e:
            self.logger.info('There is not a SOAP header of type %s' % z_object_type)

    def generate_object(self, object_type):
        """
        Generate a Zuora object, such as a Account or Contact
        """
        if object_type in ("Contact", "RatePlanCharge"):
            object_type = "{http://object.api.zuora.com/%s}" % object_type
        obj = self.client.factory.create(object_type)
        return obj

    def set_headers(self, call=None):
        """
        Return SOAP headers to the request depending on the method call made
        """
        # All calls, including utility calls, set the session header
        headers = {
            'SessionHeader': self.__session_header,
        }
        if call in ('query', 'queryMore'):
            query_options = self.client.factory.create('QueryOptions')
            query_options.batchSize = self._query_batch_size_max
            headers['QueryOptions'] = query_options

        self.client.set_options(soapheaders=headers)

    def set_endpoint(self, endpoint):
        """
        Set the endpoint after when Zuora returns the URL after successful login()

        Changes URL to point from test.zyrup.com to something like cs2-api.zyrup.com
        """
        # suds 0.3.7+ supports multiple wsdl services, but breaks setlocation :(
        # see https://fedorahosted.org/suds/ticket/261
        try:
            self.client.set_options(location=endpoint)
        except:
            self.client.wsdl.service.setlocation(endpoint)

        # Store endpoint
        self.__endpoint = endpoint

    # TODO: Move login to it's own class.
    def login(self):
        """
        Login to Zuora and starts a client session.

        return LoginResult
        """
        login_result = self.client.service.login(self.username, self.password)

        # set new endpoint
        self.set_endpoint(login_result['ServerUrl'])

        # set session header
        header = self.generate_header('SessionHeader')
        header.session = login_result['Session']
        self.set_session_header(header)
        self.set_session_id(login_result['Session'])
        self.set_next_login_time(
            datetime.now() + timedelta(microseconds=self.__session_length_millis * 1000)
        )

        self.set_headers()
        return login_result

    def login_required(self):
        if self.__session_id is None or len(self.__session_id) == 0:
            return True
        else:
            return not self.connection_alive()

    def connection_alive(self):
        return datetime.now() < self.__next_login_time

    def set_next_login_time(self, next_login_time):
        self.__next_login_time = next_login_time

    def set_session_length_millis(self, session_length_millis):
        self.__session_length_millis = session_length_millis

    def set_session_id(self, session_id):
        self.__session_id = session_id

    def set_session_header(self, header):
        self.__session_header = header

    def set_query_batch_size(self, size):
        if size > self._default_query_batch_size_max:
            raise ValueError("Max Query Batch Size must be set between 0 and %s" % self._default_query_batch_size_max)
        elif size == 0:
            return
        try:
            self._query_batch_size_max = int(size)
        except TypeError:
            raise TypeError("Query Batch Sizes must be integers set between 0 and %s" %
                            self._default_query_batch_size_max)

    def set_batch_sizes(self, sizes):
        min_batch = max_batch = 0
        if isinstance(sizes, tuple):
            min_batch, max_batch = sizes
        else:
            max_batch = sizes

        if min_batch == 0:
            min_batch = self._default_batch_min
        if max_batch == 0:
            max_batch = self._default_batch_max

        if min_batch > self._default_batch_max:
            raise ValueError("Min Batch Size must be set between 0 and %s, but recommended value is %s" %
                             (self._default_batch_max, self._default_batch_min))
        if max_batch > self._default_batch_max:
            raise ValueError("Max Batch Size must be set between 0 and %s" % self._default_batch_max)

        self._batch_min = int(min_batch)
        self._batch_max = int(max_batch)

    def get_batch_sizes(self):
        batch_min = self._default_batch_min
        batch_max = self._default_batch_max
        if self._batch_min:
            batch_min = self._batch_min
        if self._batch_max:
            batch_max = self._batch_max
        return batch_min, batch_max