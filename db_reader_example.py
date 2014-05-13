#!/usr/bin/python

import db as db

data = db.get("SELECT * FROM debug ORDER BY debug_id DESC LIMIT 0, 10")
for row in data:
    print row
    print row['value']
