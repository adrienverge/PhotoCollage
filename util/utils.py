from PIL import Image


def extract_image_date(img_path):
    im = Image.open(img_path)
    exif = im.getexif()
    try:
        creation_time = exif.get(36867)
    except:
        creation_time = "NA"

    return creation_time


def get_rectangle_from_points(list_of_points):
    # Given a list of points like this,
    # [[0.125, 95.375], [249.125, 95.375], [249.125, 269.375], [0.125, 269.375]]
    # the task is to find the min_x, min_y, max_x, max_y
    min_x, max_x = min(list_of_points)[0], max(list_of_points)[0]
    min_y, max_y = min(list_of_points)[1], max(list_of_points)[1]

    return [min_x, min_y, max_x, max_y]


# left=938.17993, top=651.6867, right=1033.7305, bottom=777.4458
def get_box_from_points_arr(arr_of_points):
    left = float(arr_of_points[0])
    top = float(arr_of_points[1])
    right = float(arr_of_points[2])
    bottom = float(arr_of_points[3])

    return [[left, top], [right, top], [left, bottom], [right, bottom]]


def get_box_from_points(left, top, right, bottom):
    return [[left, top], [right, top], [left, bottom], [right, bottom]]


def get_center_coods_of_rectangle(rectangle_points: [float, float, float, float]):
    _width = rectangle_points[2] - rectangle_points[0]
    _height = rectangle_points[3] - rectangle_points[1]

    center_x = rectangle_points[0] + _width / 2
    center_y = rectangle_points[1] + _height / 2

    return center_x, center_y
