FROM ubuntu:20.04

ENV HOME=/root
ENV DEBIAN_FRONTEND=noninteractive 
ENV VIRTUAL_ENV=/opt/pcvenv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN echo "==> Installing Dependencies..." && \
    apt-get update -y && \
    apt-get install -y \
        bash \
        gettext \
        libcanberra-gtk-module \
        libcanberra-gtk3-module \
        python3 \
        python3-pil \
        python3-gi \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-venv \
        sudo \
        unzip \
    && \
    echo "==> Cleanup..."  && \
    apt-get clean && \
    apt-get autoremove --yes

RUN echo "==> Initialize Python Virtualenv and Set Default Shell..."  && \
    python3 -m venv $VIRTUAL_ENV && \
    chsh -s /usr/bin/bash

RUN echo "==> Installing Pip3 Packages..."  && \
    python3 -m pip install --upgrade pip 

RUN echo "==> Create VSCode Non-Root User and Add Sudo Support..."  && \
    groupadd --gid $USER_GID $USERNAME && \
    useradd -s /usr/bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME 