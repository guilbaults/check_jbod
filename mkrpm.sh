#!/bin/bash
spectool -g -R check_jbod-el7.spec
rpmbuild --define "dist .el7" -ba check_jbod-el7.spec
