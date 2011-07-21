========================
Munchy Lunchy API Server
========================

Version 1.0b


Installation Documentation
==========================

::

    git clone git://github.com/mattbasta/munchylunchy-api.git apiserver
    cd apiserver
    mkvirtualenv apiserver
    pip install -r requirements.txt


Prerequirements
---------------

- pip
- A redis server
- git
- virtualenv


Endpoint Documentation
======================

All endpoints support a typing interface. By default, data will be served as JSON. Optionally, a URL parameter (``type``) can be set with any of these values:

json
    Return output in JSON or JSON-P format
xml
    Return output in XML format

If the type is set to ``json``, another optional argument can be set (``callback``), converting the request to JSON-P. This is compatible with jQuery's implementation of JSON-P. Callback names must be alphanumeric.


Endpoint List
=============

    /auth/browserid
    /auth/token
    /health/ping
    /health/redis
    /tastes/set

