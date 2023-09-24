'''
Test Django management commands.
'''

from django.test import SimpleTestCase
from django.core.management import call_command
from django.db.utils import OperationalError
from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error


@patch('core.management.commands.wait_for_db.Command.check')
class TestCommands(SimpleTestCase):
    ''' Test commands. '''

    def test_wait_for_db_ready(self, patched_check):
        '''Test waiting for database till its ready.'''
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        '''Test waiting for database while  getting OperationalError'''
        patched_check.side_effect = [Psycopg2Error] * 3 + [OperationalError] * 3 + [True] # noqa

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, 7)
        patched_check.assert_called_with(databases=['default'])
