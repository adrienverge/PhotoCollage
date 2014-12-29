# -*- coding: utf-8 -*-
"""
Copyright (C) 2014 Adrien Vergé

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import base64

from gi.repository import GdkPixbuf


# Generated with:
#   import base64
#   with open("data/icons/scale-verti.png", "rb") as f:
#       encoded_image = base64.b64encode(f.read())
#   n = 79 - 4 - 2
#   for i in range(0, len(encoded_image), n):
#       print('    "' + encoded_image[i:i+n] + '"')
ICON_EXPAND_HORIZONTALLY = (
    "iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAABmJLR0QAAAAAAAD5Q7t/AAAAC"
    "XBIWXMAAA3XAAAN1wFCKJt4AAAAB3RJTUUH3gwdEgITKknh/gAAAplJREFUOMvtlc1LVFEYxn"
    "/nzr3dWfS5nEyCImdXYZBZElJQBNWqTdCuLIloSooh1xGJFQntEitaWCRhtSikKBJcBGlalla"
    "mgY4XRsgGyTkf3tPCmT50NP+AntXlfc/93cM5z/tc+K+cxMzCq9cdT6WUO6VSKKlQSqJyz1Ip"
    "lFJMZCZkSHgoeaa2ZeHgzg67aUMZjuPMuZvWB/cZ+PIZL+IdTCRq7hRa484sOI6D4zg8aXuMM"
    "RobWjzPQ0qJ7/u4rkdqNEUYhmR+ZJobGq5QCD5rW46YLmmlCIKAdDpNEASMjIwwODRIEAR0dX"
    "VRsX0by1YsR0/p5rq6CwfmA68GBko3bAbAWgsWrJ1uep7H2Fia9FiaaDRKU+MNspNZ+j70k0z"
    "W3gMuFAIXAc+ANVu3lf9qhjbEWktoLX7Ux3Ecxse/sWpVEWVlWyhZV0LVkWP5+zgHnM+/GwFW"
    "Ai+BtUBHS+vd4qJYMf0f+8hkMtjcDQshMMYg5bRLtNYIIdi3dz8Dg5/o6X6rgUpgKdAmgG5g/"
    "VwOiMfjnK5J4Lou2ewkl+qvMDT09V82rnWBRfOtmJoyGGOwWCKuS5g/9Pm1QgAx4DkQBzrbO5"
    "6XVpRX8vBRK8PDwyilEEIQiTgIIRgf/45UWVzXxfd9kmdrqTp6mMbrTVkgClwFTjvAKLAD6Ad"
    "KTxxPzPq8MQatNUprIu7f1u/t7eXWzdvkoNeAmj9dkcrBu7vf9MwCh2GI1hqt9axee3s7xhiA"
    "BuAkYGf6OAVs7HnfWfiswxCtFcbov8a9urqa+ssXAU7loQVHOi/f94nFYkglUTmLyXwgKQXA4"
    "sVLfsXAP7MiP3W7d+1ZUDxaaxcGFkK8eNf3pnLaalO56PwdmYWi1Pf9Z///QHPqJ9gGSPFS3b"
    "SHAAAAAElFTkSuQmCC")
ICON_EXPAND_VERTICALLY = (
    "iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAABmJLR0QAAAAAAAD5Q7t/AAAAC"
    "XBIWXMAAA3XAAAN1wFCKJt4AAAAB3RJTUUH3gwdEgI3FkoFLwAAAmNJREFUOMutlb9PU1EUxz"
    "/33ldI+BUMxSAODhLcVEZ1N7o7aBQlBGZ/xMS4G5IqVFCSRuKf4GB0MBoSBgOxCBUQiwOQyAC"
    "7lrb3tu9dh74HLbalkX6Tkzu8ez/n5HtyzoPadAJYA5aBbuqkbuAnYP1YB07WG1oMP3UU8JIP"
    "WiyCzvrnRs2U72vfZlaSCRsEYM+dP2s/z83sVRtfnLUXL12wgE0sz9uFpS92PjFn5xfnpiuCV"
    "5IJ63meLacAXE6u6wbJ9+QchAsh+PjpA1rrssnfvX9bcjfU0MCVy1fRxlAR7LouAOl0mp2dnb"
    "Lg7e1tpJJIIUFAV1cXAEZXAQcftdGYAxX09JxGKQchJVIohBAIAdYrOGCMrgL2YUZrcrkcAFJ"
    "KHMfh3v27OI6DktKvWAAQCoVK3pYFBz4ZY8i7+QJEKpSSKEcVwEohlURnC8mDXlS3wuxb4Xku"
    "SikQAuFXl81m0MaQyaTxPI9wuJPGxsaSoqp6bIzBWvA8i9aG9G6aqanXSCG4PdAPQHv7MVpb2"
    "nCcGqwIGmCMIZ/PlTRk69cWANZ6NDc3s7m5QTL5g76+PlKpP6R+p0q6J8tZUdy0IAI1NTXR0R"
    "Emm80wODTA7m6Kjc11PLxbh1rR0tJacTo7O48T7gjT23uGha8JdFbT1tp24+GDR28qPopNTZa"
    "MdCwWs6urq/+MdDwet0PDg3Y0GrETE9Hrhy6h2KvJ6fEXYzY6/syORiNWCGFDoZAdGh7cA/ff"
    "uWmllBawkcjItf9dm+M+MFO0No1/jhxlHwvgZZlF/6QevyYBPC+CjlFnPQUe13r5L89KdsJXA"
    "Wy7AAAAAElFTkSuQmCC")


def load_pixbuf(encoded):
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(base64.b64decode(encoded))
    loader.close()
    return loader.get_pixbuf()
