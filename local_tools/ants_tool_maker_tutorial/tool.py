
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
            "ANTsPy tutorial settings." \
        )
        
        # Add the file selection method:
        self.add_input_container(
            title="Oncology medical image",
            info="Required inputs:<br><b>&bull; Anatomical brain medical image</b>: 2D image to analyze<br>&ensp;Accepted modalities: 'T1', 'T2'",  # text in case we want to show which modalities are accepted by the filter.
            anchor=1,
            batch=1,
            container_id="input_images",
            mandatory=1,
            file_list=[
                InputFile(
                    file_filter_condition_name="c_image1",
                    filter_file=FilterFile(
                        modality=[Modality.T1, Modality.T2],
                        tags=[["r16"]]
                    ),
                    mandatory=1,
                    min_files=1,
                    max_files=1,
                ),
                InputFile(
                    file_filter_condition_name="c_image2",
                    filter_file=FilterFile(
                        modality=[Modality.T1, Modality.T2],
                        tags=[["r64"]]
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
                ["do_registration", "ANTs registration interface"],
            ], 
            default=["do_biasfieldcorrection", "do_segmentation"],
            title="Which steps do you want to execute?",
        )
        
        # Displays an horizontal line
        self.add_line()

        self.add_input_string(
            id_="mrf", 
            default="[0.2, 1x1]",  # antspy tutorial uses 2D iamge
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

        context.upload_file(
            source_file_path=fname1, 
            destination_path="input_image.nii.gz",
            modality=fname1_handler.get_file_modality(),
            tags=fname1_handler.get_file_tags(),
        )
        original_png_image = "original.png"

        ants.plot(fname1, filename=original_png_image)
        context.upload_file(
            original_png_image, 
            original_png_image,
        )

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

        # do any operations directly on ANTsImage types
        img_arr = img.numpy()
        img2 = img.new_image_like(img_arr*2)
        # do any operations directly on ANTsImage types
        img3 = img2 - img
        img3 = img2 > img
        img3 = img2 / img
        img3 = img2 == img

        # change any physical properties
        img4 = img.clone()
        print(img4.spacing)
        img4.set_spacing((1,1))
        print(img4.spacing)

        # test if two images are allclose in values
        issame = ants.allclose(img,img2)
        logger.info(f"two images are allclose in values? : {issame}")
        # test if two images have same physical space
        issame_phys = ants.image_physical_space_consistency(img,img2)
        logger.info(f"two images have same physical space : {issame_phys}")

        body_content = ""
        logger.info(f"Performing steps: {"\n".join(self.inputs.perform_steps)}")

        if "do_biasfieldcorrection" in self.inputs.perform_steps:
            logger.info("Started N4 bias field correction")
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

        if "do_thickness" in self.inputs.perform_steps:
            self.inputs.perform_steps.append("do_segmentation")

        if "do_segmentation" in self.inputs.perform_steps:
            logger.info("Started segmentation")
            img = ants.image_read(fname1)
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
                logger.info("Started thickness")
                img = ants.image_read(fname1)
                print(self.inputs.mrf)
                mask = ants.get_mask(img).threshold_image(1, 2)

                thickimg = ants.kelly_kapowski(
                    s=img_seg['segmentation'], 
                    g=img_seg['probabilityimages'][1],
                    w=img_seg['probabilityimages'][2], 
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
        
        if "do_registration" in self.inputs.perform_steps:
            logger.info("Started registration")
            fname2_handler = self.inputs.input_images.c_image2[0]
            fname2 = fname2_handler.file_path
            fixed = ants.image_read(fname1)
            moving = ants.image_read(fname2)
            mytx = ants.registration(fixed=fixed, moving=moving, type_of_transform='SyN')
            logger.info("Finished registration")
            logger.info(mytx)
            warped_moving = mytx['warpedmovout'].to_filename("warped.nii.gz")
            context.upload_file(
                "warped.nii.gz", 
                "warped.nii.gz"
            )
            png_image = "registration.png"
            fixed.plot(overlay=warped_moving, title='After Registration', filename=png_image)
            context.upload_file(png_image, png_image)
            body_content += BODY_TEMPLATE.format(
                header="Registration step",
                src_image=png_image,
                image_description=f"Output of ANTs Registration for {os.path.basename(fname1)}",
                image_caption=f"Output of ANTs Registration for {os.path.basename(fname1)}",
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
        papaya_1 = PapayaViewer(title="T1 ANTs segmentation and cortical thickness", width="50%", region=Region.center)
        # the first viewer's region is defined as center

        # Add as many layers as you want, they are going to be loaded in the order that you add them.
        papaya_1.add_file(file="input_image.nii.gz", coloring=Coloring.grayscale)  # base iamge, using the file name
        papaya_1.add_file(file="atropos_processed.nii.gz", coloring=Coloring.custom)  # overlay 1, custom coloring shows different colors for different label values.
        papaya_1.add_file(file="thickness_processed.nii.gz", coloring=Coloring.hot_n_cold)  # overlay 2, hot/cold coloring
        # Add the papaya element as a visualization in the results configuration object.
        result_conf.add_visualization(new_element=papaya_1)

        papaya_2 = PapayaViewer(title="T1 ANTs registration", width="50%", region=Region.right)
        # the second viewer's `region` is defined as right. This is required by the Split() element below, which has the property
        # orientation set to `vertical`. If it is set to horizontal, then you can choose between 'Region.top' or 'Region.bottom'.

        # You can use modality or tag of the output file to select the file to be shown in the viewer.
        papaya_2.add_file(file="input_image.nii.gz", coloring=Coloring.grayscale)  # using the file modality
        papaya_2.add_file(file="warped.nii.gz", coloring=Coloring.custom_random)  # using file tag
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