from django_forwarded import Forwarded
from unittest import mock, TestCase
from django.test import override_settings


class Depth1(TestCase):
    @override_settings(TRUSTED_PROXY_DEPTH=1)
    def setUp(self):
        self.middleware = Forwarded(get_response=lambda x: x)
        self.request = mock.Mock()
        self.request.META = {
            "REMOTE_ADDR": "127.0.0.1",
        }

    def test_no_proxy(self):
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '127.0.0.1')

    def test_empty(self):
        self.request.META['HTTP_FORWARDED'] = ''
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '127.0.0.1')

    def test_invalid(self):
        self.request.META['HTTP_FORWARDED'] = 'dfajsd, dsfsad,dsasf; ;4w8rr89347e;asfs;df; adsf;dasf;asdf'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '127.0.0.1')

    def test_valid_ipv4(self):
        self.request.META['HTTP_FORWARDED'] = 'for=192.168.1.1;host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_valid_ipv6(self):
        self.request.META['HTTP_FORWARDED'] = 'for="[2001::1]";host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::1')

    def test_multiple_proxies(self):
        self.request.META['HTTP_FORWARDED'] = ('for="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::2]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::3]";host=example.com;proto=https;proto-version=""')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::3')


class Depth2(TestCase):
    @override_settings(TRUSTED_PROXY_DEPTH=2)
    def setUp(self):
        self.middleware = Forwarded(get_response=lambda x: x)
        self.request = mock.Mock()
        self.request.META = {
            "REMOTE_ADDR": "127.0.0.1",
        }

    def test_single_proxy(self):
        self.request.META['HTTP_FORWARDED'] = 'for="[2001::1]";host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::1')

    def test_multiple_proxies(self):
        self.request.META['HTTP_FORWARDED'] = ('for="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::2]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::3]";host=example.com;proto=https;proto-version=""')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::2')


class TrustedList(TestCase):
    @override_settings(TRUSTED_PROXY_LIST=[
        "192.168.1.1",
        "2001::1",
        "172.16.100.101",
        "2001::10:10",
    ])
    def setUp(self):
        self.middleware = Forwarded(get_response=lambda x: x)
        self.request = mock.Mock()
        self.request.META = {
            "REMOTE_ADDR": "192.168.1.1",
        }

    def test_no_proxy(self):
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_empty(self):
        self.request.META['HTTP_FORWARDED'] = ''
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_invalid(self):
        self.request.META['HTTP_FORWARDED'] = 'dfajsd, dsfsad,dsasf; ;4w8rr89347e;asfs;df; adsf;dasf;asdf'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_fake_header(self):
        self.request.META['HTTP_FORWARDED'] = 'for=192.168.12.10;by=10.2.3.1;host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_missing_by_parameter(self):
        self.request.META['HTTP_FORWARDED'] = 'for=172.16.100.100;host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.1.1')

    def test_missing_by_parameter_in_chain(self):
        self.request.META['HTTP_FORWARDED'] = ('for=172.16.43.100;by="[2001::10:10]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::10:10]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::1]";by=192.168.1.1;host=example.com;proto=https;proto-version=""')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::1')

    def test_spoofed_header(self):
        self.request.META['HTTP_FORWARDED'] = ('for="[2001::2]";by="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::123]";by=192.168.1.1;host=example.com;proto=https;proto-version="", ')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::123')

    def test_untrusted_origin(self):
        self.request.META['REMOTE_ADDR'] = '172.16.21.42'
        self.request.META['HTTP_FORWARDED'] = ('for="[2001::2]";by="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::123]";by=192.168.1.1;host=example.com;proto=https;proto-version="", ')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '172.16.21.42')

    def test_untrusted_chain(self):
        self.request.META['HTTP_FORWARDED'] = ('for="[2001::2]";by="[2001::1:1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::1:1]";by=192.168.1.1;host=example.com;proto=https;proto-version="", ')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::1:1')

    def test_valid_ipv4(self):
        self.request.META['HTTP_FORWARDED'] = 'for=192.168.12.10;by=192.168.1.1;host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '192.168.12.10')

    def test_valid_ipv6(self):
        self.request.META['HTTP_FORWARDED'] = 'for="[2001::2]";by="192.168.1.1";host=example.com;proto=https;proto-version=""'
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '2001::2')

    def test_multiple_proxies(self):
        self.request.META['HTTP_FORWARDED'] = ('for=172.16.43.100;by="[2001::10:10]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::10:10]";by="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::1]";by=192.168.1.1;host=example.com;proto=https;proto-version=""')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '172.16.43.100')

    def test_multiple_fake_proxies(self):
        self.request.META['HTTP_FORWARDED'] = ('for=172.16.43.100;by="[2001::100:10]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::100:10]";by="[2001::100:11]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::100:11]";by="[2001::100:12]";host=example.com;proto=https;proto-version="", '
                                               'for=172.16.4.190;by="[2001::10:10]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::10:10]";by="[2001::1]";host=example.com;proto=https;proto-version="", '
                                               'for="[2001::1]";by=192.168.1.1;host=example.com;proto=https;proto-version=""')
        response = self.middleware(self.request)
        self.assertEqual(response.META['REMOTE_ADDR'], '172.16.4.190')
