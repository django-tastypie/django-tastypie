#!/bin/bash

export TWINE_USERNAME='jenkins'
export TWINE_PASSWORD=$(credstash --table octane-keystore-production -r us-west-2 get octane.jenkins_artifactory_auth)
export TWINE_REPOSITORY_URL='https://octanelending.jfrog.io/octanelending/api/pypi/pypi'

python3 setup.py sdist
twine upload dist/*