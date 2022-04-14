import unittest
import json

from publish.LuluLineItem import LuluLineItem
from publish.lulu import get_access_token_json, client_id_sandbox, client_secret_sandbox, \
    get_job_details, get_line_items, create_order_payload, submit_full_order


class LuluIntegrationTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(LuluIntegrationTests, self).__init__(*args, **kwargs)

    def test_line_item(self):
        cover_url = "https://drive.google.com/file/d/1Y3y1GlcY4n120ERg_PU0ISNbiTnK1Rn9/view?usp=sharing"
        interior_url = "https://drive.google.com/file/d/1GpzDaNbea-aZcHFMzb-HvzP8isxIfYr5/view?usp=sharing"
        first_item = LuluLineItem("1", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)

        json_item_str = first_item.get_lulu_line_item()
        assert ("0827X1169FCPRELW060UW444MNG" == json.loads(json_item_str)["pod_package_id"])

    def test_get_line_items(self):
        cover_url = "https://drive.google.com/file/d/1Y3y1GlcY4n120ERg_PU0ISNbiTnK1Rn9/view?usp=sharing"
        interior_url = "https://drive.google.com/file/d/1GpzDaNbea-aZcHFMzb-HvzP8isxIfYr5/view?usp=sharing"
        first_item = LuluLineItem("1", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)
        second_item = LuluLineItem("2", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)

        order_items = [first_item, second_item]

        json_items_str = get_line_items(order_items)
        print(json_items_str)

    def test_get_print_job_all(self):
        cover_url = "https://drive.google.com/file/d/1Y3y1GlcY4n120ERg_PU0ISNbiTnK1Rn9/view?usp=sharing"
        interior_url = "https://drive.google.com/file/d/1GpzDaNbea-aZcHFMzb-HvzP8isxIfYr5/view?usp=sharing"
        first_item = LuluLineItem("1", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)
        second_item = LuluLineItem("2", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)

        order_items = [first_item, second_item]

        json_str = create_order_payload(order_items)
        valid_json = json.loads(json_str)

    def test_create_all_print_jobs(self):
        cover_url = "https://drive.google.com/file/d/1UCdNESiQvd4J-97rAtx5BbssY0EVF4iK/view?usp=sharing"
        interior_url = "https://drive.google.com/file/d/18vfC1xcQDUb3EJVTRVrksemsLYfrdwKM/view?usp=sharing"
        first_item = LuluLineItem("1", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)
        second_item = LuluLineItem("2", "0827X1169FCPRELW060UW444MNG", interior_url, cover_url)

        order_items = [first_item, second_item]
        response = submit_full_order(order_items)

        print(response.text)

    def test_get_access_token(self):
        access_token = get_access_token_json(client_id_sandbox, client_secret_sandbox)
        assert (access_token['expires_in'] == 3600)

    def test_get_job_details(self):
        created_job_id = self.test_create_print_job()
        self.test_job_details(created_job_id)

    def test_job_details(self, id):
        get_job_details(id)

    def test_job_details_for(self):
        get_job_details("56197")
