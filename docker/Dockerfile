ARG BASE_IMAGE_TAG=3.11-bookworm
FROM python:${BASE_IMAGE_TAG}

ARG MCDR_REQUIREMENT=latest
ARG PYPI_INDEX=https://pypi.org/simple

RUN <<EOT
set -e
export PIP_ROOT_USER_ACTION=ignore
python3 -m pip install -U pip
if [ "$MCDR_REQUIREMENT" = "latest" ]; then
  pip3 install mcdreforged
else
  if [ "$PYPI_INDEX" = "https://test.pypi.org/simple" ]; then
    pip3 install mcdreforged
  fi
  pip3 install "mcdreforged==${MCDR_REQUIREMENT}" -i "$PYPI_INDEX"
fi
pip3 cache purge
EOT

RUN <<EOT
set -e
mkdir /pip_packages
cat <<EOF > /etc/pip.conf
[global]
target = /pip_packages
EOF
EOT

WORKDIR /mcdr
CMD ["python3", "-m", "mcdreforged", "start"]
