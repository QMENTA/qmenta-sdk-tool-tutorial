
import logging
import os
import ants

from qmenta.sdk.tool_maker.outputs import (
    Coloring,
    HtmlInject,
    OrientationLayout,
    PapayaViewer,
    Region,
    ResultsConfiguration,
    Split,
    Tab,
)
from qmenta.sdk.tool_maker.modalities import Modality
from qmenta.sdk.tool_maker.tool_maker import InputFile, Tool, FilterFile

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image with Caption</title>
</head>
<body>
{body}
</body>
</html>
"""

BODY_TEMPLATE ="""
<h1>{header}</h1>
<figure>
    <img src={src_image} alt={image_description} style="max-width: 400px;">
    <figcaption>{image_caption}</figcaption>
</figure>
"""


class QmentaSDKToolMakerTutorial(Tool):
    def tool_inputs(self):
        """
        Define the inputs for the tool. This is used to create the settings.json file.
        More information on the inputs can be found here:
        https://docs.qmenta.com/sdk/guides_docs/settings.html
        """
        # Displays a text box in blue color with the information specified.
        self.add_info(
            "Required inputs:<br><b>&bull; Anatomical brain medical image</b>: 3D image to analyze<br>&ensp;" \
        )
        # Add the file selection method:
        self.add_input_container(
            title="Oncology medical image",
            info="Accepted modalities: 'T1', 'T2', 'CT', 'SCALAR'<br>",
            anchor=1,
            batch=1,
            container_id="input_images",
            mandatory=1,
            file_list=[
                InputFile(
                    file_filter_condition_name="c_image1",
                    filter_file=FilterFile(
                        modality=[Modality.T1, Modality.SCALAR],
                    ),
                    mandatory=1,
                    min_files=1,
                    max_files=1,
                ),
                InputFile(
                    file_filter_condition_name="c_image2",
                    filter_file=FilterFile(
                        modality=[Modality.CT, Modality.T2],
                    ),
                    mandatory=1,
                    min_files=1,
                    max_files=1,
                ),
            ],
        )
        self.add_input_container(
            title="Labels mask",
            info="<b>&bull;Labels mask</b>: Mask containing one or more labels.<br>&ensp;Accepted tags: 'mask','labels'",
            anchor=1,
            batch=1,
            container_id="input_labels",
            mandatory=1,
            file_list=[
                InputFile(
                    file_filter_condition_name="c_labels",
                    filter_file=FilterFile(
                        tags=[["labels"], ["mask"]],
                    ),
                    mandatory=1,
                    min_files=1,
                    max_files=1,
                ),
            ],
        )

        # Displays an horizontal line
        self.add_line()

        # Displays a header text
        self.add_heading("ANTs tool can perform the following steps")

        self.add_input_multiple_choice(
            id_="perform_steps",
            options=[
                ["do_biasfieldcorrection", "Perform Bias Field Correction"],
                ["do_segmentation", "Perform tissue segmentation"],
                ["do_thickness", "Perform cortical thickness"],
            ], 
            default=["do_biasfieldcorrection", "do_segmentation"],
            title="Which steps do you want to execute?",
        )
         # Displays an horizontal line
        self.add_line()

        self.add_input_string(
            id_="mrf", 
            default="[0.2, 1x1x1]", 
            title="'mrf' parameters as a string, usually \"[smoothingFactor,radius]\" " \
            "where smoothingFactor determines the amount of smoothing and radius determines " \
            "the MRF neighborhood, as an ANTs style neighborhood vector eg \"1x1x1\" for a 3D image.", 
        )

    def run(self, context):
        """
        This is the main function that is called when the tool is run.
        """
        # ================ #
        # GETTING THINGS READY
        logger = logging.getLogger("main")
        logger.info("Tool starting")
        # Define directories for the input and output files inside the container
        output_dir = os.path.join(os.environ.get("WORKDIR", "/root"), "OUTPUT")
        os.makedirs(output_dir, exist_ok=True)

        os.chdir(output_dir)
        context.set_progress(value=0, message="Processing")  # Set progress status so it is displayed in the platform

        # Downloads all the files and populate the variable self.inputs with the handlers and parameters
        context.set_progress(message="Downloading input data and setting self.inputs object")
        self.prepare_inputs(context, logger)

        fname1_handler = self.inputs.input_images.c_image1[0]
        fname1 = fname1_handler.file_path
        img = ants.image_read(fname1)
        logger.info(img)

        logger.info("Operations:\n"
            f"- Median: {img.median()}\n"
            f"- STD: {img.std()}\n"
            f"- Arg. Min: {img.argmin()}\n"
            f"- Arg. Max: {img.argmax()}\n"
            f"- Flatten: {img.flatten()[:10]}\n"
            f"- Non-zero: {img.nonzero()[:10]}\n"
            f"- Unique: {img.unique()[:10]}\n"
        )

        labels = self.inputs.input_labels.c_labels[0].file_path
        img2 = ants.image_read(labels)
        logger.info(img2)

        # do any operations directly on ANTsImage types
        try:
            _ = img2 - img
            _ = img2 > img
            _ = img2 / img
            _ = img2 == img
            # test if two images are allclose in values
            issame = ants.allclose(img, img2)
            logger.info(f"two images are allclose in values? : {issame}")
            # test if two images have same physical space
            issame_phys = ants.image_physical_space_consistency(img, img2)
            logger.info(f"two images have same physical space : {issame_phys}")
        except ValueError as err:
            logger.error(f"Operations between images could not be performed\n{str(err)}")

        # change any physical properties
        img4 = img.clone()
        logger.info(f"Before: {img4.spacing}")
        img4.set_spacing((2,2,2))
        logger.info(f"After: {img4.spacing}")

        context.upload_file(
            source_file_path=fname1, 
            destination_path="input_image.nii.gz",
            modality=fname1_handler.get_file_modality(),
            tags=fname1_handler.get_file_tags(),
        )
        png_image = "original.png"

        ants.plot(fname1, filename=png_image)
        context.upload_file(
            png_image, 
            png_image,
        )

        body_content = ""
        logger.info(f"Performing steps: {"\n".join(self.inputs.perform_steps)}")

        if "do_biasfieldcorrection" in self.inputs.perform_steps:
            image = ants.image_read(fname1)
            image_n4 = ants.n4_bias_field_correction(image)
            # save to filename
            image_n4.to_filename("n4_processed.nii.gz")

            context.upload_file(
                "n4_processed.nii.gz", 
                "n4_processed.nii.gz"
            )
            
            png_image = "n4_bias.png"
            ants.plot(image_n4, filename=png_image)
            context.upload_file(png_image, png_image)
            body_content += BODY_TEMPLATE.format(
                header="N4 Bias Field Correction",
                src_image=png_image,
                image_description=f"Output of the n4 bias field correction for {os.path.basename(fname1)}",
                image_caption=f"Output of the n4 bias field correction for {os.path.basename(fname1)}",
            )

        if "do_segmentation" in self.inputs.perform_steps:
            img = ants.image_read(fname1)
            img = ants.resample_image(img, (64, 64, 64), 1, 0)
            mask = ants.get_mask(img)
            img_seg = ants.atropos(
                a=img, m=self.inputs.mrf, c='[2,0]', i='kmeans[3]', x=mask
            )
            # save to filename
            img_seg["segmentation"].to_filename("atropos_processed.nii.gz")

            logger.info(f"segmentation file keys from atropos : {img_seg.keys()}")
            context.upload_file(
                "atropos_processed.nii.gz", 
                "atropos_processed.nii.gz"
            )

            png_image = "segmentation.png"
            ants.plot(img_seg['segmentation'], filename=png_image)
            context.upload_file(png_image, png_image)
            body_content += BODY_TEMPLATE.format(
                header="Tissue segmentation",
                src_image=png_image,
                image_description=f"Output of ANTs Atropos for {os.path.basename(fname1)}",
                image_caption=f"Output of ANTs Atropos for {os.path.basename(fname1)}",
            )

        if "do_thickness" in self.inputs.perform_steps:
            img = ants.image_read(fname1)
            mask = ants.get_mask(img).threshold_image(1, 2)
            segs=ants.atropos( a = img, m = self.inputs.mrf, c = '[2,0]',  i = 'kmeans[3]', x = mask )
            thickimg = ants.kelly_kapowski(
                s=segs['segmentation'], 
                g=segs['probabilityimages'][1],
                w=segs['probabilityimages'][2], 
                its=45, r=0.5, m=1
            )
            logger.info(f"thickness image : {thickimg}")
            thickimg.to_filename("thickness_processed.nii.gz")
            context.upload_file(
                "thickness_processed.nii.gz",
                "thickness_processed.nii.gz"
            )

            png_image = "thickness.png"
            img.plot(overlay=thickimg, overlay_cmap='jet', filename=png_image)
            context.upload_file(png_image, png_image)
            body_content += BODY_TEMPLATE.format(
                header="Cortical thickness",
                src_image=png_image,
                image_description=f"Output of ANTs Kelly Kapowski for {os.path.basename(fname1)}",
                image_caption=f"Output of ANTs Kelly Kapowski for {os.path.basename(fname1)}",
            )
        if body_content:
            report_output = "online_report.html"
            with open(report_output, "w") as f1:
                f1.write(HTML_TEMPLATE.format(body=body_content))
            context.upload_file(report_output, report_output)

    def tool_outputs(self):
        # Main object to create the results configuration object.
        result_conf = ResultsConfiguration()

        # Add the tools to visualize files using the function add_visualization

        # Online 3D volume viewer: visualize DICOM or NIfTI files.
        papaya_1 = PapayaViewer(title="Tissue segmentation over T1", width="50%", region=Region.center)
        # the first viewer's region is defined as center

        # Add as many layers as you want, they are going to be loaded in the order that you add them.
        papaya_1.add_file(file="input_image.nii.gz", coloring=Coloring.grayscale)  # using the file name
        papaya_1.add_file(file="atropos_processed.nii.gz", coloring=Coloring.custom)
        # Add the papaya element as a visualization in the results configuration object.
        result_conf.add_visualization(new_element=papaya_1)

        papaya_2 = PapayaViewer(title="Labels segmentation over T1", width="50%", region=Region.right)
        # the second viewer's region is defined as right, this depends on the Split(), which has the element
        # orientation set to vertical. If it is set to horizontal, then you can choose between 'top' or 'bottom'.

        # You can use modality or tag of the output file to select the file to be shown in the viewer.
        papaya_2.add_file(file="input_image.nii.gz", coloring=Coloring.grayscale)  # using the file modality
        papaya_2.add_file(file="thickness_processed.nii.gz", coloring=Coloring.custom_random)  # using file tag
        result_conf.add_visualization(new_element=papaya_2)

        # To create a split, specify which ones are the objects to be shown in the split
        split_1 = Split(
            orientation=OrientationLayout.vertical, children=[papaya_1, papaya_2], button_label="Images"
        )
        # The button label is defined because this element goes into a Tab element. The tab's "button_label" property
        # is a label that will appear to select between different viewer elements in the platform.

        html_online = HtmlInject(width="100%", region=Region.center, button_label="Report")
        html_online.add_html(file="online_report.html")
        result_conf.add_visualization(new_element=html_online)

        # Remember to add the button_label in the child objects of the tab.
        tab_1 = Tab(children=[split_1, html_online])
        # Call the function generate_results_configuration_file to create the final object that will be saved in the
        # tool path
        result_conf.generate_results_configuration_file(
            build_screen=tab_1, tool_path=self.tool_path, testing_configuration=False
        )

def run(context):
    QmentaSDKToolMakerTutorial().tool_outputs()  # this can be removed if no results configuration file needs to be generated.
    QmentaSDKToolMakerTutorial().run(context)