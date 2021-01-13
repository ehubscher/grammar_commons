FROM continuumio/miniconda3:4.7.10-alpine AS installer

ENV PATH /home/anaconda/.local/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV APP_NAME namespace_name_package_name

RUN apk add --update bash
RUN conda init
RUN conda create --name ${APP_NAME} python=3.7 && echo "conda activate ${APP_NAME}" > ~/.bashrc

ENV PATH  /opt/conda/envs/${APP_NAME}/bin:$PATH

WORKDIR /workspaces/${APP_NAME}
COPY . .

RUN pip install -e .
