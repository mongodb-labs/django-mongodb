#!/usr/bin/env bash
set -eu

CURRENT_VERSION=$(python setup.py --version)
sed -i "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"$1\"/" django_mongodb/__init__.py
