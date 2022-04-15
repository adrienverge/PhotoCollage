class OrderDetails:
    def __init__(self, wix_order_id: str, cover_format: str):
        self.wix_order_id = wix_order_id
        self.cover_format = cover_format
        self.interior_pdf_url = None
        self.cover_url = None
        self.lulu_job_id: str = None
        self.pod_package_id = None

    def get_lulu_line_item(self):
        data = """{
                                "title": "%s",
                                "pod_package_id": "%s",
                                "quantity": 1,
                                "interior": {
                                    "source_url": "%s"
                                },
                                "cover": {
                                    "source_url": "%s"
                                }
                            }
            """ % (self.wix_order_id, self.pod_package_id, self.interior_pdf_url, self.cover_url)

        return data
