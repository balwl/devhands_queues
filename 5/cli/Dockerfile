FROM ubuntu:24.04

RUN apt-get update
RUN apt-get install curl -y
RUN cd /usr/bin && curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh

ENV LANG=C.UTF-8
WORKDIR /root