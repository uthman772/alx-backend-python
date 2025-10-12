# messaging_app/management/commands/wait_for_db.py
import time
import socket
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django command to wait for database to be available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_up = False
        while not db_up:
            try:
                # Try to connect to MySQL database
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('db', 3306))
                sock.close()
                db_up = True
            except socket.error:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))