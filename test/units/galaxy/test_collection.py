# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import pytest
import re
import tarfile
import tempfile
import uuid

from hashlib import sha256
from io import BytesIO
from unittest.mock import MagicMock, mock_open, patch

import ansible.constants as C
from ansible import context
from ansible.cli.galaxy import GalaxyCLI, SERVER_DEF
from ansible.errors import AnsibleError
from ansible.galaxy import api, collection, token
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six.moves import builtins
from ansible.utils import context_objects as co
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash_s
from ansible.utils.sentinel import Sentinel


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture()
def collection_input(tmp_path_factory):
    ''' Creates a collection skeleton directory for build tests '''
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    namespace = 'ansible_namespace'
    collection = 'collection'
    skeleton = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'collection_skeleton')

    galaxy_args = ['ansible-galaxy', 'collection', 'init', '%s.%s' % (namespace, collection),
                   '-c', '--init-path', test_dir, '--collection-skeleton', skeleton]
    GalaxyCLI(args=galaxy_args).run()
    collection_dir = os.path.join(test_dir, namespace, collection)
    output_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Output'))

    return collection_dir, output_dir


@pytest.fixture()
def collection_artifact(monkeypatch, tmp_path_factory):
    ''' Creates a temp collection artifact and mocked open_url instance for publishing tests '''
    mock_open = MagicMock()
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    mock_uuid = MagicMock()
    mock_uuid.return_value.hex = 'uuid'
    monkeypatch.setattr(uuid, 'uuid4', mock_uuid)

    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    input_file = to_text(tmp_path / 'collection.tar.gz')

    with tarfile.open(input_file, 'w:gz') as tfile:
        b_io = BytesIO(b"\x00\x01\x02\x03")
        tar_info = tarfile.TarInfo('test')
        tar_info.size = 4
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    return input_file, mock_open


