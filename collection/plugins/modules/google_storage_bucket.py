#!/usr/bin/python

# Copyright: (c) 2020, Michael Shen <mishen@umich.edu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
'''

from ansible.module_utils.basic import AnsibleModule
from google.cloud import storage
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import Conflict

# returns:
#   True/False changed
#   error message
#   result
def bucketPresent(params, check=False):
    result = getBucket(params)
    if result['state'] == 'present':
        if check:
            return False, '', result
        else:
            if params['storage_class'] != result['storage_class']:
                return updateBucket(params, result)
            else:
                return False, '', result
    else:
        if check:
            result = {
                "name": params['name'],
                "state": params['state'],
                "storage_class": params['storage_class'],
                "location": params['location']
            }
            return True, '', result
        else:
            return createBucket(params, result)

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
                "location": params['location']
            }
            return True, '', result
        else:
            return deleteBucket(params, result)

# getBucket checks to see if a given bucket exists or not, filling in the
# result dictionary with as much relevant information as it can find.
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
        result['location'] = bucket.location
    except NotFound:
        result['state'] = 'absent'
    return result

def createBucket(params, result):
    if not 'project' in params:
        return False, "project not defined, required when creating buckets", result

    storage_client = storage.Client(project=params['project'])

    try:
        bucket = storage_client.bucket(params['name'])
        bucket.storage_class = params['storage_class']
        bucket.create(location=params['location'])
        result['state'] = 'present'
        result['storage_class'] = bucket.storage_class
        result['location'] = bucket.location
    except Conflict:
        return False, "Naming conflict: Bucket %s exists elsewhere." % params['name'], result
    return True, '', result

def updateBucketStorageClass(params, result):
    if not 'project' in params:
        return False, "project not defined, required when creating buckets", result

    storage_client = storage.Client(project=params['project'])

    bucket = storage_client.bucket(params['name'])
    if bucket.storage_class != params['storage_class']:
        bucket.storage_class = params['storage_class']
        bucket.update()
        result['storage_class'] = bucket.storage_class
        return True, '', result
    else:
        return False, '', result

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
