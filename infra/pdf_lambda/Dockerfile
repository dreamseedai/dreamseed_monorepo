# AWS Lambda Python base image (Amazon Linux)
FROM public.ecr.aws/lambda/python:3.11

# System deps for matplotlib/reportlab
RUN yum -y install \ 
        gcc gcc-c++ make \
        freetype-devel libpng-devel zlib-devel \
        libjpeg-turbo-devel \
        fontconfig \
    && yum clean all && rm -rf /var/cache/yum

# (Optional) add fonts directory and register later via env KOREAN_TTF_PATH
# COPY fonts/NotoSansCJK-Regular.ttc /opt/fonts/NotoSansCJK-Regular.ttc

# Python deps
COPY requirements.txt  ./
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Lambda function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# (Optional) set default envs for fonts
# ENV KOREAN_TTF_PATH=/opt/fonts/NotoSansCJK-Regular.ttc
# ENV KOREAN_FONT_NAME=NotoSansCJK

CMD ["lambda_function.handler"]
