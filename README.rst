Notifpy
=======

**Notifpy** is a custom YouTube and Twitch subscription system. The original
goal was to get rid of a Google account. However, querying YouTube API
requires an API key and therefore you still need an account. The good
thing is that it wont be able to see what or when you are watching
anything. Now it also includes Twitch streams.

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

You'll need a version of Python that runs Django 3.0.2, ie. 3.6 or above.

Installation
~~~~~~~~~~~~

Install the module from its custom package repository:

.. code:: bash

    pip install --extra-index-url="https://packages.chalier.fr" django-notifpy

Add it to your Django ``INSTALLED_APPS``, use the ``migrate``
and ``collectstatic`` options, and that's it!

API Secrets
~~~~~~~~~~~

In order to use YouTube Data API v3, you need an `API
key <https://console.developers.google.com/apis/credentials>`__. For
more information you can check the
`documentation <https://developers.google.com/youtube/registering_an_application>`__.
Create a dummy ``notifpy.models.Settings`` object and set its ``youtube`` field to:

.. code:: json

    {
        "client_id": "...",
        "redirect_uri": "...",
        "client_secret": "...",
        "scope": "https://www.googleapis.com/auth/youtube.force-ssl"
    }

The use of Twitch API requires an app key that you may create
`here <https://dev.twitch.tv/dashboard/apps/create>`__. You may find the
documentation `here <https://dev.twitch.tv/docs/authentication#registration>`__.
In the same ``notifpy.models.Settings`` object, set the ``twitch`` field to:

.. code:: json

    {
        "client_id": "...",
        "client_secret": "...",
        "redirect_uri": "...",
        "scope": "openid"
    }


Redirect URIs
~~~~~~~~~~~~~

Please note that the ``redirect_uri`` in both cases should be of the form:

.. code::

    http(s)://<domain.including.port>/<path-to-notifpy-app>/oauth/youtube
    http(s)://<domain.including.port>/<path-to-notifpy-app>/oauth/twitch

OAuth authentication flow uses those routes to catch the redirection when
the app is granted an authorization code.

2. Usage
--------

Here are some notes about the use of Notifpy:

- Manual updates can be triggered with a ``manage.py`` command ``update``.
- Filter regexes for YouTube channels uses regular expressions following `Python's syntax <https://docs.python.org/3/library/re.html>`__.
- Automation on a server of channel updates can be done by running the script every hour with the following cron task (use ``crontab -e`` append it). The program will adapt updates based on the given priorities:

::

    SHELL=/bin/bash
    0 * * * * cd /PATH/TO/SERVER && source venv/bin/activate && python manage.py update

Change ``PATH`` to your actual path.
