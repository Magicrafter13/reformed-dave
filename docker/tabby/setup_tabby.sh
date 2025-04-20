#!/usr/bin/sh

cd /app/tabbyAPI
python start.py --update-deps << EOF
A
EOF

cd /app
rm $(readlink -f "$0")
