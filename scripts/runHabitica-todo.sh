#!/bin/sh
# Run habiticaTodo, avoid proxy.
unset http_proxy
unset https_proxy

pwd
cd habiticaTodo
python3.9 oneWaySync.py
