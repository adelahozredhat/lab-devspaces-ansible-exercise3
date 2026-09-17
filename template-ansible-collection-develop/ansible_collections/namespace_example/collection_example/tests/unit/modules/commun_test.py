
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import json
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


@pytest.fixture
def module_mock(mocker):
    return mocker.patch.multiple(basic.AnsibleModule,
                                 exit_json=exit_json,
                                 fail_json=fail_json)


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation

    ansible-core 2.19+ requires a serialization profile. Without
    ``_ANSIBLE_PROFILE``, AnsibleModule raises:
    ``No serialization profile was specified.``
    """
    args = dict(args)
    if '_ansible_remote_tmp' not in args:
        args['_ansible_remote_tmp'] = '/tmp'
        args['_ansible_keep_remote_files'] = False
    payload = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(payload)
    if hasattr(basic, '_ANSIBLE_PROFILE'):
        basic._ANSIBLE_PROFILE = 'legacy'
