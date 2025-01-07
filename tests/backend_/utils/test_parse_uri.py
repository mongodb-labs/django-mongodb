from unittest.mock import patch

import pymongo
from django.test import SimpleTestCase

from django_mongodb_backend import parse_uri


class ParseURITests(SimpleTestCase):
    def test_simple_uri(self):
        settings_dict = parse_uri("mongodb://cluster0.example.mongodb.net/myDatabase")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb_backend")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "cluster0.example.mongodb.net")

    def test_no_database(self):
        settings_dict = parse_uri("mongodb://cluster0.example.mongodb.net")
        self.assertIsNone(settings_dict["NAME"])
        self.assertEqual(settings_dict["HOST"], "cluster0.example.mongodb.net")

    def test_srv_uri_with_options(self):
        uri = "mongodb+srv://my_user:my_password@cluster0.example.mongodb.net/my_database?retryWrites=true&w=majority"
        # patch() prevents a crash when PyMongo attempts to resolve the
        # nonexistent SRV record.
        with patch("dns.resolver.resolve"):
            settings_dict = parse_uri(uri)
        self.assertEqual(settings_dict["NAME"], "my_database")
        self.assertEqual(settings_dict["HOST"], "mongodb+srv://cluster0.example.mongodb.net")
        self.assertEqual(settings_dict["USER"], "my_user")
        self.assertEqual(settings_dict["PASSWORD"], "my_password")
        self.assertIsNone(settings_dict["PORT"])
        self.assertEqual(
            settings_dict["OPTIONS"], {"retryWrites": True, "w": "majority", "tls": True}
        )

    def test_localhost(self):
        settings_dict = parse_uri("mongodb://localhost")
        self.assertEqual(settings_dict["HOST"], "localhost")
        self.assertEqual(settings_dict["PORT"], 27017)

    def test_localhost_with_port(self):
        settings_dict = parse_uri("mongodb://localhost:27018")
        self.assertEqual(settings_dict["HOST"], "localhost")
        self.assertEqual(settings_dict["PORT"], 27018)

    def test_hosts_with_ports(self):
        settings_dict = parse_uri("mongodb://localhost:27017,localhost:27018")
        self.assertEqual(settings_dict["HOST"], "localhost:27017,localhost:27018")
        self.assertEqual(settings_dict["PORT"], None)

    def test_hosts_without_ports(self):
        settings_dict = parse_uri("mongodb://host1.net,host2.net")
        self.assertEqual(settings_dict["HOST"], "host1.net:27017,host2.net:27017")
        self.assertEqual(settings_dict["PORT"], None)

    def test_conn_max_age(self):
        settings_dict = parse_uri("mongodb://localhost", conn_max_age=600)
        self.assertEqual(settings_dict["CONN_MAX_AGE"], 600)

    def test_test_kwarg(self):
        settings_dict = parse_uri("mongodb://localhost", test={"NAME": "test_db"})
        self.assertEqual(settings_dict["TEST"], {"NAME": "test_db"})

    def test_invalid_credentials(self):
        msg = "The empty string is not valid username."
        with self.assertRaisesMessage(pymongo.errors.InvalidURI, msg):
            parse_uri("mongodb://:@localhost")

    def test_no_scheme(self):
        with self.assertRaisesMessage(pymongo.errors.InvalidURI, "Invalid URI scheme"):
            parse_uri("cluster0.example.mongodb.net")
