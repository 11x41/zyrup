#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from datetime import datetime
import csv
import time
import logging
from urlparse import parse_qs

import re
import requests

from .base import Zuora


logger = logging.getLogger(__package__)


class ZuoraExport(Zuora):

    def export(self, z_object='', fields=[], filters='', sleep_seconds=5, max_tries=None):
        """
        Uses the Export object from Zuora to pull down a Datasource
        version of the object specified.
        """
        self.set_headers('export')
        logger.debug("Getting %ss" % z_object)

        logger.debug("Generating Export Object")
        fields = ", ".join(["%s" % f for f in fields])
        if filters == '':
            logger.debug("Query All")
            query = "SELECT %s FROM %s" % (fields, z_object)
        else:
            logger.debug("Query Filter")
            query = "SELECT %s FROM %s WHERE %s" % (fields,
                                                    z_object,
                                                    filters
                                                    )
        logger.debug(query)

        export = self.generate_object("Export")
        export.Name = '%s%s' % (z_object, time.time())
        export.Query = query
        export.Format = 'csv'
        results = self.create(export)

        if results.Success:
            logger.info('Export Object (%s) created' % results.Id)
            export_query = "SELECT status, fileId, query, size FROM Export WHERE Id ='%s'" % results.Id
            done = False

            tries = 0
            while (not done) and ((max_tries is None) or (tries < max_tries)):
                results = self.query(export_query)
                tries += 1
                if results.done:
                    if results.size == 1:
                        status = results.records[0].Status
                        done = True if status == 'Completed' else False
                if not done:
                    logger.debug("sleeping for %s..." % sleep_seconds)
                    time.sleep(sleep_seconds)
                else:
                    file_id = results.records[0].FileId
                    logger.debug("Returning file_id (%s)" % file_id)
                    return file_id
            if (max_tries is not None) and (tries >= max_tries):
                logger.error("Unable to retrieve export FileID from Zuora")
                return None
        else:
            logger.error(results)
            return None

    def download(self, file_id, filename=None, droppath=""):
        logger.info("Beginning download ....")
        auth = {
            "Authorization": "ZSession %s" % self._sessionId
        }

        o = parse_qs(self.__endpoint)
        try:
            loc = o.netloc
        except:
            loc = o.host
        url = "%s://%s/apps/api/file/%s" % (o.scheme, loc, file_id)
        r = requests.get(url, headers=auth)
        if r.status != 200:
            raise Exception("Download failed")

        if filename is not None:
            src = "%s%s.csv" % (droppath, filename)
            f = open(src, "w+")
            f.write(r.data)
            f.close()
            logger.info("%s written" % src)

            import shutil
            now = datetime.now()
            now = "%s_%s_%s_%s_%s" %(now.year, now.day, now.month, now.hour, now.minute)
            dst = src.replace('.csv', '.%s.csv' % now)
            shutil.copyfile(src, dst)
            logger.info("backup copy of %s.csv copied to %s" % (filename, dst))
        else:
            try:
                reader = csv.DictReader(re.split("[\n\r]+", r.data))
                return list(reader)
            except Exception as e:
                self.fatal_error("Cannot read export", exception=e)