@pytest.fixture()
def galaxy_yml_dir(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    b_galaxy_yml = os.path.join(b_test_dir, b'galaxy.yml')
    with open(b_galaxy_yml, 'wb') as galaxy_obj:
        galaxy_obj.write(to_bytes(request.param))

    yield b_test_dir


@pytest.fixture()
def tmp_tarfile(tmp_path_factory, manifest_info):
    ''' Creates a temporary tar file for _extract_tar_file tests '''
    filename = u'ÅÑŚÌβŁÈ'
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-%s Collections' % to_native(filename)))
    tar_file = os.path.join(temp_dir, to_bytes('%s.tar.gz' % filename))
    data = os.urandom(8)

    with tarfile.open(tar_file, 'w:gz') as tfile:
        b_io = BytesIO(data)
        tar_info = tarfile.TarInfo(filename)
        tar_info.size = len(data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

        b_data = to_bytes(json.dumps(manifest_info, indent=True), errors='surrogate_or_strict')
        b_io = BytesIO(b_data)
        tar_info = tarfile.TarInfo('MANIFEST.json')
        tar_info.size = len(b_data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    sha256_hash = sha256()
    sha256_hash.update(data)

    with tarfile.open(tar_file, 'r') as tfile:
        yield temp_dir, tfile, filename, sha256_hash.hexdigest()


@pytest.fixture()
def galaxy_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(None, 'test_server', 'https://galaxy.ansible.com',
                               token=token.GalaxyToken(token='key'))
    return galaxy_api


@pytest.fixture()
def manifest_template():
    def get_manifest_info(namespace='ansible_namespace', name='collection', version='0.1.0'):
        return {
            "collection_info": {
                "namespace": namespace,
                "name": name,
                "version": version,
                "authors": [
                    "shertel"
                ],
                "readme": "README.md",
                "tags": [
                    "test",
                    "collection"
                ],
                "description": "Test",
                "license": [
                    "MIT"
                ],
                "license_file": None,
                "dependencies": {},
                "repository": "https://github.com/{0}/{1}".format(namespace, name),
                "documentation": None,
                "homepage": None,
                "issues": None
            },
            "file_manifest_file": {
                "name": "FILES.json",
                "ftype": "file",
                "chksum_type": "sha256",
                "chksum_sha256": "files_manifest_checksum",
                "format": 1
            },
            "format": 1
        }

    return get_manifest_info


@pytest.fixture()
def manifest_info(manifest_template):
    return manifest_template()


@pytest.fixture()
def files_manifest_info():
    return {
        "files": [
            {
                "name": ".",
                "ftype": "dir",
                "chksum_type": None,
                "chksum_sha256": None,
                "format": 1
            },
            {
                "name": "README.md",
                "ftype": "file",
                "chksum_type": "sha256",
                "chksum_sha256": "individual_file_checksum",
                "format": 1
            }
        ],
        "format": 1}


@pytest.fixture()
def manifest(manifest_info):
    b_data = to_bytes(json.dumps(manifest_info))

    with patch.object(builtins, 'open', mock_open(read_data=b_data)) as m:
        with open('MANIFEST.json', mode='rb') as fake_file:
            yield fake_file, sha256(b_data).hexdigest()


@pytest.fixture()
def server_config(monkeypatch):
    monkeypatch.setattr(C, 'GALAXY_SERVER_LIST', ['server1', 'server2', 'server3'])

    default_options = dict((k, None) for k, v, t in SERVER_DEF)

    server1 = dict(default_options)
    server1.update({'url': 'https://galaxy.ansible.com/api/', 'validate_certs': False})

    server2 = dict(default_options)
    server2.update({'url': 'https://galaxy.ansible.com/api/', 'validate_certs': True})

    server3 = dict(default_options)
    server3.update({'url': 'https://galaxy.ansible.com/api/'})

    return server1, server2, server3


@pytest.mark.parametrize(
    'required_signature_count,valid',
    [
        ("1", True),
        ("+1", True),
        ("all", True),
        ("+all", True),
        ("-1", False),
        ("invalid", False),
        ("1.5", False),
        ("+", False),
    ]
)
def test_cli_options(required_signature_count, valid, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
        '--keyring',
        '~/.ansible/pubring.kbx',
        '--required-valid-signature-count',
        required_signature_count
    ]

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)

    if valid:
        galaxy_cli.run()
    else:
        with pytest.raises(SystemExit, match='2') as error:
            galaxy_cli.run()


@pytest.mark.parametrize(
    "config,server",
    [
        (
            # Options to create ini config
            {
                'url': 'https://galaxy.ansible.com',
                'validate_certs': 'False',
                'v3': 'False',
            },
            # Expected server attributes
            {
                'validate_certs': False,
                '_available_api_versions': {},
            },
        ),
        (
            {
                'url': 'https://galaxy.ansible.com',
                'validate_certs': 'True',
                'v3': 'True',
            },
            {
                'validate_certs': True,
                '_available_api_versions': {'v3': '/v3'},
            },
        ),
    ],
)
def test_bool_type_server_config_options(config, server, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]

    config_lines = [
        "[galaxy]",
        "server_list=server1\n",
        "[galaxy_server.server1]",
        "url=%s" % config['url'],
        "v3=%s" % config['v3'],
        "validate_certs=%s\n" % config['validate_certs'],
    ]

    with tempfile.NamedTemporaryFile(suffix='.cfg') as tmp_file:
        tmp_file.write(
            to_bytes('\n'.join(config_lines))
        )
        tmp_file.flush()

        with patch.object(C, 'GALAXY_SERVER_LIST', ['server1']):
            with patch.object(C.config, '_config_file', tmp_file.name):
                C.config._parse_config_file()
                galaxy_cli = GalaxyCLI(args=cli_args)
                mock_execute_install = MagicMock()
                monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
                galaxy_cli.run()

    assert galaxy_cli.api_servers[0].name == 'server1'
    assert galaxy_cli.api_servers[0].validate_certs == server['validate_certs']
    assert galaxy_cli.api_servers[0]._available_api_versions == server['_available_api_versions']


@pytest.mark.parametrize('global_ignore_certs', [True, False])
def test_validate_certs(global_ignore_certs, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]
    if global_ignore_certs:
        cli_args.append('--ignore-certs')

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert len(galaxy_cli.api_servers) == 1
    assert galaxy_cli.api_servers[0].validate_certs is not global_ignore_certs


@pytest.mark.parametrize('global_ignore_certs', [True, False])
def test_validate_certs_with_server_url(global_ignore_certs, monkeypatch):
    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
        '-s',
        'https://galaxy.ansible.com'
    ]
    if global_ignore_certs:
        cli_args.append('--ignore-certs')

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert len(galaxy_cli.api_servers) == 1
    assert galaxy_cli.api_servers[0].validate_certs is not global_ignore_certs


@pytest.mark.parametrize('global_ignore_certs', [True, False])
def test_validate_certs_with_server_config(global_ignore_certs, server_config, monkeypatch):

    # test sidesteps real resolution and forces the server config to override the cli option
    get_plugin_options = MagicMock(side_effect=server_config)
    monkeypatch.setattr(C.config, 'get_plugin_options', get_plugin_options)

    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]
    if global_ignore_certs:
        cli_args.append('--ignore-certs')

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    # server cfg, so should match def above, if not specified so it should use default (true)
    assert galaxy_cli.api_servers[0].validate_certs is server_config[0].get('validate_certs', True)
    assert galaxy_cli.api_servers[1].validate_certs is server_config[1].get('validate_certs', True)
    assert galaxy_cli.api_servers[2].validate_certs is server_config[2].get('validate_certs', True)


