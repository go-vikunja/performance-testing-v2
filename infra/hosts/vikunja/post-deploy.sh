#!/usr/bin/env bash
# Image runs as uid 1000; bind mount must be writable by it.
mkdir -p /opt/perf/files && chown 1000:1000 /opt/perf/files
