# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#

import json
import types

import aiocouchdb.client
import aiocouchdb.feeds
import aiocouchdb.database
import aiocouchdb.tests.utils as utils
from aiocouchdb.client import urljoin


class DatabaseTestCase(utils.TestCase):

    def setUp(self):
        super().setUp()
        self.url_db = urljoin(self.url, 'db')
        self.db = aiocouchdb.database.Database(self.url_db)

    def test_init_with_url(self):
        self.assertIsInstance(self.db.resource, aiocouchdb.client.Resource)

    def test_init_with_resource(self):
        res = aiocouchdb.client.Resource(self.url_db)
        server = aiocouchdb.server.Server(res)
        self.assertIsInstance(server.resource, aiocouchdb.client.Resource)
        self.assertEqual(self.url_db, self.db.resource.url)

    def test_exists(self):
        resp = self.mock_json_response(data=b'{}')
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.exists())
        self.assert_request_called_with('HEAD', 'db')
        self.assertTrue(result)

    def test_exists_forbidden(self):
        resp = self.mock_json_response(data=b'{}')
        resp.status = 403
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.exists())
        self.assert_request_called_with('HEAD', 'db')
        self.assertFalse(result)

    def test_exists_not_found(self):
        resp = self.mock_json_response(data=b'{}')
        resp.status = 404
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.exists())
        self.assert_request_called_with('HEAD', 'db')
        self.assertFalse(result)

    def test_info(self):
        resp = self.mock_json_response(data=b'{}')
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.info())
        self.assert_request_called_with('GET', 'db')
        self.assertIsInstance(result, dict)

    def test_create(self):
        resp = self.mock_json_response(data=b'{"ok": true}')
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.create())
        self.assert_request_called_with('PUT', 'db')
        self.assertTrue(result)

    def test_delete(self):
        resp = self.mock_json_response(data=b'{"ok": true}')
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.delete())
        self.assert_request_called_with('DELETE', 'db')
        self.assertTrue(result)

    def test_all_docs(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        result = self.run_loop(self.db.all_docs())
        self.assert_request_called_with('GET', 'db', '_all_docs')
        self.assertIsInstance(result, aiocouchdb.feeds.ViewFeed)

    def test_all_docs_params(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        all_params = {
            'attachments': False,       
            'conflicts': True,
            'descending': True,
            'endkey': 'foo',
            'endkey_docid': 'foo_id',
            'include_docs': True,
            'inclusive_end': False,
            'limit': 10,
            'skip': 20,
            'stale': 'ok',
            'startkey': 'bar',
            'startkey_docid': 'bar_id',
            'update_seq': True
        }

        for key, value in all_params.items():
            self.run_loop(self.db.all_docs(**{key: value}))
            if key in ('endkey', 'startkey'):
                value = json.dumps(value)
            self.assert_request_called_with('GET', 'db', '_all_docs',
                                            params={key: value})

    def test_all_docs_key(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        self.run_loop(self.db.all_docs('foo'))
        self.assert_request_called_with('GET', 'db', '_all_docs',
                                        params={'key': '"foo"'})

    def test_all_docs_keys(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        self.run_loop(self.db.all_docs('foo', 'bar', 'baz'))
        self.assert_request_called_with('POST', 'db', '_all_docs',
                                        data={'keys': ['foo', 'bar', 'baz']})

    def test_bulk_docs(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        self.run_loop(self.db.bulk_docs([{'_id': 'foo'}, {'_id': 'bar'}]))
        self.assert_request_called_with('POST', 'db', '_bulk_docs')
        data = self.request.call_args[1]['data']
        self.assertIsInstance(data, types.GeneratorType)
        self.assertEqual(b'{"docs": [{"_id": "foo"},{"_id": "bar"}]}',
                         b''.join(data))

    def test_bulk_docs_all_or_nothing(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        self.run_loop(self.db.bulk_docs([{'_id': 'foo'}, {'_id': 'bar'}],
                                        all_or_nothing=True))
        self.assert_request_called_with('POST', 'db', '_bulk_docs')
        data = self.request.call_args[1]['data']
        self.assertIsInstance(data, types.GeneratorType)
        self.assertEqual(b'{"all_or_nothing": true, "docs": '
                         b'[{"_id": "foo"},{"_id": "bar"}]}',
                         b''.join(data))

    def test_bulk_docs_new_edits(self):
        resp = self.mock_json_response()
        self.request.return_value = self.future(resp)

        self.run_loop(self.db.bulk_docs([{'_id': 'foo'}], new_edits=False))
        self.assert_request_called_with('POST', 'db', '_bulk_docs',
                                        params={'new_edits': False})
