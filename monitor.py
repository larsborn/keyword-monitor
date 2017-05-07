import requests
import os
import hashlib
from os.path import join
import smtplib
from email.mime.text import MIMEText

base_path = os.environ['KWM_DATA_DIRECTORY']
searx_url = os.environ['KWM_SEARX_URL']


class Source(object):
    def query(self, keyword):
        raise NotImplemented


class Sink(object):
    def notify(self, keyword, tasking, result):
        raise NotImplemented


class Searx(Source):
    def query(self, keyword):
        params = {
            'q': '"%s"' % keyword,
            'categories': 'general',
            'time_range': 'day',
            'format': 'json',
        }
        r = requests.get(searx_url, params=params)
        res = r.json()
        if len(res['results']) == 0:
            return []

        return list(set([r['url'] for r in res['results']]))


class Email(Sink):
    def notify(self, keyword, receiver, new_urls):
        email_body = 'Keyword "%s" has the following fresh results:\r\n\r\n' % keyword
        email_body += '\r\n'.join(new_urls)

        # build the email message
        msg = MIMEText(email_body)
        msg['Subject'] = '[keyword-monitor] %i new URLs for keyword "%s"' % (len(new_urls), keyword)
        msg['From'] = os.environ['KWM_SENDER_ADDRESS']
        msg['To'] = receiver

        server = smtplib.SMTP(os.environ['KWM_SMTP_SERVER'], 587)

        server.ehlo()
        server.starttls()
        server.login(os.environ['KWM_SMTP_USER'], os.environ['KWM_SMTP_PASSWORD'])
        server.sendmail(os.environ['KWM_SMTP_USER'], os.environ['KWM_SMTP_USER'], msg.as_string())
        server.quit()


sources = [Searx()]
sinks = [Email()]


def ensure_and_get_path(tasking, keyword):
    path = join(base_path, tasking, 'responses')
    if not os.path.exists(path): os.mkdir(path)
    return join(path, hashlib.sha256(keyword).hexdigest())


def get_known_urls(tasking, keyword):
    path = ensure_and_get_path(tasking, keyword)
    if not os.path.exists(path): return []
    return [url.strip() for url in open(path, 'r').read().strip().split('\n') if url.strip()]


for source in sources:
    for tasking in os.listdir(base_path):
        email_address = open(join(base_path, tasking, 'info.txt'), 'r').read().strip()
        keywords = open(join(base_path, tasking, 'keywords.txt'), 'r').read().strip().split('\n')
        for keyword in keywords:
            known_urls = set(get_known_urls(tasking, keyword))
            current_urls = set(source.query(keyword))
            new_urls = list(current_urls - known_urls)
            if new_urls:
                open(ensure_and_get_path(tasking, keyword), 'a').write(''.join(['%s\n' % url for url in new_urls]))
                for sink in sinks:
                    sink.notify(keyword, email_address, new_urls)
