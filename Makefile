.PHONY: default
default: help ;

help:
	echo "make help"
	echo "make backup"

backup:
	mkdir -p backups
	cp db.sqlite3 backups/db.sqlite3.$$(date +%Y.%m.%d.%s)
	tree backups
