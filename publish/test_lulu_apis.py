import unittest
import json

from publish.lulu import get_access_token_json, client_id_sandbox, client_secret_sandbox, create_print_job, \
    get_job_details


class LuluIntegrationTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(LuluIntegrationTests, self).__init__(*args, **kwargs)

    def test_get_access_token(self):
        access_token = get_access_token_json(client_id_sandbox, client_secret_sandbox)
        assert(access_token['expires_in'] == 3600)

    def test_create_print_job(self):
        student_id = "Anuj"
        print_job_details = create_print_job(student_id)
        print(json.loads(print_job_details.text)['id'])
        return json.loads(print_job_details.text)['id']

    def test_get_job_details(self):
        created_job_id = self.test_create_print_job()
        get_job_details(created_job_id)