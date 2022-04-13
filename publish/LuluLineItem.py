class LuluLineItem:
    def __init__(self, student_id, pod_package_id, interior_pdf_url, cover_url):
        self.student_id = student_id
        self.pod_package_id = pod_package_id
        self.interior_pdf_url = interior_pdf_url
        self.cover_url = cover_url

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
            """ % (self.student_id, self.pod_package_id, self.interior_pdf_url, self.cover_url)

        return data
