# google_storage_bucket

## Synopsis

* Manages the state of Google Cloud Storage Buckets

## Parameters

```yaml
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
```

## Requirements

The below requirements are needed on the host that executes this module.

* "google-cloud-storage >= 1.31.0"

## Examples

* Ensure my-project-bucket exists in my-project

```yaml
- name: Create my-project-bucket
  google_storage_bucket:
    name: "my-project-bucket"
    project: "my-project"
    storage_class: "NEARLINE"
    location: "us-central1"
    state: present
```

* Ensure my-project-bucket does not exist

```yaml
- name: Delete my-project-bucket
  google_storage_bucket:
    name: "my-project-bucket"
    state: absent
```

## Return Values

```yaml
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
```

## Authors

* Michael Shen (@mjlshen)
