from unittest.mock import patch

import pymongo
from django.test import SimpleTestCase

from django_mongodb import parse_uri

URI = "mongodb+srv://myDatabaseUser:D1fficultP%40ssw0rd@cluster0.example.mongodb.net/myDatabase?retryWrites=true&w=majority&tls=false"


class ParseURITests(SimpleTestCase):
    def test_simple_uri(self):
        settings_dict = parse_uri("mongodb://cluster0.example.mongodb.net/myDatabase")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "cluster0.example.mongodb.net")

    def test_no_database(self):
        settings_dict = parse_uri("mongodb://cluster0.example.mongodb.net/")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertIsNone(settings_dict["NAME"])
        self.assertEqual(settings_dict["HOST"], "cluster0.example.mongodb.net")

    # PyMongo will try to resolve the SRV record if the URI has the mongodb+srv:// prefix.
    # https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
    def test_srv_uri_with_options(self):
        with patch("dns.resolver.resolve"):
            settings_dict = parse_uri(URI)
            self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
            self.assertEqual(settings_dict["NAME"], "myDatabase")
            self.assertEqual(settings_dict["HOST"], "mongodb+srv://cluster0.example.mongodb.net")
            self.assertEqual(settings_dict["USER"], "myDatabaseUser")
            self.assertEqual(settings_dict["PASSWORD"], "D1fficultP@ssw0rd")
            self.assertIsNone(settings_dict["PORT"])
            self.assertEqual(
                settings_dict["OPTIONS"], {"retryWrites": True, "w": "majority", "tls": False}
            )

    def test_localhost(self):
        settings_dict = parse_uri("mongodb://localhost/myDatabase")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "localhost")

    def test_localhost_with_port(self):
        settings_dict = parse_uri("mongodb://localhost/myDatabase")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "localhost")
        self.assertEqual(settings_dict["PORT"], 27017)

    def test_localhosts_with_ports(self):
        settings_dict = parse_uri(
            "mongodb://localhost:27017,localhost:27018,localhost:27019/myDatabase"
        )
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "localhost:27017,localhost:27018,localhost:27019")
        self.assertEqual(settings_dict["PORT"], None)

    def test_conn_max_age(self):
        settings_dict = parse_uri("mongodb://localhost/myDatabase", conn_max_age=600)
        self.assertEqual(settings_dict["CONN_MAX_AGE"], 600)

    def test_conn_health_checks(self):
        settings_dict = parse_uri("mongodb://localhost/myDatabase", conn_health_checks=True)
        self.assertEqual(settings_dict["CONN_HEALTH_CHECKS"], True)

    def test_test_kwarg(self):
        settings_dict = parse_uri("mongodb://localhost/myDatabase", test={"NAME": "test_db"})
        self.assertEqual(settings_dict["TEST"]["NAME"], "test_db")

    def test_invalid_credentials(self):
        with self.assertRaises(pymongo.errors.InvalidURI):
            parse_uri("mongodb://:@localhost/myDatabase")

    def test_no_prefix(self):
        with self.assertRaises(pymongo.errors.InvalidURI):
            parse_uri("cluster0.example.mongodb.net/myDatabase")
