# -*- coding: utf-8 -*-
import os
from collections import namedtuple

import nibabel as nib
import numpy as np
import pandas as pd
import radiomics
import SimpleITK as sitk


def run(context):
    """
    Function invoked by the SDK that passes a context object. This object can then be used
    to communicate with the platform in the context of that particular analysis to fetch files,
    report progress, and upload results, among others.

    Parameters
    ----------
    context : qmenta.sdk.context.AnalysisContext
        Analysis context object to communicate with the QMENTA Platform.
    """

    """ Basic setup """

    # Define directories for the input and output files inside the container
    input_dir = os.path.join(os.path.expanduser("~"), "INPUT")
    output_dir = os.path.join(os.path.expanduser("~"), "OUTPUT")
    os.makedirs(output_dir, exist_ok=True)
    context.set_progress(value=0, message="Processing")  # Set progress status so it is displayed in the platform

    """ Get the input data """

    # Retrieve input files
    anat = context.get_files("input_anat", file_filter_condition_name="c_anat")[0].download(input_dir)
    modality = context.get_files("input_anat", file_filter_condition_name="c_anat")[0].get_file_modality()

    labels = context.get_files("input_mask", file_filter_condition_name="c_labels")[0].download(input_dir)
    tags = context.get_files("input_mask", file_filter_condition_name="c_labels")[0].get_file_tags()

    # Retrieve settings
    settings = context.get_settings()

    # Load input data into memory
    mask_nib = nib.load(labels)
    mask_img = mask_nib.get_data()
    anat_img = sitk.GetImageFromArray(nib.load(anat).get_data())

    """ Processing code """

    # Create feature extractor with user specified settings
    context.set_progress(value=10, message="Instantiating feature extractor")

    extractor = radiomics.featureextractor.RadiomicsFeatureExtractor()
    extractor.disableAllFeatures()
    for feature_class in settings["feature_classes"]:  # The feature classes are retrieved from the settings
        extractor.enableFeatureClassByName(feature_class)
    for image_filter in settings["image_filters"]:  # The image filters are also retrieved from the settings
        extractor.enableImageTypeByName(image_filter)
        if image_filter == "LoG":
            extractor.settings["sigma"] = [settings["sigma_LoG"]]
            extractor.settings["binWidth"] = settings["fwidth_LoG"]

    # Print extractor parameters for debugging and info
    print("Extraction parameters:\n\t", extractor.settings)
    print("Enabled filters:\n\t", extractor.enabledImagetypes)
    print("Enabled features:\n\t", extractor.enabledFeatures)

    # Initialize all necessary dataframes and dicts
    original_rds_df = pd.DataFrame()
    original_rds_dict = {}

    wavelet_names = ["HHH", "HHL", "HLH", "HLL", "LHH", "LHL", "LLH", "LLL"]
    Wavelet = namedtuple("Wavelet", "df dict")
    if "Wavelet" in settings["image_filters"]:
        wavelets = {}
        for name in wavelet_names:
            wavelets[name] = Wavelet(pd.DataFrame(), {})

    if "LoG" in settings["image_filters"]:
        log_rds_df = pd.DataFrame()
        log_rds_dict = {}

    if "Logarithm" in settings["image_filters"]:
        logarithm_rds_df = pd.DataFrame()
        logarithm_rds_dict = {}

    if "Exponential" in settings["image_filters"]:
        exp_rds_df = pd.DataFrame()
        exp_rds_dict = {}

    # Compute radiomic features for each label and puts them in a separate sheet in the excel
    context.set_progress(value=20, message="Extracting radiomic features")
    for label in np.unique(mask_img)[1:]:
        label_mask = np.zeros_like(mask_img)
        label_mask[mask_img == label] = 1
        label_sitk = sitk.GetImageFromArray(label_mask)
        features = extractor.execute(anat_img, label_sitk)

        for key, value in features.items():
            if "original" in key:
                original_rds_dict[key] = [value]
            elif "sigma" in key:
                log_rds_dict[key] = [value]
            elif "logarithm" in key:
                logarithm_rds_dict[key] = [value]
            elif "exponential" in key:
                exp_rds_dict[key] = [value]
            else:
                for name in wavelet_names:
                    if name in key:
                        wavelets[name].dict[key] = [value]
                        break

        original_rds_df["label" + str(label)] = pd.Series(original_rds_dict)
        original_rds_dict = {}

        if "Wavelet" in settings["image_filters"]:
            for name in wavelet_names:
                wavelets[name].df["label" + str(label)] = pd.Series(wavelets[name].dict)
                wavelets[name]._replace(dict={})

        if "LoG" in settings["image_filters"]:
            log_rds_df["label" + str(label)] = pd.Series(log_rds_dict)
            log_rds_dict = {}

        if "Logarithm" in settings["image_filters"]:
            logarithm_rds_df["label" + str(label)] = pd.Series(logarithm_rds_dict)
            logarithm_rds_dict = {}

        if "Exponential" in settings["image_filters"]:
            exp_rds_df["label" + str(label)] = pd.Series(exp_rds_dict)
            exp_rds_dict = {}

    # Create CSV with radiomics features and obtain filtered images
    original_radiomics_csv = os.path.join(output_dir, "original_radiomic_features.csv")
    original_rds_df.to_csv(original_radiomics_csv)
    radiomics_csv_to_upload = []  # List[Tuple[src_filepath : str, dst_platform_path : str, tags : Set]]
    filtered_images_to_upload = []  # List[Tuple[src_filepath : str, dst_platform_path : str, tags : Set]]

    if "Wavelet" in settings["image_filters"]:
        wavelet_generator = radiomics.imageoperations.getWaveletImage(anat_img, sitk.GetImageFromArray(mask_img))
        for wavelet in wavelet_generator:
            src_filepath = os.path.join(output_dir, wavelet[1] + "_filtered_image.nii.gz")
            dst_platform_path = "Wavelet/" + wavelet[1] + "_filtered_image.nii.gz"
            tags = {"wavelet"}

            nib.save(
                nib.Nifti1Image(sitk.GetArrayFromImage(wavelet[0]), mask_nib.affine, mask_nib.header),
                src_filepath,
            )

            filtered_images_to_upload.append((src_filepath, dst_platform_path, tags))

        for name in wavelet_names:
            dst_platform_path = "wavelet_{}_radiomic_features.csv".format(name)
            src_filepath = os.path.join(output_dir, dst_platform_path)
            tags = {"wavelet", "csv"}

            wavelets[name].df.to_csv(src_filepath)

            radiomics_csv_to_upload.append((src_filepath, dst_platform_path, tags))

    if "LoG" in settings["image_filters"]:
        log_generator = radiomics.imageoperations.getLoGImage(
            anat_img, sitk.GetImageFromArray(mask_img), sigma=[settings["sigma_LoG"]], binWidth=settings["fwidth_LoG"]
        )
        log_image = next(log_generator)

        src_filepath = os.path.join(output_dir, log_image[1] + "_filtered_image.nii.gz")
        dst_platform_path = "LoG/" + log_image[1] + "_filtered_image.nii.gz"
        tags = {"LoG"}

        nib.save(
            nib.Nifti1Image(sitk.GetArrayFromImage(log_image[0]), mask_nib.affine, mask_nib.header),
            src_filepath,
        )

        filtered_images_to_upload.append((src_filepath, dst_platform_path, tags))

        dst_platform_path = "LoG/LoG_radiomic_features.csv"
        src_filepath = os.path.join(output_dir, "LoG_radiomic_features.csv")
        tags = {"LoG", "csv"}

        log_rds_df.to_csv(src_filepath)

        radiomics_csv_to_upload.append((src_filepath, dst_platform_path, tags))

    if "Logarithm" in settings["image_filters"]:
        logarithm_generator = radiomics.imageoperations.getLogarithmImage(anat_img, sitk.GetImageFromArray(mask_img))
        logarithm_image = next(logarithm_generator)

        src_filepath = os.path.join(output_dir, logarithm_image[1] + "_filtered_image.nii.gz")
        dst_platform_path = "Logarithm/" + logarithm_image[1] + "_filtered_image.nii.gz"
        tags = {"logarithm"}

        nib.save(
            nib.Nifti1Image(sitk.GetArrayFromImage(logarithm_image[0]), mask_nib.affine, mask_nib.header),
            src_filepath,
        )

        filtered_images_to_upload.append((src_filepath, dst_platform_path, tags))

        dst_platform_path = "Logarithm/logarithm_radiomic_features.csv"
        src_filepath = os.path.join(output_dir, "logarithm_radiomic_features.csv")
        tags = {"logarithm", "csv"}

        logarithm_rds_df.to_csv(src_filepath)

        radiomics_csv_to_upload.append((src_filepath, dst_platform_path, tags))

    if "Exponential" in settings["image_filters"]:
        exponential_generator = radiomics.imageoperations.getExponentialImage(
            anat_img, sitk.GetImageFromArray(mask_img)
        )
        exponential_image = next(exponential_generator)

        src_filepath = os.path.join(output_dir, exponential_image[1] + "_filtered_image.nii.gz")
        dst_platform_path = "Exponential/" + exponential_image[1] + "_filtered_image.nii.gz"
        tags = {"exponential"}

        nib.save(
            nib.Nifti1Image(sitk.GetArrayFromImage(exponential_image[0]), mask_nib.affine, mask_nib.header),
            src_filepath,
        )

        filtered_images_to_upload.append((src_filepath, dst_platform_path, tags))

        dst_platform_path = "Exponential/exponential_radiomic_features.csv"
        src_filepath = os.path.join(output_dir, "exponential_radiomic_features.csv")
        tags = {"exponential", "csv"}

        exp_rds_df.to_csv(src_filepath)

        radiomics_csv_to_upload.append((src_filepath, dst_platform_path, tags))

    """ Upload the results """

    # Upload original image, mask and radiomic features extracted from them
    context.set_progress(value=90, message="Uploading results")

    context.upload_file(anat, "inputs/anatomical_image.nii.gz", modality=modality)
    context.upload_file(labels, "inputs/labels_mask.nii.gz", tags=tags)
    context.upload_file(original_radiomics_csv, "original_radiomic_features.csv", tags={"csv"})

    # Upload filtered images and radiomic CSVs
    all_results = filtered_images_to_upload + radiomics_csv_to_upload
    for src_filepath, dst_platform_path, tags in all_results:
        context.upload_file(
            src_filepath,
            dst_platform_path,
            tags=tags,
        )
