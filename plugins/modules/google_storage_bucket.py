#!/usr/bin/python

# Copyright: (c) 2020, Michael Shen <mishen@umich.edu>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: google_storage_bucket

short_description: "Manages the state of Google Cloud Storage Buckets."

version_added: "2.9"

description:
    - "The Buckets resource represents a bucket in Google Cloud Storage."
    - "For more information see https://cloud.google.com/storage/docs/json_api/v1/buckets"

options:
    name:
        description:
            - The name of the bucket, must be unique within all of GCP.
            - When you create a bucket, you permanently define its name, its geographic location, and the project it is part of.
        required: true
    project:
        description:
            - The name of the project to manage the Google storage bucket.
            - When you create a bucket, you permanently define its name, its geographic location, and the project it is part of.
    state:
        description:
            - The state of the object in GCP
        choices:
            - present
            - absent
        default: present
        type: str
        required: false
    storage_class:
        description:
            - Sets the default storage class of the bucket. For more information see: https://cloud.google.com/storage/docs/storage-classes
        choices:
            - STANDARD
            - NEARLINE
            - COLDLINE
            - ARCHIVE
        default: STANDARD
        type: str
        required: false
    location:
        description:
            - The location of the bucket. If not passed, the default location, US, will be used. See https://cloud.google.com/storage/docs/bucket-locations
            - When you create a bucket, you permanently define its name, its geographic location, and the project it is part of.
        default: us
        type: str
        required: false
    versioning_enabled:
        description:
            - Object Versioning retains a noncurrent object version when the live object version gets replaced or deleted.
            - See https://cloud.google.com/storage/docs/object-versioning for official documentation.
        default: false
        type: bool
        required: false
    force:
        description:
            - When true, destroy a bucket even if there are objects in it.
            - When false, destroying a bucket will cause the module to fail.
        choices:
            - true
            - false
        default: false
        type: bool
        required: false

requirements:
    - "google-cloud-storage >= 1.31.0"
author:
    - Michael Shen (@mjlshen)
'''

EXAMPLES = '''
# Ensure my-project-bucket exists in my-project
- name: Create my-project-bucket
  google_storage_bucket:
    name: "my-project-bucket"
    project: "my-project"
    storage_class: "NEARLINE"
    location: "us-central1"
    state: present

# Ensure my-project-bucket does not exist
- name: Delete my-project-bucket
  google_storage_bucket:
    name: "my-project-bucket"
    state: absent
'''

RETURN = '''
changed:
    description: True if action was taken to create or destroy a bucket.
    type: bool
    returned: always
name:
    description: The name of the bucket.
    type: str
    returned: always
state:
    description: The state of the bucket, present or absent.
    type: str
    returned: always
storage_class:
    description: The default storage class of the bucket.
    type: str
    returned: always
location:
    description: The geographic location of the bucket.
    type: str
    returned: always
versioning_enabled:
    description: Object Versioning retains a noncurrent object version when the live object version gets replaced or deleted. https://cloud.google.com/storage/docs/object-versioning
    type: bool
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from google.cloud import storage
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import Conflict


# If state: present, this function will be called, returning:
# 1) True if the state of the bucket has changed, else False
# 2) Any error message, if present
# 3) The resulting parameters of the bucket
def bucketPresent(params, check=False):
    result = getBucket(params)
    if result['state'] == 'present':
        if check:
            return (params['storage_class'] != result['storage_class']) and (params['versioning_enabled'] != result['versioning_enabled']), '', result
        else:
            if (result['storage_class'] == params['storage_class'] and result['versioning_enabled'] == params['versioning_enabled']):
                return False, '', result
            else:
                return updateBucket(params, result)
    else:
        if check:
            result = {
                "name": params['name'],
                "state": params['state'],
                "storage_class": params['storage_class'],
                "location": params['location'],
                "versioning_enabled": params['versioning_enabled']
            }
            return True, '', result
        else:
            return createBucket(params, result)


