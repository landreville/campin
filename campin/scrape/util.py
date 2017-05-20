from urllib.parse import urljoin


def extract(el, xpath):
    return ''.join(el.xpath(xpath).extract())


def text(el):
    return extract(el, 'text()')


def full_link(response, relative_url):
    return urljoin(response.url, relative_url)
