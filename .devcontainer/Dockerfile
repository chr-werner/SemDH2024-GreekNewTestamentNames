# Use the python image from Microsoft Dev Containers as the base image
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

LABEL org.opencontainers.image.authors="christoph.werner@hs-wismar.de" \
    version="0.4" \
    description="Container for Python, R, .NET, and relevant dependencies for working with ancient Greek manuscripts and R development."

# Install necessary system dependencies, including R from the Rocker repository
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
        gnupg \
        bash \
        openssl \
        ca-certificates \
        git \
        htop \
        build-essential \
        curl \
        make \
        wget \
        xz-utils \
        locales \
        libcurl4-openssl-dev \
        libssl-dev \
        libxml2-dev \
        tar \
        dirmngr \
        software-properties-common \
        libharfbuzz-dev \
        libfribidi-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
        jq \
        tmux

RUN gpg --keyserver keyserver.ubuntu.com  --recv-key '95C0FAF38DB3CCAD0C080A7BDC78B2DDEABC47B7' && \
    gpg --armor --export '95C0FAF38DB3CCAD0C080A7BDC78B2DDEABC47B7' | sudo tee /etc/apt/trusted.gpg.d/cran_debian_key.asc && \
    echo "deb http://cloud.r-project.org/bin/linux/debian bookworm-cran40/" | sudo tee -a /etc/apt/sources.list && \
    apt-get update && \
    apt-cache policy r-base && \
    apt-get install -y r-base

# Set UTF-8 locale for proper Greek character support
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

# Set environment variables for Python, locale, and .NET
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOTNET_VERSION=7.0.410 \
    DOTNET_DOWNLOAD_URL=https://download.visualstudio.microsoft.com/download/pr/0ddc1522-2361-4394-97e9-52318bf51951/c5aef30601a86810f1f8ea89d42c26a0/dotnet-sdk-7.0.410-linux-x64.tar.gz \
    DOTNET_SHA512_CHECKSUM=20b8e02979328e4c4a14493f7791ed419aabd0175233db80cd60e2c004b829b3e8301281ea86b27ba818372473accf5a6d553e5354c54917c8e84d25f5855caa \
    DOTNET_DIR=/usr/share/dotnet \
    DOTNET_ROOT=/usr/share/dotnet \
    PATH=$PATH:/usr/share/dotnet

# Install .NET SDK
RUN curl -SL --output dotnet-sdk.tar.gz $DOTNET_DOWNLOAD_URL && \
    mkdir -p $DOTNET_DIR && \
    tar -zxf dotnet-sdk.tar.gz -C $DOTNET_DIR && \
    rm dotnet-sdk.tar.gz

# Copy the local R and python requirements file into the Docker container
COPY packages.txt /tmp/r_req.txt
COPY requirements.txt /tmp/p_req.txt

# Install R and python packages
RUN R -e "install.packages(readLines('/tmp/r_req.txt'), repos = 'https://cran.rstudio.com/')" && \
    pip install -r /tmp/p_req.txt

RUN echo "set -g mouse on" >> ~/.tmux.conf

# Clean up unnecessary files and caches
RUN rm -rf /var/lib/apt/lists/*

