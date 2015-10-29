#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import unittest
import logging

from mock import Mock, patch

from zuora_python_toolkit.base import Zuora, session_required


logger = logging.getLogger("zyrup")
suds_logger = logging.getLogger("suds.client")


class ZuoraBaseTestCase(unittest.TestCase):
    client = None
    session_length_millis = 600000

    def setUp(self):
        wsdl = '../config/apisandbox.zuora.a.63.0.wsdl'
        username = 'api@c.co'
        password = 'Asdf1234!'

        kwargs = {
            "wsdl": wsdl,
            "username": username,
            "password": password,
            "session_length_millis": self.session_length_millis,
        }
        self.client = Zuora(**kwargs)


class ZuoraClientSetupTestCase(ZuoraBaseTestCase):

    def setUp(self):
        super(ZuoraClientSetupTestCase, self).setUp()

    def test_set_batch_sizes_with_valid_tuple(self):
        min_batch = 8
        max_batch = 8
        sizes = (min_batch, max_batch)
        self.client.set_batch_sizes(sizes)
        self.assertEqual(self.client.get_batch_sizes(), (min_batch, max_batch))

    def test_set_batch_sizes_with_invalid_max_value_in_tuple(self):
        min_batch = 8
        max_batch = 51
        sizes = (min_batch, max_batch)
        self.assertRaises(ValueError, self.client.set_batch_sizes, sizes)

    def test_set_batch_sizes_with_invalid_min_value_in_tuple(self):
        min_batch = 51
        max_batch = 8
        sizes = (min_batch, max_batch)
        self.assertRaises(ValueError, self.client.set_batch_sizes, sizes)

    def test_set_batch_sizes_with_single_value(self):
        sizes = 22
        default_min = self.client._default_batch_min
        self.client.set_batch_sizes(sizes)
        self.assertEqual(self.client.get_batch_sizes(), (default_min, sizes))

    def test_set_batch_sizes_with_invalid_type(self):
        sizes = ('A', 'B')
        self.assertRaises(ValueError, self.client.set_batch_sizes, sizes)

    def test_set_query_batch_size(self):
        size = 22
        self.client.set_query_batch_size(size)
        self.assertEqual(self.client._query_batch_size_max, size)

    def test_set_query_batch_size_that_exceeds_max_value(self):
        size = 5000
        self.assertRaises(ValueError, self.client.set_query_batch_size, size)

    def test_set_query_batch_size_with_zero(self):
        size = 0
        self.client.set_query_batch_size(size)
        self.assertEqual(self.client._query_batch_size_max, self.client._default_query_batch_size_max)

    def test_set_query_batch_size_with_invalid_type(self):
        size = 'A'
        self.assertRaises(ValueError, self.client.set_query_batch_size, size)


@patch('zyrup.base.Zuora.login',
       return_value={
           'Session': 'LiUBQF...ugxg2jJuCA==',
           'ServerUrl': 'https://apisandbox.zuora.com/apps/services/a/26.0'
       })
class ZuoraMockLoginTestCase(ZuoraBaseTestCase):

    def test_login(self, login_mock):
        login_result = self.client.login()
        self.assertIn('Session', login_result)

    def test_check_login_decorator(self, login_mock):
        login_result = self.client.login()
        self.assertIn('Session', login_result)

        func = Mock(return_value=True)
        decorated_func = session_required(func)
        decorated_func_result = decorated_func(self.client)
        func.assert_called_with(self.client)


class ZuoraQueryTestCase(ZuoraBaseTestCase):

    def test_query(self):
        results = self.client\
            .query("SELECT ID FROM Account")
        print results

    def test_query_more(self):
        self.client.set_query_batch_size(100)
        result = self.client.query("SELECT ID FROM Account")
        self.assertEqual(len(result.records), 100)
        result = self.client.query_more(result.queryLocator)
        self.assertEqual(len(result.records), 100)


class ZuoraRetrieveTestCase(ZuoraBaseTestCase):

    def test_retrieve(self):
        z_object_type = 'Account'
        field_list = ['AccountNumber', 'Batch', 'BillCycleDay', ]
        id_list = ['2c92c0f8407f15460140808bf84a34a8', '2c92c0f9475dd7a101475f98c49377a6']
        results = self.client.retrieve(z_object_type, field_list, id_list)
        print results


class ZuoraCreateAccountTestCase(ZuoraBaseTestCase):

    def setUp(self):
        super(ZuoraCreateAccountTestCase, self).setUp()
        self.client.set_batch_sizes((5, 5))

    # def test_create(self):
    #     account = self.client.generate_object("Account")
    #     account.Name = "zyrup-python-toolkit unit test"
    #     account.AutoPay = False
    #     account.Batch = "Batch1"
    #     account.BillCycleDay = "1"
    #     account.Currency = "USD"
    #     account.PaymentTerm = "Due Upon Receipt"
    #     account.Status = "Draft"
    #
    #     #result = self.client.create(account)
    #     #self.assertTrue(result.Success)

    def test_create_bulk(self):
        accounts = []
        for x in xrange(25):
            account = self.client.generate_object("Account")
            account.Name = "bulktest-%s" % x
            account.AutoPay = False
            account.Batch = "Batch1"
            account.BillCycleDay = "1"
            account.Currency = "USD"
            account.PaymentTerm = "Due Upon Receipt"
            account.Status = "Draft"
            accounts.append(account)
        results = self.client.create(accounts)
        print results


