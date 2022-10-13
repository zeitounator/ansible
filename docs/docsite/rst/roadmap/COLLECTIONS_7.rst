.. _ansible_7_roadmap:

===================
Ansible project 7.0
===================

This release schedule includes dates for the `ansible <https://pypi.org/project/ansible/>`_ package, with a few dates for the `ansible-core <https://pypi.org/project/ansible-core/>`_ package as well. All dates are subject to change. See the `ansible-core 2.14 Roadmap <https://docs.ansible.com/ansible-core/devel/roadmap/ROADMAP_2_14.html>`_ for the most recent updates on ``ansible-core``.

.. contents::
   :local:


Release schedule
=================


:2022-09-19: ansible-core feature freeze, stable-2.14 branch created.
:2022-09-26: Start of ansible-core 2.14 betas (biweekly, as needed).
:2022-09-27: Ansible-7.0.0 alpha1 (roughly biweekly ``ansible`` alphas timed to coincide with ``ansible-core-2.14`` pre-releases).
:2022-10-12: Community topic: List any backwards incompatible collection releases that beta1 should try to accommodate.
:2022-10-17: First ansible-core 2.14 release candidate.
:2022-10-18: Ansible-7.0.0 alpha2.
:2022-10-26: Community Meeting topic: Decide what contingencies to activate for any blockers that do not meet the deadline.
:2022-11-07: Ansible-core-2.14.0 released.
:2022-11-07: Last day for collections to make backwards incompatible releases that will be accepted into Ansible-7. This includes adding new collections to Ansible 7.0.0; from now on new collections have to wait for 7.1.0 or later.
:2022-11-08: Create the ansible-build-data directory and files for Ansible-8.
:2022-11-08: Ansible-7.0.0 beta1 -- feature freeze [1]_ (weekly beta releases; collection owners and interested users should test for bugs).
:2022-11-15: Ansible-7.0.0 rc1 [2]_ [3]_ (weekly release candidates as needed; test and alert us to any blocker bugs).  Blocker bugs will slip release.
:2022-11-29: Ansible-7.0.0 release.
:2022-12-06: Release of ansible-core 2.14.1.
:2022-12-20: Release of Ansible-7.1.0 (bugfix + compatible features: every three weeks.)

.. [1] No new modules or major features accepted after this date. In practice, this means we will freeze the semver collection versions to compatible release versions. For example, if the version of community.crypto on this date was community.crypto 2.3.0; Ansible-7.0.0 could ship with community.crypto 2.3.1.  It would not ship with community.crypto 2.4.0.

.. [2] After this date only changes blocking a release are accepted.  Accepted changes require creating a new rc and may slip the final release date.

.. [3] Collections will only be updated to a new version if a blocker is approved.  Collection owners should discuss any blockers at a community IRC meeting (before this freeze) to decide whether to bump the version of the collection for a fix. See the `Community IRC meeting agenda <https://github.com/ansible/community/issues/539>`_.

.. note::

  Breaking changes will be introduced in Ansible 7.0.0, although we encourage the use of deprecation periods that will show up in at least one Ansible release before the breaking change happens, this is not guaranteed.


Ansible minor releases
=======================

Ansible 7.x minor releases will occur approximately every three weeks if changes to collections have been made or if it is deemed necessary to force an upgrade to a later ansible-core-2.14.x.  Ansible 7.x minor releases may contain new features but not backwards incompatibilities.  In practice, this means we will include new collection versions where either the patch or the minor version number has changed but not when the major number has changed. For example, if Ansible-7.0.0 ships with community.crypto 2.3.0; Ansible-6.1.0 may ship with community.crypto 2.4.0 but would not ship with community.crypto 3.0.0.


.. note::

    Minor releases will stop when Ansible-8 is released.  See the :ref:`Release and Maintenance Page <release_and_maintenance>` for more information.


For more information, reach out on a mailing list or a chat channel - see :ref:`communication` for more details.
