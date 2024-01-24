FROM quay.io/astronomer/astro-runtime:10.1.0
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt
