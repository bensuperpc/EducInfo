ARG BASE_IMAGE=python:3.12-slim-bookworm
FROM ${BASE_IMAGE} AS base

COPY --from=root-protect ./requirements.txt /work/requirements.txt
WORKDIR /work

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

FROM base AS final

ARG BUILD_DATE=${BUILD_DATE}
ARG VCS_REF=""
ARG VCS_URL="https://github.com/Doalou/EducInfo"
ARG OUTPUT_IMAGE_NAME=${OUTPUT_IMAGE_NAME}
ARG AUTHOR="Doalou"
ARG URL="https://github.com/Doalou/EducInfo"

ARG IMAGE_VERSION="1.0.0"
ENV IMAGE_VERSION=${IMAGE_VERSION}

ENV TERM=xterm-256color

LABEL maintainer="Doalou"
LABEL author="Doalou"
LABEL description=""

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=${BUILD_DATE} \
      org.label-schema.name=${OUTPUT_IMAGE_NAME} \
      org.label-schema.description="" \
      org.label-schema.version=${IMAGE_VERSION} \
      org.label-schema.vendor=${AUTHOR} \
      org.label-schema.url=${URL} \
      org.label-schema.vcs-url=${VCS_URL} \
      org.label-schema.vcs-ref=${VCS_REF} \
      org.label-schema.docker.cmd=""

VOLUME [ "/work" ]
EXPOSE 5000

WORKDIR /work

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh && chown root:root /entrypoint.sh

#ARG USERNAME=user
#RUN useradd -m "${USERNAME}"
# Add color to bash
#RUN echo PS1="'\[\033[01;32m\][\u@\h\[\033[01;37m\] \W\[\033[01;32m\]]\$\[\033[00m\] '" >> "/home/${USERNAME}/.bashrc"
#USER ${USERNAME}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["flask", "run", "--host=0.0.0.0"]

