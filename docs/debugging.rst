.. ref-debugging:

==================
Debugging Tastypie
==================

There are some common problems people run into when using Tastypie for the first
time. Some of the common problems and things to try appear below.


"I'm getting XML output in my browser but I want JSON output!"
==============================================================

This is actually not a bug and JSON support is present in your ``Resource``.
This issue is that Tastypie respects the ``Accept`` header your browser sends.
Most browsers send something like::

    Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5

Note that ``application/xml`` comes first, which is a format that Tastypie
handles by default, hence why you receive XML.

If you use ``curl`` from the command line, you should receive JSON by default::

    curl http://localhost:8000/api/v1/

If you want JSON in the browser, simply append ``?format=json`` to your URL.
Tastypie always respects this override first, before it falls back to the
``Accept`` header.
