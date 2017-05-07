import requests
import os
import hashlib
from os.path import join
import smtplib
from email.mime.text import MIMEText


class Source(object):
    def query(self, keyword):
        raise NotImplemented


class Sink(object):
    def notify(self, keyword, tasking, result):
        raise NotImplemented


class Searx(Source):
    def __init__(self, searx_url):
        self.searx_url = searx_url

    def query(self, keyword):
        params = {
            'q': '"%s"' % keyword,
            'categories': 'general',
            'time_range': 'day',
            'format': 'json',
        }
        r = requests.get(self.searx_url, params=params)
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


def ensure_and_get_path(tasking, keyword):
    path = join(base_path, tasking, 'responses')
    if not os.path.exists(path): os.mkdir(path)
    return join(path, hashlib.sha256(keyword).hexdigest())


def get_known_urls(tasking):
    path = join(base_path, tasking, 'responses')
    if not os.path.exists(path): return []
    ret = []
    for file in os.listdir(path):
        ret += [url.strip() for url in open(os.path.join(path, file), 'r').read().strip().split('\n') if url.strip()]
    return ret


if __name__ == "__main__":
    base_path = os.environ['KWM_DATA_DIRECTORY']
    sources = [Searx(os.environ['KWM_SEARX_URL'])]
    sinks = [Email()]

    for source in sources:
        for tasking in os.listdir(base_path):
            known_urls = set(get_known_urls(tasking))
            email_address = open(join(base_path, tasking, 'info.txt'), 'r').read().strip()
            keywords = open(join(base_path, tasking, 'keywords.txt'), 'r').read().strip().split('\n')
            for keyword in keywords:
                current_urls = set(source.query(keyword))
                new_urls = list(current_urls - known_urls)
                if new_urls:
                    open(ensure_and_get_path(tasking, keyword), 'a').write(''.join(['%s\n' % url for url in new_urls]))
                    for sink in sinks:
                        sink.notify(keyword, email_address, new_urls)
