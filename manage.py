#!/usr/bin/env python
import os
import sys
from time import time

start = time()
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    assert sys.version_info >= (3, 6), 'py3.6+ please'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


end = time()
sys.stdout.write('Δ %.2fs\n' % (end - start))
