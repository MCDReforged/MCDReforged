ARG BASE_IMAGE_TAG=3.13
FROM python:${BASE_IMAGE_TAG}

ARG MCDR_VERSION_REQUIREMENT=latest
ARG PYPI_INDEX=https://pypi.org/simple

RUN <<EOT
set -eux
export PIP_ROOT_USER_ACTION=ignore
python3 -m pip install -U pip
if [ "$MCDR_VERSION_REQUIREMENT" = "latest" ]; then
  pip3 install mcdreforged
else
  pip3 install "mcdreforged==${MCDR_VERSION_REQUIREMENT}" -i "$PYPI_INDEX" --extra-index-url https://pypi.org/simple
fi
pip3 cache purge && rm -rf ~/.cache/
EOT

RUN <<EOT
set -eux
mkdir -p "$(python3 -m site --user-site)"
cat <<EOF > /etc/pip.conf
[global]
user = true
EOF
cat <<EOF >> ~/.bashrc

# Add Python user bin to PATH
export PATH="\$PATH:$(python3 -m site --user-base)/bin"
EOF
EOT

WORKDIR /mcdr
CMD ["python3", "-m", "mcdreforged", "start", "--auto-init"]
