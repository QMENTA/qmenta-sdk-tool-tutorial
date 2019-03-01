# -*- coding: utf-8 -*-
from collections import namedtuple
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

    wavelet_names = ['HHH', 'HHL', 'HLH', 'HLL', 'LHH', 'LHL', 'LLH', 'LLL']
    Wavelet = namedtuple('Wavelet', 'df dict')
    if "Wavelet" in settings['image_filters']:
        wavelets = {}
        for name in wavelet_names:
            wavelets[name] = Wavelet(pd.DataFrame(), {})

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

        for key, value in features.iteritems():
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

        original_rds_df['label' + str(label)] = pd.Series(original_rds_dict)
        original_rds_dict = {}

        if "Wavelet" in settings['image_filters']:
            for name in wavelet_names:
                wavelets[name].df['label' + str(label)] = pd.Series(wavelets[name].dict)
                wavelets[name]._replace(dict={})

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
        for name in wavelet_names:
            csv_path = 'wavelet_{}_radiomic_features.csv'.format(name)
            wavelets[name].df.to_csv(os.path.join(output_dir, csv_path))
            context.upload_file(os.path.join(output_dir, csv_path), csv_path, tags={'wavelet', 'csv'})

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
