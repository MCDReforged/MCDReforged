ARG BASE_IMAGE_TAG=3.13
FROM python:${BASE_IMAGE_TAG}

ARG MCDR_VERSION_REQUIREMENT=latest
ARG PYPI_INDEX=https://pypi.org/simple

RUN <<EOT
set -eux
export PIP_ROOT_USER_ACTION=ignore

# temp fix before base images are all up to date: https://blog.python.org/2026/10/python-3151-3149-31317/
python3 -m pip install "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"

python3 -m pip install -U pip
if [ "$MCDR_VERSION_REQUIREMENT" = "latest" ]; then
  pip3 install mcdreforged
else
  pip3 install "mcdreforged==${MCDR_VERSION_REQUIREMENT}" -i "$PYPI_INDEX" --extra-index-url https://pypi.org/simple
fi
pip3 freeze
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
