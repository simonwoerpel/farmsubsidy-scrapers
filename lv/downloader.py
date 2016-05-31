# coding: utf-8
""" This is a selenium downloader for the Latvian website. """


# The form for requesting data is https://eps.lad.gov.lv/payment_recipients.
# The form gives you the option of downloading a csv file... which is cool.
# Requesting all the data at once times out however. So the way to go is to
# request subsidy schemes one by one and pray to the god of APIs.

from csv import QUOTE_ALL
from logging import getLogger, basicConfig, DEBUG
from os.path import join
from pandas import read_csv
from requests import get
from datetime import datetime
from slugify import slugify


basicConfig(level=DEBUG, format='[%(module)s] %(message)s')
log = getLogger(__name__)


class DataFragment(object):
    BASE_URL = 'https://eps.lad.gov.lv/payment_recipients?'
    BUCKET = '/home/loic/output/farm-subsidies'
    CHUNK_SIZE = 512 * 1024

    def __init__(self, scheme, year=2014):
        self.timestamp = str(datetime.now())
        self.year = int(year)
        self.scheme = scheme
        self.response = None
        self.query = {
            'commit': u'Meklēt',
            'eps_payment[fund]': 'elf',
            'eps_payment[schema]': 'L111.14',
            'eps_payment[year]': self.year,
            'eps_payment[year_type]': 'K',
            'format': 'csv',
            'utf8': u'✓'
        }

    def download(self):
        self.query.update({'eps_payment[schema]': self.scheme})
        self.response = get(self.BASE_URL, params=self.query)
        log.debug('Downloaded scheme %s', self.scheme)

    def save_to_cache(self):
        chunks = self.response.iter_content(chunk_size=self.CHUNK_SIZE)
        with open(self.filepath, 'w+') as cache:
            for chunk in chunks:
                if chunk:
                    cache.write(chunk)
        log.debug('Saved scheme to %s', self.filepath)

    @property
    def filepath(self):
        parts = ['latvia', str(self.year), self.scheme, self.timestamp]
        filename = slugify(unicode('_'.join(parts)))
        return join(self.BUCKET, filename + '.csv')

    @property
    def dataframe(self):
        dataframe = read_csv(self.filepath, sep=':', quoting=QUOTE_ALL, skiprows=[0, 1, 2], encoding='utf-16')
        log.info('Loaded %s (%s rows)', self.name, dataframe.shape[0])
        return dataframe

    @property
    def name(self):
        return 'scheme = %s, year = %s' % (self.scheme, str(self.year))


class Aggregator(object):
    SCHEMES = [
        'L111.14',
        'L002'
        # 'L141'
        # 'L112'
        # 'NATURA',
        # 'ZRG',
        # 'L006;L005',
        # 'L312.21;L312.02;L312.03;L312.11;L312.01',
        # 'ACM',
        # 'ARKIR',
        # 'BDUZ',
        # 'BLA',
        # 'VEI',
        # 'PAAP',
        # 'FDA',
        # 'A004',
        # 'INTVK',
        # 'L125',
        # 'IDIV',
        # 'INZPIE;INZPUA;TKODSRP',
        # 'IKC',
        # 'ISA',
        # 'ILA',
        # 'IPKV',
        # 'NIM',
        # 'L411',
        # 'L123',
        # 'L223',
        # 'L4132.03;L4132.02;L4131.05;L4132.04;L4132.01;L4131.01;L4132.05;L4131.02;L4131.03'
    ]

    def __init__(self, year=2014):
        self.year = year

    @property
    def dataframes(self):
        for scheme in self.SCHEMES:
            fragment = DataFragment(scheme)
            fragment.download()
            fragment.save_to_cache()
            yield fragment.dataframe

    def aggregate(self):
        for df in self.dataframes:
            log.debug('Aggregated %s rows', df.shape[0])


if __name__ == '__main__':
    aggregator = Aggregator(2014)
    aggregator.aggregate()
