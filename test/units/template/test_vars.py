# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from unittest.mock import MagicMock

from ansible.template.vars import AnsibleJ2Vars


class TestVars(unittest.TestCase):
    def setUp(self):
        self.mock_templar = MagicMock(name='mock_templar')

    def test_globals_empty(self):
        ajvars = AnsibleJ2Vars(self.mock_templar, {})
        res = dict(ajvars)
        self.assertIsInstance(res, dict)

    def test_globals(self):
        res = dict(AnsibleJ2Vars(self.mock_templar, {'foo': 'bar', 'blip': [1, 2, 3]}))
        self.assertIsInstance(res, dict)
        self.assertIn('foo', res)
        self.assertEqual(res['foo'], 'bar')
