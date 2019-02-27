# -*- coding: utf-8 -*-

import os

import SimpleITK as sitk
import nibabel as nib
import numpy as np
import pandas as pd
import radiomics
from radiomics import featureextractor


def run(context):
    # Define directories for the input and output files inside the container
    input_dir = os.path.join('/root', 'INPUT')
    output_dir = os.path.join('/root', 'OUTPUT')
    os.mkdir(output_dir)
    context.set_progress(value=0, message="Processing")  # Set progress status so it is displayed in the platform

    # Retrieve files and settings
    anat = context.get_files('input', file_filter_condition_name='c_anat')[0].download(input_dir)
    modality = context.get_files('input', file_filter_condition_name='c_anat')[0].get_file_modality()
    labels = context.get_files('input_mask', file_filter_condition_name='c_labels')[0].download(input_dir)
    tags = context.get_files('input_mask', file_filter_condition_name='c_labels')[0].get_file_tags()
    mask_nib = nib.load(labels)
    mask_img = mask_nib.get_data()
    anat_img = sitk.GetImageFromArray(nib.load(anat).get_data())
    settings = context.get_settings()

    # Create feature extractor with user specified settings
    context.set_progress(value=10, message="Instantiating feature extractor")

    extractor = featureextractor.RadiomicsFeaturesExtractor()
    extractor.disableAllFeatures()
    for feature_class in settings['feature_classes']:  # The feature classes are retrieved from the settings
        extractor.enableFeatureClassByName(feature_class)
    for image_filter in settings['image_filters']:  # The image filters are also retrieved from the settings
        extractor.enableImageTypeByName(image_filter)
        if image_filter == 'LoG':
            extractor.settings['sigma'] = [settings['sigma_LoG']]
            extractor.settings['binWidth'] = settings['fwidth_LoG']

    # Print extractor parameters for debugging and info
    print('Extraction parameters:\n\t', extractor.settings)
    print('Enabled filters:\n\t', extractor._enabledImagetypes)
    print('Enabled features:\n\t', extractor._enabledFeatures)

    # Initialize all necessary dataframes and dicts
    original_rds_df = pd.DataFrame()
    original_rds_dict = {}

    if "Wavelet" in settings['image_filters']:
        wavelet_HHH_rds_df = pd.DataFrame()
        wavelet_HHH_rds_dict = {}
        wavelet_HHL_rds_df = pd.DataFrame()
        wavelet_HHL_rds_dict = {}
        wavelet_HLH_rds_df = pd.DataFrame()
        wavelet_HLH_rds_dict = {}
        wavelet_HLL_rds_df = pd.DataFrame()
        wavelet_HLL_rds_dict = {}
        wavelet_LHH_rds_df = pd.DataFrame()
        wavelet_LHH_rds_dict = {}
        wavelet_LHL_rds_df = pd.DataFrame()
        wavelet_LHL_rds_dict = {}
        wavelet_LLH_rds_df = pd.DataFrame()
        wavelet_LLH_rds_dict = {}
        wavelet_LLL_rds_df = pd.DataFrame()
        wavelet_LLL_rds_dict = {}

    if "LoG" in settings['image_filters']:
        log_rds_df = pd.DataFrame()
        log_rds_dict = {}

    if "Logarithm" in settings['image_filters']:
        logarithm_rds_df = pd.DataFrame()
        logarithm_rds_dict = {}

    if "Exponential" in settings['image_filters']:
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
            if "HHH" in key:
                wavelet_HHH_rds_dict[key] = [value]
            if "HHL" in key:
                wavelet_HHL_rds_dict[key] = [value]
            if "HLH" in key:
                wavelet_HLH_rds_dict[key] = [value]
            if "HLL" in key:
                wavelet_HLL_rds_dict[key] = [value]
            if "LHH" in key:
                wavelet_LHH_rds_dict[key] = [value]
            if "LHL" in key:
                wavelet_LHL_rds_dict[key] = [value]
            if "LLH" in key:
                wavelet_LLH_rds_dict[key] = [value]
            if "LLL" in key:
                wavelet_LLL_rds_dict[key] = [value]
            if "sigma" in key:
                log_rds_dict[key] = [value]
            if "logarithm" in key:
                logarithm_rds_dict[key] = [value]
            if "exponential" in key:
                exp_rds_dict[key] = [value]

        original_rds_df['label' + str(label)] = pd.Series(original_rds_dict)
        original_rds_dict = {}

        if "Wavelet" in settings['image_filters']:
            wavelet_HHH_rds_df['label' + str(label)] = pd.Series(wavelet_HHH_rds_dict)
            wavelet_HHH_rds_dict = {}
            wavelet_HHL_rds_df['label' + str(label)] = pd.Series(wavelet_HHL_rds_dict)
            wavelet_HHL_rds_dict = {}
            wavelet_HLH_rds_df['label' + str(label)] = pd.Series(wavelet_HLH_rds_dict)
            wavelet_HLH_rds_dict = {}
            wavelet_HLL_rds_df['label' + str(label)] = pd.Series(wavelet_HLL_rds_dict)
            wavelet_HLL_rds_dict = {}
            wavelet_LHH_rds_df['label' + str(label)] = pd.Series(wavelet_LHH_rds_dict)
            wavelet_LHH_rds_dict = {}
            wavelet_LHL_rds_df['label' + str(label)] = pd.Series(wavelet_LHL_rds_dict)
            wavelet_LHL_rds_dict = {}
            wavelet_LLH_rds_df['label' + str(label)] = pd.Series(wavelet_LLH_rds_dict)
            wavelet_LLH_rds_dict = {}
            wavelet_LLL_rds_df['label' + str(label)] = pd.Series(wavelet_LLL_rds_dict)
            wavelet_LLL_rds_dict = {}

        if "LoG" in settings['image_filters']:
            log_rds_df['label' + str(label)] = pd.Series(log_rds_dict)
            log_rds_dict = {}

        if "Logarithm" in settings['image_filters']:
            logarithm_rds_df['label' + str(label)] = pd.Series(logarithm_rds_dict)
            logarithm_rds_dict = {}

        if "Exponential" in settings['image_filters']:
            exp_rds_df['label' + str(label)] = pd.Series(exp_rds_dict)
            exp_rds_dict = {}

    # Upload of excel file and input files
    context.set_progress(value=90, message="Uploading results")
    original_rds_df.to_csv(os.path.join(output_dir, 'original_radiomic_features.csv'))

    context.upload_file(os.path.join(output_dir, 'original_radiomic_features.csv'), 'original_radiomic_features.csv',
                        tags={'csv'})
    context.upload_file(anat, 'inputs/anatomical_image.nii.gz', modality=modality)
    context.upload_file(labels, 'inputs/labels_mask.nii.gz', tags=tags)

    # If selected in the settings, filtered images and csvs also outputted

    if "Wavelet" in settings['image_filters']:
        wavelet_generator = radiomics.imageoperations.getWaveletImage(anat_img, sitk.GetImageFromArray(mask_img))
        for wavelet in wavelet_generator:
            nib.save(nib.Nifti1Image(sitk.GetArrayFromImage(wavelet[0]), mask_nib.affine, mask_nib.header),
                     os.path.join(output_dir, wavelet[1] + '_filtered_image.nii.gz'))
            context.upload_file(os.path.join(output_dir, wavelet[1] + '_filtered_image.nii.gz'),
                                'Wavelet/' + wavelet[1] + '_filtered_image.nii.gz', tags={'wavelet'})
        wavelet_HHH_rds_df.to_csv(os.path.join(output_dir, 'wavelet_HHH_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_HHH_radiomic_features.csv'),
                            'Wavelet/wavelet_HHH_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_HHL_rds_df.to_csv(os.path.join(output_dir, 'wavelet_HHL_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_HHL_radiomic_features.csv'),
                            'Wavelet/wavelet_HHL_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_HLH_rds_df.to_csv(os.path.join(output_dir, 'wavelet_HLH_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_HLH_radiomic_features.csv'),
                            'Wavelet/wavelet_HLH_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_HLL_rds_df.to_csv(os.path.join(output_dir, 'wavelet_HLL_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_HLL_radiomic_features.csv'),
                            'Wavelet/wavelet_HLL_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_LHH_rds_df.to_csv(os.path.join(output_dir, 'wavelet_LHH_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_LHH_radiomic_features.csv'),
                            'Wavelet/wavelet_LHH_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_LHL_rds_df.to_csv(os.path.join(output_dir, 'wavelet_LHL_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_LHL_radiomic_features.csv'),
                            'Wavelet/wavelet_LHL_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_LLH_rds_df.to_csv(os.path.join(output_dir, 'wavelet_LLH_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_LLH_radiomic_features.csv'),
                            'Wavelet/wavelet_LLH_radiomic_features.csv', tags={'wavelet', 'csv'})
        wavelet_LLL_rds_df.to_csv(os.path.join(output_dir, 'wavelet_LLL_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'wavelet_LLL_radiomic_features.csv'),
                            'Wavelet/wavelet_LLL_radiomic_features.csv', tags={'wavelet', 'csv'})

    if "LoG" in settings['image_filters']:
        log_generator = radiomics.imageoperations.getLoGImage(anat_img, sitk.GetImageFromArray(mask_img),
                                                              sigma=[settings["sigma_LoG"]],
                                                              binWidth=settings['fwidth_LoG'])
        log_image = next(log_generator)
        nib.save(nib.Nifti1Image(sitk.GetArrayFromImage(log_image[0]), mask_nib.affine, mask_nib.header),
                 os.path.join(output_dir, log_image[1] + '_filtered_image.nii.gz'))
        context.upload_file(os.path.join(output_dir, log_image[1] + '_filtered_image.nii.gz'),
                            'LoG/' + log_image[1] + '_filtered_image.nii.gz', tags={'LoG'})
        log_rds_df.to_csv(os.path.join(output_dir, 'LoG_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'LoG_radiomic_features.csv'),
                            'LoG/LoG_radiomic_features.csv', tags={'LoG', 'csv'})

    if "Logarithm" in settings['image_filters']:
        logarithm_generator = radiomics.imageoperations.getLogarithmImage(anat_img, sitk.GetImageFromArray(mask_img))
        logarithm_image = next(logarithm_generator)
        nib.save(nib.Nifti1Image(sitk.GetArrayFromImage(logarithm_image[0]), mask_nib.affine, mask_nib.header),
                 os.path.join(output_dir, logarithm_image[1] + '_filtered_image.nii.gz'))
        context.upload_file(os.path.join(output_dir, logarithm_image[1] + '_filtered_image.nii.gz'),
                            'Logarithm/' + logarithm_image[1] + '_filtered_image.nii.gz', tags={'logarithm'})
        logarithm_rds_df.to_csv(os.path.join(output_dir, 'logarithm_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'logarithm_radiomic_features.csv'),
                            'Logarithm/logarithm_radiomic_features.csv', tags={'logarithm', 'csv'})

    if "Exponential" in settings['image_filters']:
        exponential_generator = radiomics.imageoperations.getExponentialImage(anat_img,
                                                                              sitk.GetImageFromArray(mask_img))
        exponential_image = next(exponential_generator)
        nib.save(nib.Nifti1Image(sitk.GetArrayFromImage(exponential_image[0]), mask_nib.affine, mask_nib.header),
                 os.path.join(output_dir, exponential_image[1] + '_filtered_image.nii.gz'))
        context.upload_file(os.path.join(output_dir, exponential_image[1] + '_filtered_image.nii.gz'),
                            'Exponential/' + exponential_image[1] + '_filtered_image.nii.gz', tags={'exponential'})
        exp_rds_df.to_csv(os.path.join(output_dir, 'exponential_radiomic_features.csv'))
        context.upload_file(os.path.join(output_dir, 'exponential_radiomic_features.csv'),
                            'Exponential/exponential_radiomic_features.csv', tags={'exponential', 'csv'})