def test_build_collection_no_galaxy_yaml():
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection galaxy.yml path '%s/galaxy.yml' does not exist." % fake_path)

    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(fake_path, u'output', False)


def test_build_existing_output_file(collection_input):
    input_dir, output_dir = collection_input

    existing_output_dir = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    os.makedirs(existing_output_dir)

    expected = "The output collection artifact '%s' already exists, but is a directory - aborting" \
               % to_native(existing_output_dir)
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)


def test_build_existing_output_without_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    expected = "The file '%s' already exists. You can use --force to re-create the collection artifact." \
               % to_native(existing_output)
    with pytest.raises(AnsibleError, match=expected):
        collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)


def test_build_existing_output_with_force(collection_input):
    input_dir, output_dir = collection_input

    existing_output = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    with open(existing_output, 'w+') as out_file:
        out_file.write("random garbage")
        out_file.flush()

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), True)

    # Verify the file was replaced with an actual tar file
    assert tarfile.is_tarfile(existing_output)


def test_build_with_existing_files_and_manifest(collection_input):
    input_dir, output_dir = collection_input

    with open(os.path.join(input_dir, 'MANIFEST.json'), "wb") as fd:
        fd.write(b'{"collection_info": {"version": "6.6.6"}, "version": 1}')

    with open(os.path.join(input_dir, 'FILES.json'), "wb") as fd:
        fd.write(b'{"files": [], "format": 1}')

    with open(os.path.join(input_dir, "plugins", "MANIFEST.json"), "wb") as fd:
        fd.write(b"test data that should be in build")

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        manifest_file = next(m for m in members if m.path == "MANIFEST.json")
        manifest_file_obj = actual.extractfile(manifest_file.name)
        manifest_file_text = manifest_file_obj.read()
        manifest_file_obj.close()
        assert manifest_file_text != b'{"collection_info": {"version": "6.6.6"}, "version": 1}'

        json_file = next(m for m in members if m.path == "MANIFEST.json")
        json_file_obj = actual.extractfile(json_file.name)
        json_file_text = json_file_obj.read()
        json_file_obj.close()
        assert json_file_text != b'{"files": [], "format": 1}'

        sub_manifest_file = next(m for m in members if m.path == "plugins/MANIFEST.json")
        sub_manifest_file_obj = actual.extractfile(sub_manifest_file.name)
        sub_manifest_file_text = sub_manifest_file_obj.read()
        sub_manifest_file_obj.close()
        assert sub_manifest_file_text == b"test data that should be in build"


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: value: broken'], indirect=True)
def test_invalid_yaml_galaxy_file(galaxy_yml_dir):
    galaxy_file = os.path.join(galaxy_yml_dir, b'galaxy.yml')
    expected = to_native(b"Failed to parse the galaxy.yml at '%s' with the following error:" % galaxy_file)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: test_namespace'], indirect=True)
def test_missing_required_galaxy_key(galaxy_yml_dir):
    galaxy_file = os.path.join(galaxy_yml_dir, b'galaxy.yml')
    expected = "The collection galaxy.yml at '%s' is missing the following mandatory keys: authors, name, " \
               "readme, version" % to_native(galaxy_file)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b'namespace: test_namespace'], indirect=True)
def test_galaxy_yaml_no_mandatory_keys(galaxy_yml_dir):
    expected = "The collection galaxy.yml at '%s/galaxy.yml' is missing the " \
               "following mandatory keys: authors, name, readme, version" % to_native(galaxy_yml_dir)

    with pytest.raises(ValueError, match=expected):
        assert collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir, require_build_metadata=False) == expected


@pytest.mark.parametrize('galaxy_yml_dir', [b'My life story is so very interesting'], indirect=True)
def test_galaxy_yaml_no_mandatory_keys_bad_yaml(galaxy_yml_dir):
    expected = "The collection galaxy.yml at '%s/galaxy.yml' is incorrectly formatted." % to_native(galaxy_yml_dir)

    with pytest.raises(AnsibleError, match=expected):
        collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
