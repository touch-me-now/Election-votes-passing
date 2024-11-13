Just an application for asynchronously parsing votes of parties in the elections of the Kyrgyz Republic. linux/mac cron runs every hour in docker container

The data is saved in mongo and is not duplicated. Fields to which items are bound:
    "name", "region_id", "city_slug".

### Running requires:
- Python 3.11 (tested under Python 3.11)

### Create environment file in BASE DIR .env (see .env-example)
> :warning: **Required!**
```text
    .
    ├── ...
    ├── Base dir
    │   ├── .env-example
>>> │   ├── .env
    │   ├── main.py
    │   └── ...
    └── ...
```

### Build docker container
```bash
docker build -t cron-python-job .
```

### Running docker container
```bash
docker run -d --name cron-job-container cron-python-job
```

### Local running
```bash
python3 main.py
```

