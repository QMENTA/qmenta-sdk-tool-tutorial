
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
from qmenta.sdk.tool_maker.modalities import Modality, Tag
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
<h3>{image_caption}</h3>
<img src="{src_image}" alt="{image_description}" style="max-width: 400px;">
"""


class QmentaSDKToolMakerTutorial(Tool):
    def tool_inputs(self):
        """
        Define the inputs for the tool. This is used to create the settings.json file.
        More information on the inputs can be found here:
        https://docs.qmenta.com/sdk/guides_docs/settings.html
        """
      
        # Add the file selection method:
        self.add_input_container(
            title="Oncology medical image",
            info="<h2>ANTsPY Tutorial</h2>Required inputs:<br><b>&bull; Anatomical brain medical image</b>: " \
            "2D image to analyze<br>&ensp;Accepted modalities: 'T1', 'T2'<br>&ensp;Two files with different tags: 'r16' and 'r64'",  # text in case we want to show which modalities are accepted by the filter.
            anchor=1,
            batch=1,
            container_id="input_images",
            mandatory=1,
            file_list=[
                InputFile(
                    file_filter_condition_name="c_image1",
                    filter_file=FilterFile(
                        modality=[Modality.T1, Modality.T2],
                        regex=".*r16.*\\.nii\\.gz",
                    ),
                    mandatory=1,
                    min_files=1,
                    max_files=1,
                ),
                InputFile(
                    file_filter_condition_name="c_image2",
                    filter_file=FilterFile(
                        modality=[Modality.T1, Modality.T2],
                        regex=".*r16.*\\.nii\\.gz",
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
        self.add_heading("PyANTs tool can perform the following steps:")

        self.add_input_multiple_choice(
            id_="perform_steps",
            options=[
                ("do_biasfieldcorrection", "Perform Bias Field Correction"),
                ("do_segmentation", "Perform tissue segmentation"),
                ("do_thickness", "Perform cortical thickness"),
                ("do_registration", "ANTs registration interface"),
            ], 
            default=[
                "do_biasfieldcorrection", 
                "do_segmentation",
                "do_thickness",
                "do_registration"
            ],
            title="Which step/s do you want to execute?",
        )
        
        # Displays an horizontal line
        self.add_line()

        self.add_input_string(
            id_="mrf", 
            default="[0.2, 1x1]",  # antspy tutorial uses 2D image
            title="'mrf' parameters as a string, usually \"[smoothingFactor,radius]\" " \
            "where smoothingFactor determines the amount of smoothing and radius determines " \
            "the MRF neighborhood, as an ANTs style neighborhood vector eg \"1x1\" for a 2D image.", 
        )

    def run(self, context):
        """
        Main entry point for the tool execution.

        The workflow is divided into three phases:
        1. Processing: execute ANTs operations and write result files.
        2. Reporting: generate visualizations and build the HTML report.
        3. Uploading: upload all outputs to the QMENTA Platform.
        """

        # ============================================================
        # INITIAL SETUP
        # ============================================================
        logger = logging.getLogger("main")
        logger.info("Tool starting")

        # Define and create working directory
        output_dir = os.path.join(os.environ.get("WORKDIR", "/root"), "OUTPUT")
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)

        context.set_progress(value=0, message="Initializing tool execution")

        # Download inputs and populate self.inputs
        context.set_progress(message="Downloading input data")
        self.prepare_inputs(context, logger)

        # Retrieve input image paths
        fname1_handler = self.inputs.input_images.c_image1[0]
        fname1 = fname1_handler.file_path

        fname2 = None
        if "do_registration" in self.inputs.perform_steps:
            fname2 = self.inputs.input_images.c_image2[0].file_path

        # Containers to track outputs
        generated_files = []
        report_items = []

        # ============================================================
        # PROCESSING PHASE
        # ============================================================
        logger.info("Starting processing phase")
        logger.info("Selected steps:\n{}".format("\n".join(self.inputs.perform_steps)))

        img = ants.image_read(fname1)

        # --- Bias Field Correction ---
        if "do_biasfieldcorrection" in self.inputs.perform_steps:
            logger.info("Running N4 bias field correction")
            image_n4 = ants.n4_bias_field_correction(img)
            image_n4.to_filename("n4_processed.nii.gz")

            generated_files.append("n4_processed.nii.gz")
            report_items.append({
                "header": "N4 Bias Field Correction",
                "image": "n4_bias.png",
                "source_image": image_n4,
                "description": "N4 bias field correction result",
            })

        # Enforce dependency: segmentation required for thickness
        if "do_thickness" in self.inputs.perform_steps and "do_segmentation" not in self.inputs.perform_steps:
            self.inputs.perform_steps.append("do_segmentation")

        # --- Tissue Segmentation ---
        if "do_segmentation" in self.inputs.perform_steps:
            logger.info("Running tissue segmentation")
            mask = ants.get_mask(img)

            img_seg = ants.atropos(
                a=img,
                m=self.inputs.mrf,
                c='[2,0]',
                i='kmeans[3]',
                x=mask
            )

            img_seg["segmentation"].to_filename("atropos_processed.nii.gz")
            generated_files.append("atropos_processed.nii.gz")

            report_items.append({
                "header": "Tissue Segmentation",
                "image": "segmentation.png",
                "source_image": img_seg["segmentation"],
                "description": "ANTs Atropos tissue segmentation",
            })

            # --- Cortical Thickness ---
            if "do_thickness" in self.inputs.perform_steps:
                logger.info("Running cortical thickness estimation")
                thickimg = ants.kelly_kapowski(
                    s=img_seg["segmentation"],
                    g=img_seg["probabilityimages"][1],
                    w=img_seg["probabilityimages"][2],
                    its=45, r=0.5, m=1
                )

                thickimg.to_filename("thickness_processed.nii.gz")
                generated_files.append("thickness_processed.nii.gz")

                report_items.append({
                    "header": "Cortical Thickness",
                    "image": "thickness.png",
                    "overlay": thickimg,
                    "base_image": img,
                    "description": "Cortical thickness estimation",
                })

        # --- Registration ---
        if "do_registration" in self.inputs.perform_steps:
            logger.info("Running image registration")
            fixed = ants.image_read(fname1)
            moving = ants.image_read(fname2)

            tx = ants.registration(
                fixed=fixed,
                moving=moving,
                type_of_transform="SyN"
            )

            warped = tx["warpedmovout"]
            warped.to_filename("warped.nii.gz")
            generated_files.append("warped.nii.gz")

            report_items.append({
                "header": "Image Registration",
                "image": "registration.png",
                "overlay": warped,
                "base_image": fixed,
                "description": "ANTs nonlinear registration result",
            })

        # ============================================================
        # REPORTING PHASE (ALL PLOTTING + BODY_TEMPLATE)
        # ============================================================
        logger.info("Generating report content")

        body_content = ""

        for item in report_items:
            if "overlay" in item:
                item["base_image"].plot(
                    overlay=item["overlay"],
                    overlay_cmap="jet",
                    filename=item["image"]
                )
            else:
                ants.plot(item["source_image"], filename=item["image"])

            generated_files.append(item["image"])  # to upload later!

            body_content += BODY_TEMPLATE.format(
                header=item["header"],
                src_image=item["image"],
                image_description=item["description"],
                image_caption=item["description"],
            )

        report_file = None
        if body_content:
            report_file = "online_report.html"
            with open(report_file, "w") as f:
                f.write(HTML_TEMPLATE.format(body=body_content))

            generated_files.append(report_file)

        # ============================================================
        # UPLOADING PHASE
        # ============================================================
        logger.info("Uploading outputs to QMENTA Platform")

        # Upload original input image for reference
        context.upload_file(
            source_file_path=fname1,
            destination_path="input_image.nii.gz",
            modality=fname1_handler.get_file_modality(),
            tags=fname1_handler.get_file_tags(),
        )

        # Upload all generated outputs
        for filename in generated_files:
            context.upload_file(filename, filename)

        context.set_progress(value=100, message="Processing completed")
        logger.info("Tool execution finished successfully")

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
        papaya_2.add_file(file="warped.nii.gz", coloring=Coloring.red)  # using file tag
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