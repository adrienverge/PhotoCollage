class Photograph:

    def __init__(self, name, faces, event_name):
        self.name = name
        self.faces = faces
        self.event_name = event_name

    def get_bounding_box_for_child(self, child_name):
        # We have to look in the faces list for this child
        # Maybe later we can use a Map instead of a List
        for face in self.faces:
            if face[0] == child_name:
                return face[2]

        return None
