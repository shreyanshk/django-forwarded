# Copyright 2019 CERN
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This software is distributed under the terms of the Apache version 2 licence,
# copied verbatim in the file “LICENSE”.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

from django.conf import settings


class Forwarded:
    def __init__(self, get_response):
        self.get_response = get_response
        trusted_depth = getattr(settings, 'TRUSTED_PROXY_DEPTH', None)
        trusted_list = getattr(settings, 'TRUSTED_PROXY_LIST', None)
        if trusted_list is not None:
            assert (type(trusted_list) == list), "invalid value for TRUSTED_PROXY_LIST. must be a list"
            for trusted_proxy in trusted_list:
                assert (type(trusted_proxy) == str), "invalid value in TRUSTED_PROXY_LIST. must be a string"
            self.trusted_list = trusted_list
            self.get_client_ip = self._get_client_ip_by_trusted_list
        elif trusted_depth is not None:
            assert ((type(trusted_depth) == int) and trusted_depth >= 1), "invalid value for TRUSTED_PROXY_DEPTH. must be >= 1"
            self.trusted_depth = trusted_depth
            self.get_client_ip = self._get_client_ip_by_trusted_depth
        else:
            raise RuntimeError("invalid configuration, neither TRUSTED_PROXY_DEPTH nor TRUSTED_PROXY_LIST is defined in configuration")

    def __call__(self, request):
        try:
            forwarded_header = request.META['HTTP_FORWARDED']
        except KeyError:  # header was not found
            return self.get_response(request)

        parsed_header = self.parse_forwarded_header(forwarded_header)  # python lists are ordered
        client_ip = self.get_client_ip(parsed_header, request.META['REMOTE_ADDR'])
        request.META['REMOTE_ADDR'] = client_ip
        return self.get_response(request)

    def parse_forwarded_header(self, forwarded_header):
        proxy_str_list = [x.strip() for x in forwarded_header.split(",")]
        proxies = list()
        for proxy_str in proxy_str_list:
            param_str_list = proxy_str.split(';')
            data = {}
            for param_str in param_str_list:
                try:
                    k, v = param_str.split("=")
                    k = k.lower()  # the keys are case insensitive
                    if k in ['by', 'for', 'host']:
                        v = v[1:-1] if (len(v) >= 2) and ((v[0] + v[-1] == '""') or (v[0] + v[-1] == "''")) else v
                        v = v[1:-1] if (len(v) >= 2) and (v[0] + v[-1] == '[]') else v
                    data[k] = v
                except ValueError:  # malformed parameter
                    pass
            if data:
                proxies.append(data)
        return proxies

    def _get_client_ip_by_trusted_list(self, proxies, request_ip):
        reversed_proxy_list = reversed(list(proxies))
        last_trusted_client_ip = request_ip
        for proxy in reversed_proxy_list:
            try:
                proxy_addr = proxy['by']
                client_addr = proxy['for']
                if last_trusted_client_ip == proxy_addr and proxy_addr in self.trusted_list:
                    last_trusted_client_ip = client_addr
                else:
                    return last_trusted_client_ip
            except KeyError:
                return last_trusted_client_ip
        return last_trusted_client_ip

    def _get_client_ip_by_trusted_depth(self, proxies, request_ip):
        trusted_proxies = proxies[-self.trusted_depth:] if len(proxies) > self.trusted_depth else proxies
        for proxy in trusted_proxies:
            if proxy.get('for', None):
                return proxy['for']
        return request_ip  # everything failed! so return remote address from request
