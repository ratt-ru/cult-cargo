FROM kernsuite/base:{kern_version}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y upgrade && \
    apt-get install apt-utils && \
    apt-get install -y python3 python3-pip wget git \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives


