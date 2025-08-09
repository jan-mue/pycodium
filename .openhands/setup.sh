#! /bin/bash

echo "Setting up the environment..."
uv tool update-shell
uv tool install pre-commit --with pre-commit-uv --force-reinstall
