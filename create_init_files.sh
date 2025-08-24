#!/bin/bash
# Create __init__.py files for Python packages

touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py

echo "Init files created"