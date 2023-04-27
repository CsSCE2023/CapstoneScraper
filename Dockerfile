#FROM is the base image for which we will run our application
FROM ubuntu:latest
WORKDIR /core
RUN apt-get update && apt-get -y install python3 python3-pip
RUN apt-get update --fix-missing && apt-get -y install dos2unix
RUN apt-get -y install cron
RUN apt-get -y upgrade
COPY /core/ .
COPY /data/ /data/
COPY /config.ini /config.ini
# COPY chromedriver /chromedriver
# COPY google-chrome-stable_current_amd64.deb .
# RUN apt-get -y update
# RUN apt-get --fix-missing -y install ./google-chrome-stable_current_amd64.deb
# RUN rm google-chrome-stable_current_amd64.deb
RUN chmod 0744 /chromedriver
RUN pip3 install -r requirements.txt
COPY crontab /etc/cron.d/crontab
RUN dos2unix /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log
COPY service_script.conf .
ENV PYTHONPATH /
CMD ["supervisord","-c","service_script.conf"]
