FROM python:3.11-slim

RUN apt-get update && apt-get install -y cron

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN echo "0 * * * * /usr/local/bin/python3 /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/my_cron_job
#RUN echo "*/2 * * * * /usr/local/bin/python3 /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/my_cron_job

RUN chmod 0644 /etc/cron.d/my_cron_job
RUN crontab /etc/cron.d/my_cron_job
RUN touch /var/log/cron.log
RUN touch /var/log/app.log

CMD cron -f && tail -f /var/log/cron.log
