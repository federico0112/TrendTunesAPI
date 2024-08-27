#!/usr/bin/env python
import json

# serverless database query - postgresql example

# Copyright 2016 Amazon.com, Inc. or its affiliates.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#    http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file.
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.

from common import query_handler


def handler(event, context):
    my_handler = query_handler.QueryHandler(query_handler.QueryTypes.GET_TOP_TAGS)
    return my_handler.execute()


if __name__ == "__main__":
    handler(None, None)
