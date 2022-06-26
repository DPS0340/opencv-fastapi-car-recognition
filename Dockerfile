FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# Install latest updates
RUN apt update -y

# Install Python and build libraries
RUN apt install -y \
    python3.9 \
    python3.9-distutils \
    python3-pip \
    python-is-python3 \
    ffmpeg \
    x264 \
    libx264-dev

COPY ./requirements.txt .

# Install the dependencies specified in requirements file
RUN pip install -r requirements.txt

COPY . .

WORKDIR ./src

ENTRYPOINT [ "uvicorn", "main:app", "--host", "0.0.0.0" ]
