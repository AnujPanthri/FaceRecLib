import xml.etree.ElementTree as ET
import numpy as np
import cv2


def show_pred_image(tree, img):
  root = tree.getroot()

  size = root.find('size')
  w, h = int(size.find("width").text), int(size.find("height").text)
  default_color = [220, 255, 0]
  random_color = np.random.randn(3) * 255

  for obj in root.findall("object"):
    bndbox = obj.find("bndbox")
    classname = obj.find('name').text

    xmin, ymin, xmax, ymax = int(bndbox.find('xmin').text), int(
        bndbox.find('ymin').text), int(bndbox.find('xmax').text), int(
            bndbox.find('ymax').text)

    if obj.find("distance") is None:
      color = default_color
    else:
      color = random_color
      distance = obj.find("distance").text
      classname += f"({distance})"

    img = cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 7)
    img = cv2.putText(img,
                      classname, (xmin, ymin),
                      cv2.FONT_HERSHEY_SIMPLEX,
                      2,
                      color,
                      thickness=5)
  return img


def xml_to_objs_found(tree):
  root = tree.getroot()

  size = root.find('size')
  image_w, image_h = int(size.find("width").text), int(size.find("height").text)

  objs_found = []
  for obj in root.findall("object"):
    obj_found = dict()
    bndbox = obj.find("bndbox")
    classname = obj.find('name').text
    distance = float(obj.find('distance').text) if classname != "face" else None

    xmin, ymin, xmax, ymax = int(bndbox.find('xmin').text), int(
        bndbox.find('ymin').text), int(bndbox.find('xmax').text), int(
            bndbox.find('ymax').text)

    x, y = xmin / image_w, ymin / image_h
    w, h = (xmax - xmin) / image_w, (ymax - ymin) / image_h

    obj_details = {
        'xywh': [x, y, w, h],
        'class': classname,
        'distance': distance
    }
    objs_found.append(obj_details)

  return objs_found


def objs_found_to_xml(test_img, w, h, objs_found):

  def rescale(obj_found, w, h):
    # xywh
    obj_found[0] *= w
    obj_found[1] *= h
    obj_found[2] *= w
    obj_found[3] *= h
    return obj_found

  root = ET.Element("annotation")

  filename_tag = ET.Element("filename")
  filename_tag.text = test_img
  root.append(filename_tag)
  path_tag = ET.Element("path")
  path_tag.text = "./" + test_img
  root.append(path_tag)

  size_tag = ET.Element("size")
  # w,h defined above
  # print(w,h)
  width_tag = ET.Element("width")
  width_tag.text = str(w)
  height_tag = ET.Element("height")
  height_tag.text = str(h)
  depth_tag = ET.Element("depth")
  depth_tag.text = "3"

  size_tag.append(width_tag)
  size_tag.append(height_tag)
  size_tag.append(depth_tag)
  root.append(size_tag)

  # add all objects
  for obj_found in objs_found:
    obj_found[2:] = rescale(obj_found[2:], w, h)

    obj_tag = ET.Element("object")
    name_tag = ET.Element("name")
    name_tag.text = obj_found[1]
    obj_tag.append(name_tag)

    bndbox_tag = ET.Element("bndbox")
    xmin_tag = ET.Element("xmin")
    xmin_tag.text = str(int(obj_found[2]))
    ymin_tag = ET.Element("ymin")
    ymin_tag.text = str(int(obj_found[3]))
    xmax_tag = ET.Element("xmax")
    xmax_tag.text = str(int(obj_found[2] + obj_found[4]))
    ymax_tag = ET.Element("ymax")
    ymax_tag.text = str(int(obj_found[3] + obj_found[5]))

    bndbox_tag.append(xmin_tag)
    bndbox_tag.append(ymin_tag)
    bndbox_tag.append(xmax_tag)
    bndbox_tag.append(ymax_tag)

    obj_tag.append(bndbox_tag)
    root.append(obj_tag)

  xml = ET.ElementTree(root)

  # with open(xml_file_path,"wb") as f:
  #     xml.write(f)

  return xml
