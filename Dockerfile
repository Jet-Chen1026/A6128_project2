# Use Python 2
FROM ubuntu:16.04

WORKDIR /root

RUN apt-get update
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:ubuntugis/ppa
RUN apt-get update
RUN apt-get install -y libboost-dev libboost-serialization-dev gdal-bin libgdal-dev make cmake libbz2-dev libexpat1-dev swig python-dev
RUN apt-get install -y git

RUN git clone https://github.com/cyang-kth/fmm.git\
    && cd fmm \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make -j4 \
    && make install \
    && make clean

# Use Python 3
#FROM python:3.10
#
#WORKDIR /root/project
#RUN apt-get update \
#    && apt-get upgrade -y
#RUN apt-get install -y libboost-dev libboost-serialization-dev gdal-bin libgdal-dev make cmake libbz2-dev libexpat1-dev swig
#RUN apt-get clean \
#    && rm -rf /var/lib/apt/lists/*
#
#COPY requirements.txt .
#RUN pip install --upgrade pip setuptools wheel
#RUN pip install -r requirements.txt
#RUN git clone https://github.com/rderollepot/fmm.git \
#    && cd fmm \
#    && mkdir build \
#    && cd build \
#    && cmake .. \
#    && make -j4 \
#    && make install \
#    && make clean