class testZuoraBase(ZuoraBaseTestCase):

    def tearDown(self):
        # results = self._zuora.query("SELECT ID FROM Account WHERE Name = 'zyrup-python-toolkit unit test'")
        # count = 0
        # for result in results.records:
        #     self._zuora.delete("Account", result.Id)
        #     count = count + 1
        # print "Total Deleted %s" % count
        pass

    # def test_create(self):
    #     self._zuora.checkLogin()
    #
    #     account = self._zuora.generateObject("Account")
    #     account.Name = "zyrup-python-toolkit unit test"
    #     account.AutoPay = False
    #     account.Batch = "Batch1"
    #     account.BillCycleDay = "1"
    #     account.BillingModel__c = "HMA Billing"
    #     account.Currency = "USD"
    #     account.PaymentTerm = "Due Upon Receipt"
    #     account.Status = "Draft"
    #     account.Type__c = "Internal"
    #
    #     result = self._zuora.create(account)
    #     print result
    #     self.assertTrue(result.Success)
    #
    # def test_bulk_create(self):
    #     self._zuora.checkLogin()
    #
    #     accounts = []
    #     for x in xrange(0, 51):
    #         account = self._zuora.generateObject("Account")
    #         account.Name = "zyrup-python-toolkit unit test"
    #         account.AutoPay = False
    #         account.Batch = "Batch1"
    #         account.BillCycleDay = "1"
    #         account.BillingModel__c = "HMA Billing"
    #         account.Currency = "USD"
    #         account.PaymentTerm = "Due Upon Receipt"
    #         account.Status = "Draft"
    #         account.Type__c = "Internal"
    #         accounts.append(account)
    #     results = self._zuora.create(accounts)
    #     self.assertTrue(len(results) == 51)
    #     for result in results:
    #         self.assertTrue(result.Success)
    #
    # def test_update(self):
    #     self._zuora.checkLogin()
    #
    #     account = self._zuora.generateObject("Account")
    #     account.Name = "zyrup-python-toolkit unit test"
    #     account.AutoPay = False
    #     account.Batch = "Batch1"
    #     account.BillCycleDay = "1"
    #     account.BillingModel__c = "HMA Billing"
    #     account.Currency = "USD"
    #     account.PaymentTerm = "Due Upon Receipt"
    #     account.Status = "Draft"
    #     account.Type__c = "Internal"
    #
    #     result = self._zuora.create(account)
    #
    #     account.Id = result.Id
    #     account.BillCycleDay = 2
    #     result = self._zuora.update(account)
    #     print result
    #     self.assertTrue(result.Success)
    #
    # def test_bulk_update(self):
    #     self._zuora.checkLogin()
    #
    #     accounts = []
    #     for x in xrange(0, 51):
    #         account = self._zuora.generateObject("Account")
    #         account.Name = "zyrup-python-toolkit unit test"
    #         account.AutoPay = False
    #         account.Batch = "Batch1"
    #         account.BillCycleDay = "1"
    #         account.BillingModel__c = "HMA Billing"
    #         account.Currency = "USD"
    #         account.PaymentTerm = "Due Upon Receipt"
    #         account.Status = "Draft"
    #         account.Type__c = "Internal"
    #         accounts.append(account)
    #     results = self._zuora.create(accounts)
    #
    #     accounts = []
    #     for result in results:
    #         account = self._zuora.generateObject("Account")
    #         account.Id = result.Id
    #         account.BillCycleDay = 2
    #         accounts.append(account)
    #
    #     results = self._zuora.update(accounts)
    #     self.assertTrue(len(results) == 51)
    #     for result in results:
    #         self.assertTrue(result.Success)
    #
    # def test_export_and_download(self):
    #     lastUpdatedDate = datetime.timedelta(days=2)
    #     lastUpdatedDate = datetime.datetime.now() - lastUpdatedDate
    #     lastUpdatedDate = "%s/%s/%s" % (lastUpdatedDate.month, lastUpdatedDate.day, lastUpdatedDate.year)
    #     fileId = self._zuora.export("Account", ['Id', 'AccountNumber'], "UpdatedDate >= '%s'" % lastUpdatedDate)
    #     self._zuora.download(fileId, "test", "./")
    #
    #     self.assertTrue(len(fileId) == 32)
            
if __name__ == "__main__":
    unittest.main()