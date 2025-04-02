====================
Cá Bhfuil (where is)
====================


    Cá Bhfuil - the irish for "where is" pronounced "ka will"


Cá Bhfuil is a work in progress python tool to locate where a patch is in a git repo

Its a slapped together combination of langchain, ollama, a hand full of files form
one of my other git repos and the fact i woke up a 5 am and said srew it lets play with ai.

the goal is to create something that can take a gerrit change id, git sha, a upstream or downstream
bug refernece or a commit title to find the relevnet commit, what branches its on and maybe
to summerise what it did.

basically it would be nice to have a tool that i can give a tracker(git sha, change id, launchpad/jira issue)
and have it search a git repo for refences to it. ideally once it find the relevent commtis it should
summerise what branches it is one, what git tags it is in, what tracker exist for it in each branch
and what it actully did. i.e did it fix a bug if who what did it fix and how? did it add a feature,
great! what was it? is there a spec if so where?

i am probaly not going to make it do all of that but that would be a very nice tool to have.

.. _pyscaffold-notes:

Making Changes & Contributing
=============================

This project uses `pre-commit`_, please make sure to install it before making any
changes::

    pip install pre-commit
    cd ca-bhfuil
    pre-commit install

It is a good idea to update the hooks to the latest version::

    pre-commit autoupdate

Don't forget to tell your contributors to also install and use pre-commit.

.. _pre-commit: https://pre-commit.com/

This project uses tox to execute tests, build docs and automate other development task that are not suitable for automation via pre-commit.

Note
====

This project has been set up using PyScaffold 4.1.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
