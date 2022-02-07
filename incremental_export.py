import os
import sys
import tempfile
import datetime

import inkex
from inkex.command import inkscape


class IncrementalExport(inkex.OutputExtension):

    def add_arguments(self, pars):
        pars.add_argument(
            "--directory")
        pars.add_argument(
            "--out_name",
            default="project_name")
    
    def save(self,stream):

        start_time = datetime.datetime.now()

        visible_nodes = [node for node in self.svg.iter()
            if isinstance(node, inkex.elements.ShapeElement) 
            and not isinstance(node, inkex.elements.Group)]

        out_folder = os.path.join(self.options.directory, self.options.out_name)

        if not os.path.exists(self.options.directory):
            os.mkdir(self.options.directory)

        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        cache_folder = os.path.join(out_folder, "cache")

        if not os.path.exists(cache_folder):
            os.mkdir(cache_folder)

        export_text_list = []
        image_list = []
        for node in visible_nodes:
            
            node_filename_png = os.path.join(
                    cache_folder, 
                    "{}.png".format(node.attrib["id"]))
            node_filename_svg = os.path.join(
                    cache_folder, 
                    "{}.svg".format(node.attrib["id"]))

            node_export_text = "export-id:{}; export-filename:{}; export-do;".format(
                    node.attrib["id"],
                    node_filename_png)

            image_list.append("{}.png".format(node.attrib["id"]))

            current_svg = node.tostring()
            if os.path.exists(node_filename_svg):
                cached_svg = ""
                with open(node_filename_svg, "rb") as f:
                    cached_svg = f.read()

                if cached_svg == current_svg:
                    continue

            with open(node_filename_svg, "wb") as f:
                f.write(current_svg)

            export_text_list.append(node_export_text)

        full_export_text = ("export-area-page; export-id-only; " + 
            " ".join(export_text_list))

        #inkex.utils.errormsg(full_export_text)
        
        inkscape(
            self.options.input_file,
            actions = full_export_text)

        end_export_time = datetime.datetime.now()

        raster_svg_text = self.generate_raster_svg(image_list)
        raster_svg_name = "combine_cache.svg"
        raster_svg_file = os.path.join(cache_folder, raster_svg_name)
        with open(raster_svg_file, "w") as f:
            f.write(raster_svg_text)

        inkscape(
            raster_svg_file,
            actions="export-area-page; export-filename:{}; export-do".format(
                os.path.join(out_folder,"output.png")
                ))

        end_time = datetime.datetime.now()

        inkex.utils.errormsg(
            "In {} seconds exported {} objects. {} objects were already cached. {} seconds were spent linking the objects into a single output image.".format(
                (end_export_time - start_time).total_seconds(),
                len(export_text_list),
                len(visible_nodes) - len(export_text_list),
                (end_time - end_export_time).total_seconds()))

    def generate_raster_svg(self, image_files):

        width = self.svg.attrib["width"]
        height = self.svg.attrib["height"]

        namedview = self.svg.findone("sodipodi:namedview")

        return_text = ""
        return_text += "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>"

        return_text += '''
<svg 
    width="{}" 
    height="{}" 
    viewbox="{}" 
    version="{}" 
    id="{}"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:svg="http://www.w3.org/2000/svg" > '''.format(
            width,
            height,
            self.svg.attrib["viewBox"],
            self.svg.attrib["version"],
            self.svg.attrib["id"]
            )
        
        return_text += '''
    <sodipodi:namedview
        id="{}"
        pagecolor="{}"
        inkscape:pageopacity="1" /> '''.format(
            namedview.attrib["id"],
            namedview.attrib["pagecolor"]#,
            #namedview.attrib["inkscape:pageopacity"]
            )

        
        for idx, image_file in enumerate(image_files):
            return_text += '''
<image xlink:href="{}" width="{}" height="{}" id=""/>'''.format(
            image_file,
            width,
            height)
        
        return_text += "</svg>"

        return return_text


if __name__ == "__main__":
    IncrementalExport().run()

