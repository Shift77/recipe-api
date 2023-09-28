'''
Command  of django to wait for database be available.

'''

import time
from psycopg2 import OperationalError as Psycopg2Error  # Package that makes Postgresql and Django work together # noqa
from django.db.utils import OperationalError    # Error that Django throws when database is not ready # noqa


from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        '''Entrypoint for command'''
        self.stdout.write('waiting for database...')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 more seconds...') # noqa
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database Is Available!'))
