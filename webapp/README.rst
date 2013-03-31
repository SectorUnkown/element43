element43 webapp
================

This directory contains the element43 web application. We keep this separate
from the consumer and the other components.

Brief directory overview
------------------------

* The webapp directory you are currently in is the project root directory.
  It contains a ``manage.py`` file which will let you do various things, like
  run the devserver, apply DB migrations, and etc.
* You'll also find ``prepare_static.sh``, ``precompile_group_json.py`` and ``iconIDs.yaml`` here.
  These files are used for production asset handling. Just execute ``prepare_static.sh`` and it will generate,
  collect and compress static files. You can find them in the *static* directory afterwards.
* *element43* - The Python module containing the web application.
* *media* - User-uploaded images and files.
* *static* - JS, CSS, images, and other static files.
* *templates* - HTML templates for the views.
