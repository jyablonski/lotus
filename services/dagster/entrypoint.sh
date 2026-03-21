#!/bin/sh
# Ensure IO manager storage dirs exist and are writable by appuser.
# Docker named volumes may be root-owned when first created, which
# overrides the Dockerfile's mkdir/chown.
mkdir -p /tmp/io_manager_storage/compute_logs /tmp/io_manager_storage/artifacts
chown -R appuser:appuser /tmp/io_manager_storage

exec gosu appuser "$@"
