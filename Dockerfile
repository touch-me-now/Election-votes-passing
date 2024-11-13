FROM python:3.11-slim

RUN apt-get update && apt-get install -y cron

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN echo "0 * * * * python3 main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/my_cron_job
RUN chmod 0644 /etc/cron.d/my_cron_job
RUN crontab /etc/cron.d/my_cron_job
RUN touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log