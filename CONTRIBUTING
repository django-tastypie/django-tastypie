============
Contributing
============

Tastypie is open-source and, as such, grows (or shrinks) & improves in part
due to the community. Below are some guidelines on how to help with the project.


Philosophy
==========

* Tastypie is BSD-licensed. All contributed code must be either

  * the original work of the author, contributed under the BSD, or...
  * work taken from another project released under a BSD-compatible license.

* GPL'd (or similar) works are not eligible for inclusion.
* Tastypie's git master branch should always be stable, production-ready &
  passing all tests.
* Major releases (1.x.x) are commitments to backward-compatibility of the public APIs.
  Any documented API should ideally not change between major releases.
  The exclusion to this rule is in the event of either a security issue
  or to accommodate changes in Django itself.
* Minor releases (x.3.x) are for the addition of substantial features or major
  bugfixes.
* Patch releases (x.x.4) are for minor features or bugfixes.


Guidelines For Reporting An Issue/Feature
=========================================

So you've found a bug or have a great idea for a feature. Here's the steps you
should take to help get it added/fixed in Tastypie:

* First, check to see if there's an existing issue/pull request for the
  bug/feature. All issues are at https://github.com/django-tastypie/django-tastypie/issues
  and pull reqs are at https://github.com/django-tastypie/django-tastypie/pulls.
* If there isn't one there, please file an issue. The ideal report includes:

  * A description of the problem/suggestion.
  * How to recreate the bug.
  * If relevant, including the versions of your:

    * Python interpreter
    * Django
    * Tastypie
    * Optionally of the other dependencies involved

  * Ideally, creating a pull request with a (failing) test case demonstrating
    what's wrong. This makes it easy for us to reproduce & fix the problem.
    Instructions for running the tests are at :doc:`index`

You might also hop into the IRC channel (``#tastypie`` on ``irc.freenode.net``)
& raise your question there, as there may be someone who can help you with a
work-around.


Guidelines For Contributing Code
================================

If you're ready to take the plunge & contribute back some code/docs, the
process should look like:

* Fork the project on GitHub into your own account.
* Clone your copy of Tastypie.
* Make a new branch in git & commit your changes there.
* Push your new branch up to GitHub.
* Again, ensure there isn't already an issue or pull request out there on it.
  If there is & you feel you have a better fix, please take note of the issue
  number & mention it in your pull request.
* Create a new pull request (based on your branch), including what the
  problem/feature is, versions of your software & referencing any related
  issues/pull requests.

In order to be merged into Tastypie, contributions must have the following:

* A solid patch that:

  * is clear.
  * works across all supported versions of Python/Django.
  * follows the existing style of the code base (mostly PEP-8).
  * comments included as needed.

* A test case that demonstrates the previous flaw that now passes
  with the included patch.
* If it adds/changes a public API, it must also include documentation
  for those changes.
* Must be appropriately licensed (see "Philosophy").
* Adds yourself to the AUTHORS file.

Please also:

* Unless your change only modifies the documentation, add the issue you're
  solving to the list in docs/release_notes/dev.rst, include issue and PR
  numbers.
* Squash your changes down to a single commit, or down to one commit containing
  your failing tests and one more commit containing the fix that makes those
  tests pass.

If your contribution lacks any of these things, they will have to be added
by a core contributor before being merged into Tastypie proper, which may take
substantial time for the all-volunteer team to get to.


Guidelines For Core Contributors
================================

If you've been granted the commit bit, here's how to shepherd the changes in:

* Any time you go to work on Tastypie, please use ``git pull --rebase`` to fetch
  the latest changes.
* Any new features/bug fixes must meet the above guidelines for contributing
  code (solid patch/tests passing/docs included).
* Commits are typically cherry-picked onto a branch off master.

  * This is done so as not to include extraneous commits, as some people submit
    pull reqs based on their git master that has other things applied to it.

* A set of commits should be squashed down to a single commit.

  * ``git merge --squash`` is a good tool for performing this, as is
    ``git rebase -i HEAD~N``.
  * This is done to prevent anyone using the git repo from accidently pulling
    work-in-progress commits.

* Commit messages should use past tense, describe what changed & thank anyone
  involved. Examples::

    """Added a new way to do per-object authorization."""
    """Fixed a bug in ``Serializer.to_xml``. Thanks to joeschmoe for the report!"""
    """BACKWARD-INCOMPATIBLE: Altered the arguments passed to ``Bundle.__init__``.

    Further description appears here if the change warrants an explanation
    as to why it was done."""

* For any patches applied from a contributor, please ensure their name appears
  in the AUTHORS file.
* When closing issues or pull requests, please reference the SHA in the closing
  message (i.e. ``Thanks! Fixed in SHA: 6b93f6``). GitHub will automatically
  link to it.
