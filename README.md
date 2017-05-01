# keyword-monitoring

Queries a [searx](https://github.com/asciimoo/searx) instance for a list of keywords and sends email notifications, if
the result set changes.

## Usage
Set the following environment variables and run monitor.py

* `KWM_DATA_DIRECTORY` directory containing tasking and response data. Each subdir should contain an info.txt containing exactly one email address and a keywords.txt with the keywords to be queried.
* `KWM_SEARX_URL` URL of searx instance
* `KWM_SMTP_SERVER`, `KWM_SMTP_USER`, `KWM_SMTP_PASSWORD` SMTP credentials for email notifications

