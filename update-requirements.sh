#!/usr/bin/env sh

# install pip-tools' future branch that has pip-compile
if ! command -v pip-compile >/dev/null 2>&1; then
	pip install --upgrade pip
	pip install git+https://github.com/nvie/pip-tools.git@future
fi

pip-compile --annotate requirements.in > requirements.txt
sed -i 's#pip-compile requirements.in#./update-requirements.sh#' requirements.txt
