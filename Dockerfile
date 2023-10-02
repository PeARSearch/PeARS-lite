# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org> 
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get -y install curl

WORKDIR /pears-lite

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

WORKDIR /pears-lite

CMD [ "python3", "run.py"]