invalid: value"""], indirect=True)
def test_warning_extra_keys(galaxy_yml_dir, monkeypatch):
    display_mock = MagicMock()
    monkeypatch.setattr(Display, 'warning', display_mock)

    collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)

    assert display_mock.call_count == 1
    assert display_mock.call_args[0][0] == "Found unknown keys in collection galaxy.yml at '%s/galaxy.yml': invalid"\
        % to_text(galaxy_yml_dir)


@pytest.mark.parametrize('galaxy_yml_dir', [b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md"""], indirect=True)
def test_defaults_galaxy_yml(galaxy_yml_dir):
    actual = collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)

    assert actual['namespace'] == 'namespace'
    assert actual['name'] == 'collection'
    assert actual['authors'] == ['Jordan']
    assert actual['version'] == '0.1.0'
    assert actual['readme'] == 'README.md'
    assert actual['description'] is None
    assert actual['repository'] is None
    assert actual['documentation'] is None
    assert actual['homepage'] is None
    assert actual['issues'] is None
    assert actual['tags'] == []
    assert actual['dependencies'] == {}
    assert actual['license'] == []


@pytest.mark.parametrize('galaxy_yml_dir', [(b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
license: MIT"""), (b"""
namespace: namespace
name: collection
authors: Jordan
version: 0.1.0
readme: README.md
license:
- MIT""")], indirect=True)
def test_galaxy_yml_list_value(galaxy_yml_dir):
    actual = collection.concrete_artifact_manager._get_meta_from_src_dir(galaxy_yml_dir)
    assert actual['license'] == ['MIT']


def test_build_ignore_files_and_folders(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    git_folder = os.path.join(input_dir, '.git')
    retry_file = os.path.join(input_dir, 'ansible.retry')

    tests_folder = os.path.join(input_dir, 'tests', 'output')
    tests_output_file = os.path.join(tests_folder, 'result.txt')

    os.makedirs(git_folder)
    os.makedirs(tests_folder)

    with open(retry_file, 'w+') as ignore_file:
        ignore_file.write('random')
        ignore_file.flush()

    with open(tests_output_file, 'w+') as tests_file:
        tests_file.write('random')
        tests_file.flush()

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel)

    assert actual['format'] == 1
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] not in ['.git', 'ansible.retry', 'galaxy.yml', 'tests/output', 'tests/output/result.txt']

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s' for collection build" % to_text(retry_file),
        "Skipping '%s' for collection build" % to_text(git_folder),
        "Skipping '%s' for collection build" % to_text(tests_folder),
    ]
    assert mock_display.call_count == 4
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs
    assert mock_display.mock_calls[2][1][0] in expected_msgs
    assert mock_display.mock_calls[3][1][0] in expected_msgs


def test_build_ignore_older_release_in_root(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    # This is expected to be ignored because it is in the root collection dir.
    release_file = os.path.join(input_dir, 'namespace-collection-0.0.0.tar.gz')

    # This is not expected to be ignored because it is not in the root collection dir.
    fake_release_file = os.path.join(input_dir, 'plugins', 'namespace-collection-0.0.0.tar.gz')

    for filename in [release_file, fake_release_file]:
        with open(filename, 'w+') as file_obj:
            file_obj.write('random')
            file_obj.flush()

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel)
    assert actual['format'] == 1

    plugin_release_found = False
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] != 'namespace-collection-0.0.0.tar.gz'
        if manifest_entry['name'] == 'plugins/namespace-collection-0.0.0.tar.gz':
            plugin_release_found = True

    assert plugin_release_found

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s' for collection build" % to_text(release_file)
    ]
    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs


def test_build_ignore_patterns(collection_input, monkeypatch):
    input_dir = collection_input[0]

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_display)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection',
                                              ['*.md', 'plugins/action', 'playbooks/*.j2'],
                                              Sentinel)
    assert actual['format'] == 1

    expected_missing = [
        'README.md',
        'docs/My Collection.md',
        'plugins/action',
        'playbooks/templates/test.conf.j2',
        'playbooks/templates/subfolder/test.conf.j2',
    ]

    # Files or dirs that are close to a match but are not, make sure they are present
    expected_present = [
        'docs',
        'roles/common/templates/test.conf.j2',
        'roles/common/templates/subfolder/test.conf.j2',
    ]

    actual_files = [e['name'] for e in actual['files']]
    for m in expected_missing:
        assert m not in actual_files

    for p in expected_present:
        assert p in actual_files

    expected_msgs = [
        "Skipping '%s/galaxy.yml' for collection build" % to_text(input_dir),
        "Skipping '%s/README.md' for collection build" % to_text(input_dir),
        "Skipping '%s/docs/My Collection.md' for collection build" % to_text(input_dir),
        "Skipping '%s/plugins/action' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/test.conf.j2' for collection build" % to_text(input_dir),
        "Skipping '%s/playbooks/templates/subfolder/test.conf.j2' for collection build" % to_text(input_dir),
    ]
    assert mock_display.call_count == len(expected_msgs)
    assert mock_display.mock_calls[0][1][0] in expected_msgs
    assert mock_display.mock_calls[1][1][0] in expected_msgs
    assert mock_display.mock_calls[2][1][0] in expected_msgs
    assert mock_display.mock_calls[3][1][0] in expected_msgs
    assert mock_display.mock_calls[4][1][0] in expected_msgs
    assert mock_display.mock_calls[5][1][0] in expected_msgs


def test_build_ignore_symlink_target_outside_collection(collection_input, monkeypatch):
    input_dir, outside_dir = collection_input

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_display)

    link_path = os.path.join(input_dir, 'plugins', 'connection')
    os.symlink(outside_dir, link_path)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel)
    for manifest_entry in actual['files']:
        assert manifest_entry['name'] != 'plugins/connection'

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == "Skipping '%s' as it is a symbolic link to a directory outside " \
                                               "the collection" % to_text(link_path)


def test_build_copy_symlink_target_inside_collection(collection_input):
    input_dir = collection_input[0]

    os.makedirs(os.path.join(input_dir, 'playbooks', 'roles'))
    roles_link = os.path.join(input_dir, 'playbooks', 'roles', 'linked')

    roles_target = os.path.join(input_dir, 'roles', 'linked')
    roles_target_tasks = os.path.join(roles_target, 'tasks')
    os.makedirs(roles_target_tasks)
    with open(os.path.join(roles_target_tasks, 'main.yml'), 'w+') as tasks_main:
        tasks_main.write("---\n- hosts: localhost\n  tasks:\n  - ping:")
        tasks_main.flush()

    os.symlink(roles_target, roles_link)

    actual = collection._build_files_manifest(to_bytes(input_dir), 'namespace', 'collection', [], Sentinel)

    linked_entries = [e for e in actual['files'] if e['name'].startswith('playbooks/roles/linked')]
    assert len(linked_entries) == 1
    assert linked_entries[0]['name'] == 'playbooks/roles/linked'
    assert linked_entries[0]['ftype'] == 'dir'


def test_build_with_symlink_inside_collection(collection_input):
    input_dir, output_dir = collection_input

    os.makedirs(os.path.join(input_dir, 'playbooks', 'roles'))
    roles_link = os.path.join(input_dir, 'playbooks', 'roles', 'linked')
    file_link = os.path.join(input_dir, 'docs', 'README.md')

    roles_target = os.path.join(input_dir, 'roles', 'linked')
    roles_target_tasks = os.path.join(roles_target, 'tasks')
    os.makedirs(roles_target_tasks)
    with open(os.path.join(roles_target_tasks, 'main.yml'), 'w+') as tasks_main:
        tasks_main.write("---\n- hosts: localhost\n  tasks:\n  - ping:")
        tasks_main.flush()

    os.symlink(roles_target, roles_link)
    os.symlink(os.path.join(input_dir, 'README.md'), file_link)

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        linked_folder = next(m for m in members if m.path == 'playbooks/roles/linked')
        assert linked_folder.type == tarfile.SYMTYPE
        assert linked_folder.linkname == '../../roles/linked'

        linked_file = next(m for m in members if m.path == 'docs/README.md')
        assert linked_file.type == tarfile.SYMTYPE
        assert linked_file.linkname == '../README.md'

        linked_file_obj = actual.extractfile(linked_file.name)
        actual_file = secure_hash_s(linked_file_obj.read())
        linked_file_obj.close()

        assert actual_file == '63444bfc766154e1bc7557ef6280de20d03fcd81'


def test_publish_no_wait(galaxy_server, collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = collection_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v2/import/1234'

    mock_publish = MagicMock()
    mock_publish.return_value = fake_import_uri
    monkeypatch.setattr(galaxy_server, 'publish_collection', mock_publish)

    collection.publish_collection(artifact_path, galaxy_server, False, 0)

    assert mock_publish.call_count == 1
    assert mock_publish.mock_calls[0][1][0] == artifact_path

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == \
        "Collection has been pushed to the Galaxy server %s %s, not waiting until import has completed due to " \
        "--no-wait being set. Import task results can be found at %s" % (galaxy_server.name, galaxy_server.api_server,
                                                                         fake_import_uri)


def test_publish_with_wait(galaxy_server, collection_artifact, monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    artifact_path, mock_open = collection_artifact
    fake_import_uri = 'https://galaxy.server.com/api/v2/import/1234'

    mock_publish = MagicMock()
    mock_publish.return_value = fake_import_uri
    monkeypatch.setattr(galaxy_server, 'publish_collection', mock_publish)

    mock_wait = MagicMock()
    monkeypatch.setattr(galaxy_server, 'wait_import_task', mock_wait)

    collection.publish_collection(artifact_path, galaxy_server, True, 0)

    assert mock_publish.call_count == 1
    assert mock_publish.mock_calls[0][1][0] == artifact_path

    assert mock_wait.call_count == 1
    assert mock_wait.mock_calls[0][1][0] == '1234'

    assert mock_display.mock_calls[0][1][0] == "Collection has been published to the Galaxy server test_server %s" \
        % galaxy_server.api_server


def test_find_existing_collections(tmp_path_factory, monkeypatch):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    collection1 = os.path.join(test_dir, 'namespace1', 'collection1')
    collection2 = os.path.join(test_dir, 'namespace2', 'collection2')
    fake_collection1 = os.path.join(test_dir, 'namespace3', 'collection3')
    fake_collection2 = os.path.join(test_dir, 'namespace4')
    os.makedirs(collection1)
    os.makedirs(collection2)
    os.makedirs(os.path.split(fake_collection1)[0])

    open(fake_collection1, 'wb+').close()
    open(fake_collection2, 'wb+').close()

    collection1_manifest = json.dumps({
        'collection_info': {
            'namespace': 'namespace1',
            'name': 'collection1',
            'version': '1.2.3',
            'authors': ['Jordan Borean'],
            'readme': 'README.md',
            'dependencies': {},
        },
        'format': 1,
    })
    with open(os.path.join(collection1, 'MANIFEST.json'), 'wb') as manifest_obj:
        manifest_obj.write(to_bytes(collection1_manifest))

    mock_warning = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warning)

    actual = list(collection.find_existing_collections(test_dir, artifacts_manager=concrete_artifact_cm))

    assert len(actual) == 2
    for actual_collection in actual:
        if '%s.%s' % (actual_collection.namespace, actual_collection.name) == 'namespace1.collection1':
            assert actual_collection.namespace == 'namespace1'
            assert actual_collection.name == 'collection1'
            assert actual_collection.ver == '1.2.3'
            assert to_text(actual_collection.src) == collection1
        else:
            assert actual_collection.namespace == 'namespace2'
            assert actual_collection.name == 'collection2'
            assert actual_collection.ver == '*'
            assert to_text(actual_collection.src) == collection2

    assert mock_warning.call_count == 1
    assert mock_warning.mock_calls[0][1][0] == "Collection at '%s' does not have a MANIFEST.json file, nor has it galaxy.yml: " \
                                               "cannot detect version." % to_text(collection2)


def test_download_file(tmp_path_factory, monkeypatch):
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))

    data = b"\x00\x01\x02\x03"
    sha256_hash = sha256()
    sha256_hash.update(data)

    mock_open = MagicMock()
    mock_open.return_value = BytesIO(data)
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    expected = temp_dir
    actual = collection._download_file('http://google.com/file', temp_dir, sha256_hash.hexdigest(), True)

    assert actual.startswith(expected)
    assert os.path.isfile(actual)
    with open(actual, 'rb') as file_obj:
        assert file_obj.read() == data

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'http://google.com/file'


def test_download_file_hash_mismatch(tmp_path_factory, monkeypatch):
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections'))

    data = b"\x00\x01\x02\x03"

    mock_open = MagicMock()
    mock_open.return_value = BytesIO(data)
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    expected = "Mismatch artifact hash with downloaded file"
    with pytest.raises(AnsibleError, match=expected):
        collection._download_file('http://google.com/file', temp_dir, 'bad', True)


def test_extract_tar_file_invalid_hash(tmp_tarfile):
    temp_dir, tfile, filename, dummy = tmp_tarfile

    expected = "Checksum mismatch for '%s' inside collection at '%s'" % (to_native(filename), to_native(tfile.name))
    with pytest.raises(AnsibleError, match=expected):
        collection._extract_tar_file(tfile, filename, temp_dir, temp_dir, "fakehash")


def test_extract_tar_file_missing_member(tmp_tarfile):
    temp_dir, tfile, dummy, dummy = tmp_tarfile

    expected = "Collection tar at '%s' does not contain the expected file 'missing'." % to_native(tfile.name)
    with pytest.raises(AnsibleError, match=expected):
        collection._extract_tar_file(tfile, 'missing', temp_dir, temp_dir)


def test_extract_tar_file_missing_parent_dir(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile
    output_dir = os.path.join(temp_dir, b'output')
    output_file = os.path.join(output_dir, to_bytes(filename))

    collection._extract_tar_file(tfile, filename, output_dir, temp_dir, checksum)
    os.path.isfile(output_file)


def test_extract_tar_file_outside_dir(tmp_path_factory):
    filename = u'ÅÑŚÌβŁÈ'
    temp_dir = to_bytes(tmp_path_factory.mktemp('test-%s Collections' % to_native(filename)))
    tar_file = os.path.join(temp_dir, to_bytes('%s.tar.gz' % filename))
    data = os.urandom(8)

    tar_filename = '../%s.sh' % filename
    with tarfile.open(tar_file, 'w:gz') as tfile:
        b_io = BytesIO(data)
        tar_info = tarfile.TarInfo(tar_filename)
        tar_info.size = len(data)
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    expected = re.escape("Cannot extract tar entry '%s' as it will be placed outside the collection directory"
                         % to_native(tar_filename))
    with tarfile.open(tar_file, 'r') as tfile:
        with pytest.raises(AnsibleError, match=expected):
            collection._extract_tar_file(tfile, tar_filename, os.path.join(temp_dir, to_bytes(filename)), temp_dir)


def test_require_one_of_collections_requirements_with_both():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', 'namespace.collection', '-r', 'requirements.yml'])

    with pytest.raises(AnsibleError) as req_err:
        cli._require_one_of_collections_requirements(('namespace.collection',), 'requirements.yml')

    with pytest.raises(AnsibleError) as cli_err:
        cli.run()

    assert req_err.value.message == cli_err.value.message == 'The positional collection_name arg and --requirements-file are mutually exclusive.'


def test_require_one_of_collections_requirements_with_neither():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify'])

    with pytest.raises(AnsibleError) as req_err:
        cli._require_one_of_collections_requirements((), '')

    with pytest.raises(AnsibleError) as cli_err:
        cli.run()

    assert req_err.value.message == cli_err.value.message == 'You must specify a collection name or a requirements file.'


def test_require_one_of_collections_requirements_with_collections():
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', 'namespace1.collection1', 'namespace2.collection1:1.0.0'])
    collections = ('namespace1.collection1', 'namespace2.collection1:1.0.0',)

    requirements = cli._require_one_of_collections_requirements(collections, '')['collections']

    req_tuples = [('%s.%s' % (req.namespace, req.name), req.ver, req.src, req.type,) for req in requirements]
    assert req_tuples == [('namespace1.collection1', '*', None, 'galaxy'), ('namespace2.collection1', '1.0.0', None, 'galaxy')]


@patch('ansible.cli.galaxy.GalaxyCLI._parse_requirements_file')
def test_require_one_of_collections_requirements_with_requirements(mock_parse_requirements_file, galaxy_server):
    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'verify', '-r', 'requirements.yml', 'namespace.collection'])
    mock_parse_requirements_file.return_value = {'collections': [('namespace.collection', '1.0.5', galaxy_server)]}
    requirements = cli._require_one_of_collections_requirements((), 'requirements.yml')['collections']

    assert mock_parse_requirements_file.call_count == 1
    assert requirements == [('namespace.collection', '1.0.5', galaxy_server)]


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify', spec=True)
def test_call_GalaxyCLI(execute_verify):
    galaxy_args = ['ansible-galaxy', 'collection', 'verify', 'namespace.collection']

    GalaxyCLI(args=galaxy_args).run()

    assert execute_verify.call_count == 1


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify')
def test_call_GalaxyCLI_with_implicit_role(execute_verify):
    galaxy_args = ['ansible-galaxy', 'verify', 'namespace.implicit_role']

    with pytest.raises(SystemExit):
        GalaxyCLI(args=galaxy_args).run()

    assert not execute_verify.called


@patch('ansible.cli.galaxy.GalaxyCLI.execute_verify')
def test_call_GalaxyCLI_with_role(execute_verify):
    galaxy_args = ['ansible-galaxy', 'role', 'verify', 'namespace.role']

    with pytest.raises(SystemExit):
        GalaxyCLI(args=galaxy_args).run()

    assert not execute_verify.called


@patch('ansible.cli.galaxy.verify_collections', spec=True)
def test_execute_verify_with_defaults(mock_verify_collections):
    galaxy_args = ['ansible-galaxy', 'collection', 'verify', 'namespace.collection:1.0.4']
    GalaxyCLI(args=galaxy_args).run()

    assert mock_verify_collections.call_count == 1

    print("Call args {0}".format(mock_verify_collections.call_args[0]))
    requirements, search_paths, galaxy_apis, ignore_errors = mock_verify_collections.call_args[0]

    assert [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type) for r in requirements] == [('namespace.collection', '1.0.4', None, 'galaxy')]
    for install_path in search_paths:
        assert install_path.endswith('ansible_collections')
    assert galaxy_apis[0].api_server == 'https://galaxy.ansible.com'
    assert ignore_errors is False


@patch('ansible.cli.galaxy.verify_collections', spec=True)
def test_execute_verify(mock_verify_collections):
    GalaxyCLI(args=[
        'ansible-galaxy', 'collection', 'verify', 'namespace.collection:1.0.4', '--ignore-certs',
        '-p', '~/.ansible', '--ignore-errors', '--server', 'http://galaxy-dev.com',
    ]).run()

    assert mock_verify_collections.call_count == 1

    requirements, search_paths, galaxy_apis, ignore_errors = mock_verify_collections.call_args[0]

    assert [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type) for r in requirements] == [('namespace.collection', '1.0.4', None, 'galaxy')]
    for install_path in search_paths:
        assert install_path.endswith('ansible_collections')
    assert galaxy_apis[0].api_server == 'http://galaxy-dev.com'
    assert ignore_errors is True


def test_verify_file_hash_deleted_file(manifest_info):
    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=False)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', digest, error_queue)

            assert mock_isfile.called_once

    assert len(error_queue) == 1
    assert error_queue[0].installed is None
    assert error_queue[0].expected == digest


def test_verify_file_hash_matching_hash(manifest_info):

    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=True)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', digest, error_queue)

            assert mock_isfile.called_once

    assert error_queue == []


def test_verify_file_hash_mismatching_hash(manifest_info):

    data = to_bytes(json.dumps(manifest_info))
    digest = sha256(data).hexdigest()
    different_digest = 'not_{0}'.format(digest)

    namespace = manifest_info['collection_info']['namespace']
    name = manifest_info['collection_info']['name']
    version = manifest_info['collection_info']['version']
    server = 'http://galaxy.ansible.com'

    error_queue = []

    with patch.object(builtins, 'open', mock_open(read_data=data)) as m:
        with patch.object(collection.os.path, 'isfile', MagicMock(return_value=True)) as mock_isfile:
            collection._verify_file_hash(b'path/', 'file', different_digest, error_queue)

            assert mock_isfile.called_once

    assert len(error_queue) == 1
    assert error_queue[0].installed == digest
    assert error_queue[0].expected == different_digest


def test_consume_file(manifest):

    manifest_file, checksum = manifest
    assert checksum == collection._consume_file(manifest_file)


def test_consume_file_and_write_contents(manifest, manifest_info):

    manifest_file, checksum = manifest

    write_to = BytesIO()
    actual_hash = collection._consume_file(manifest_file, write_to)

    write_to.seek(0)
    assert to_bytes(json.dumps(manifest_info)) == write_to.read()
    assert actual_hash == checksum


def test_get_tar_file_member(tmp_tarfile):

    temp_dir, tfile, filename, checksum = tmp_tarfile

    with collection._get_tar_file_member(tfile, filename) as (tar_file_member, tar_file_obj):
        assert isinstance(tar_file_member, tarfile.TarInfo)
        assert isinstance(tar_file_obj, tarfile.ExFileObject)


def test_get_nonexistent_tar_file_member(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    file_does_not_exist = filename + 'nonexistent'

    with pytest.raises(AnsibleError) as err:
        collection._get_tar_file_member(tfile, file_does_not_exist)

    assert to_text(err.value.message) == "Collection tar at '%s' does not contain the expected file '%s'." % (to_text(tfile.name), file_does_not_exist)


def test_get_tar_file_hash(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    assert checksum == collection._get_tar_file_hash(tfile.name, filename)


def test_get_json_from_tar_file(tmp_tarfile):
    temp_dir, tfile, filename, checksum = tmp_tarfile

    assert 'MANIFEST.json' in tfile.getnames()

    data = collection._get_json_from_tar_file(tfile.name, 'MANIFEST.json')

    assert isinstance(data, dict)
