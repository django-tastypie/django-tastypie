.. _ref-compatibility-notes:

===================
Compatibility Notes
===================


Tastypie does its best to be a good third-party app, trying to interoperate
with the widest range of Django environments it can. However, there are times
where certain things aren't possible. We'll do our best to document them here.


``ApiKey`` Database Index
-------------------------

When the ``ApiKey`` model was added to Tastypie, an index was lacking on the
``key`` field. This was the case until the v0.9.12 release. The model was
updated & a migration was added (``0002_add_apikey_index.py``). However, due
to the way MySQL works & the way Django generates index names, this migration
would fail miserably on many MySQL installs.

If you are using MySQL, South & the ``ApiKey`` authentication class, you should
manually add an index for the the ``ApiKey.key`` field. Something to the effect
of::

    BEGIN; -- LOLMySQL
    CREATE INDEX tastypie_apikey_key_index ON tastypie_apikey (`key`);
    COMMIT;
