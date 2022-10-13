#!/usr/bin/env bash
# Source this file from collection integration tests.
#
# It simplifies several aspects of collection testing:
#
# 1) Collection tests must be executed outside of the ansible source tree.
#    Otherwise ansible-test will test the ansible source instead of the test collection.
#    The temporary directory provided by ansible-test resides within the ansible source tree.
#
# 2) Sanity test ignore files for collections must be versioned based on the ansible-core version being used.
#    This script generates an ignore file with the correct filename for the current ansible-core version.
#
# 3) Sanity tests which are multi-version require an ignore entry per Python version.
#    This script replicates these ignore entries for each supported Python version based on the ignored path.

set -eu -o pipefail

export TEST_DIR
export WORK_DIR

TEST_DIR="$PWD"
WORK_DIR="$(mktemp -d)"

trap 'rm -rf "${WORK_DIR}"' EXIT

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

"${TEST_DIR}/../collection/update-ignore.py"
