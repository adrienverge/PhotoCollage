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
        git \
        gir1.2-gtk-3.0 \ 
        gettext \
        libcairo2 \
        libcairo2-dev \
        libcairo-gobject2 \
        libpangocairo-1.0-0 \
        libcanberra-gtk-module \
        libcanberra-gtk3-module \
        libgirepository-1.0-1 \
        pkg-config \
        python3 \
        python3-cairo \
        python3-dev \
        python3-gi \
        python3-gi-cairo \
        python3-pil \
        python3-pip \
        python3-setuptools \
        python3-six \
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
    python3 -m pip install --upgrade pip && \
    pip3 install \
        pillow \
        pycairo \
        pyyaml==5.4.1 \
        vext \
        vext.gi

RUN echo "==> Create VSCode Non-Root User and Add Sudo Support..."  && \
    groupadd --gid $USER_GID $USERNAME && \
    useradd -s /usr/bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME 

COPY ./coco_dataset/ /images