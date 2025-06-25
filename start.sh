#!/usr/bin/env bash
apt-get update && apt-get install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra
gunicorn -w 4 -b 0.0.0.0:10000 app:app 