# If state: absent, this function will be called, returning:
# 1) True if the state of the bucket has changed, else False
# 2) Any error message, if present
# 3) The resulting parameters of the bucket
def bucketAbsent(params, check=False):
    result = getBucket(params)
    if result['state'] == 'absent':
        if check:
            return False, '', result
        else:
            return False, '', result
    else:
        if check:
            result = {
                "name": params['name'],
                "state": params['state'],
                "storage_class": params['storage_class'],
                "location": params['location'],
                "versioning_enabled": params['versioning_enabled']
            }
            return True, '', result
        else:
            return deleteBucket(params, result)


def getBucket(params):
    result = {
        "name": '',
        "state": '',
        "storage_class": '',
        "location": ''
    }

    storage_client = storage.Client()
    result['name'] = params['name']
    try:
        bucket = storage_client.get_bucket(params['name'])
        result['state'] = 'present'
        result['storage_class'] = bucket.storage_class
        result['versioning_enabled'] = bucket.versioning_enabled
        result['location'] = bucket.location
    except NotFound:
        result['state'] = 'absent'
    return result


def createBucket(params, result):
    if 'project' not in params:
        return False, "project not defined, required when creating buckets", result

    storage_client = storage.Client(project=params['project'])

    try:
        bucket = storage_client.bucket(params['name'])
        bucket.storage_class = params['storage_class']
        bucket.versioning_enabled = params['versioning_enabled']
        bucket.create(location=params['location'])
        result['state'] = 'present'
        result['storage_class'] = bucket.storage_class
        result['location'] = bucket.location
    except Conflict:
        return False, "Naming conflict: Bucket %s exists elsewhere." % params['name'], result
    return True, '', result


def updateBucket(params, result):
    if 'project' not in params:
        return False, "project not defined, required when creating buckets", result

    storage_client = storage.Client(project=params['project'])

    bucket = storage_client.bucket(params['name'])
    if (bucket.storage_class == params['storage_class'] and bucket.versioning_enabled == params['versioning_enabled']):
        return False, '', result
    if bucket.storage_class != params['storage_class']:
        bucket.storage_class = params['storage_class']
        bucket.update()
    if bucket.versioning_enabled != params['versioning_enabled']:
        bucket.versioning_enabled = params['versioning_enabled']
        bucket.patch()

    result['storage_class'] = bucket.storage_class
    result['versioning_enabled'] = bucket.versioning_enabled
    return True, '', result


def deleteBucket(params, result):
    storage_client = storage.Client()
    try:
        bucket = storage_client.get_bucket(params['name'])
        if params['force']:
            bucket.delete(force=True)
            result['state'] = 'absent'
        else:
            try:
                bucket.delete()
                result['state'] = 'absent'
            except Conflict:
                result['state'] = 'present'
                return False, "Object conflict: Bucket %s is not empty. Use force: true to override" % params['name'], result
    except NotFound:
        result['state'] = 'absent'
        return False, '', result
    return True, '', result


def run_module():
    argument_spec = {
        "name": {
            "required": True,
            "type": 'str',
            "default": None
        },
        "project": {
            "required": False,
            "type": 'str',
            "default": None
        },
        "state": {
            "required": False,
            "choices": ['present', 'absent'],
            "type": 'str',
            "default": 'present'
        },
        "storage_class": {
            "required": False,
            "choices": ['STANDARD', 'NEARLINE', 'COLDLINE', 'ARCHIVE'],
            "type": 'str',
            "default": 'STANDARD'
        },
        "location": {
            "required": False,
            "type": 'str',
            "default": 'us'
        },
        "versioning_enabled": {
            "required": False,
            "type": 'bool',
            "default": False
        },
        "force": {
            "required": False,
            "type": 'bool',
            "default": False
        }
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    stateMachine = {
        "present": bucketPresent,
        "absent": bucketAbsent
    }

    changedState, errorMessage, result = stateMachine[module.params['state']](module.params, module.check_mode)
    if errorMessage != '':
        module.fail_json(msg=errorMessage, **result)
    else:
        module.exit_json(changed=changedState, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
